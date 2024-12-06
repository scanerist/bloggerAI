import asyncio
import time
from typing import Optional

from aiogram import types
from aiogram.fsm.context import FSMContext
from pyrogram import types as pyg_types
from typing import List

from services.bot.keyboards import post_approval_keyboard
from services.pyrogram_service.pyrogram_client import PyrogramService
from services.bot.senders import send
from services.bot.state_manager import Form
from services.bot.bot import BloggerAiBot
from services.database.dao import update_source_channel
from services.database.dao import get_message_id_from_source_channel_by_user_id
from services.shared.logger import setup_logger

bot = BloggerAiBot().get_bot()
logger = setup_logger(__name__)
pyrogram_service = PyrogramService.get_instance()
ME = bot.id
TIMELAP_MESSAGE = 2

async def send_media_group(media_group: List[pyg_types.Message], state: FSMContext):
    if media_group:
        while True:
            try:
                await pyrogram_service.client.send_media_group(
                    chat_id=ME, media=media_group
                )
            except Exception as e:
                logger.info(f"При отправке сообщений медийной группы с id={media_group[0].media_group_id} произошла ошибка - {e}")
            else:
                await state.set_state(Form.approve_post)
                break
    media_group.clear()

async def process_next_post(message: types.Message, state: FSMContext, source_channel: Optional[str] = None):
    data = await state.get_data()
    source_channel = source_channel if source_channel else data.get('source_channel')
    if not source_channel:
        await message.answer("Source channel is not set. Please set the source channel and try again.")
        return

    last_message = await pyrogram_service.get_last_message(source_channel)
    last_processed_message_id = await get_message_id_from_source_channel_by_user_id(
        source_channel, message.from_user.id
    ) or last_message.id - 1
    await update_source_channel(source_channel, last_message.id)
    await state.update_data(last_processed_message_id=last_message.id)

    last_processed_media_group_id = 0
    media_group = []
    offset = last_message.id + 1

    while True:
        last_messages = pyrogram_service.get_last_messages(
            source_channel, 
            offset
        )
        async for last_message in last_messages:
            
            if last_message.id <= last_processed_message_id:
                await send_media_group(media_group, state)
                await message.answer(
                    f"Все посты обработаны. Пропуск..."\
                    f"Детали: из канала: {source_channel}, last_message_id: {last_message.id}, "\
                    f"last processed message_id, записанное в state.data: {last_processed_message_id}"\
                    f"message_id на вход метода `process_next_post` message.id {message.message_id}"
                )
                return
            offset = last_message.id
            media = (
                last_message.animation or 
                last_message.audio or 
                last_message.contact or
                last_message.dice or
                last_message.game or
                last_message.location or
                last_message.photo or 
                last_message.poll or
                last_message.sticker or
                last_message.video or 
                last_message.video_note or
                last_message.voice or
                last_message.web_page or
                last_message.document
            )
            
            if last_processed_media_group_id != last_message.media_group_id:
                await send_media_group(media_group, state)
                last_processed_media_group_id = last_message.media_group_id

            if last_message.media_group_id:
                try: 
                    input = getattr(pyg_types, f"InputMedia{media.__class__.__name__}")
                except AttributeError:
                    logger.info(f"В текущей версии pyrogram класс {media.__name__} входного медиа не был найден")
                    continue
                media_instance: pyg_types.InputMedia = input(media=media.file_id)
                attached_text = last_message.text or last_message.caption
                media_instance.caption = attached_text
                media_group.append(media_instance)
            else:
                await send(message, last_message, post_approval_keyboard())
            await state.set_state(Form.approve_post)
            time.sleep(TIMELAP_MESSAGE)
            

async def send_content_message(destination_channel: str, modified_content: Optional[str], last_message: types.Message):
    if last_message.photo:
        await pyrogram_service.send_message(destination_channel, modified_content, photo=last_message.photo.file_id)
    elif last_message.video:
        await pyrogram_service.send_message(destination_channel, modified_content, video=last_message.video.file_id)
    elif last_message.audio:
        await pyrogram_service.send_message(destination_channel, modified_content, audio=last_message.audio.file_id)
    elif last_message.voice:
        await pyrogram_service.send_message(destination_channel, modified_content, voice=last_message.voice.file_id)
    else:
        await pyrogram_service.send_message(destination_channel, modified_content)


async def monitor_channel_and_notify(message: types.Message, state: FSMContext, source_channel: str,
                                     destination_channel: str, user_id: int):
    while True:
        # Получаем последнее сообщение из исходного канала
        last_message = await pyrogram_service.get_last_message(source_channel)

        # Получаем ID последнего обработанного сообщения
        last_processed_message_id = await get_message_id_from_source_channel_by_user_id(source_channel, user_id)

        logger.info(f"last message id is: {last_message.id}, last processed message id is: {last_processed_message_id}, message_id: {message.message_id}")
        # Если есть новое сообщение, обрабатываем его
        if last_message.id > last_processed_message_id:
            await process_next_post(message, state, source_channel)
            logger.info(
                "Pyrogram обнаружил новое сообщение"\
                f"last message id is: {last_message.id},"\
                f"last processed message id is: {last_processed_message_id},"\
                f"message_id (from message at aiogram's input): {message.message_id},"\
                f"source_channel: {source_channel},"\
                f"destination_channel: {destination_channel}"
            )

            await message.answer(f"Новое сообщение обработано и отправлено в {destination_channel}")

        # Ждем 5 минут перед следующей проверкой
        await asyncio.sleep(60)
