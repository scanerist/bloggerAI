import asyncio
from typing import Optional, Any

from aiogram import types
from aiogram.fsm.context import FSMContext
from pyrogram.errors import exceptions


from services.bot.keyboards import post_approval_keyboard
#from services.openai_service.openai_client import OpenAIService
from services.pyrogram_service.pyrogram_client import PyrogramService
from services.bot.state_manager import Form
from services.database.dao import update_source_channel
from services.database.dao import get_message_id_from_source_channel_by_user_id

from services.shared.logger import setup_logger

logger = setup_logger(__name__)
#openai_service = OpenAIService()
pyrogram_service = PyrogramService.get_instance()


def is_content(message: types.Message):
    return 

async def process_next_post(message: types.Message, state: FSMContext, source_channel: Optional[str] = None):
    data = await state.get_data()
    source_channel = source_channel if source_channel else data.get('source_channel')
    if not source_channel:
        await message.answer("Source channel is not set. Please set the source channel and try again.")
        return

    instruction = data.get('instruction')
    try:
        last_message = await pyrogram_service.get_last_message(source_channel)
    except exceptions.UsernameInvalid as e:
        err_message = f"Не поддерживаемый формат имени пользователя {source_channel}"
        logger.warning(err_message)
        raise ValueError(err_message)
    content: Any = last_message.text or last_message.caption or last_message.media or ""
    last_processed_message_id = data.get('last_processed_message_id')
    if last_message.id == last_processed_message_id:
        await message.answer(
            f"Все посты обработаны. Пропуск..."\
            f"Детали: из канала: {source_channel}, last_message_id: {last_message.id}, "\
            f"last processed message_id, записанное в state.data: {last_processed_message_id}"\
            f"message_id на вход метода `process_next_post` message.id {message.message_id}"
        )
        return
    if not content:
        await message.answer(
            f"Пустой пост. Пропуск... "\
            f"Детали: из канала: {source_channel}, last_message_id: {last_message.id}, "\
            f"last processed message_id, записанное в state.data: {last_processed_message_id}"\
            f"message_id на вход метода `process_next_post` message.id {message.message_id}"
        )
        try:
            await process_next_post(message, state)
            return
        except RecursionError as e:
            await message.answer(f"Проблема c обработкой сообщений из этого канала {source_channel}")
            return
    #modified_content = await openai_service.modify_post(content, instruction)
    modified_content = content +  "МОДИФИЦИРОВАН!" if type(content) == str else content

    if type(modified_content) != str:
        logger.info(f"Отправляемый контент не строка, а нечто: {modified_content}, вот все его атрибуты: {dir(modified_content)}")

    await state.update_data(modified_content=modified_content)
    await update_source_channel(source_channel, last_message.id)
    await message.answer(modified_content, reply_markup=post_approval_keyboard())
    await state.update_data(last_processed_message_id=last_message.id)
    await state.set_state(Form.approve_post)


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
