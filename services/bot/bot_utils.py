"""
Functional for monitoring new messages from source chat and sending them to the bot.

I.e. our bot 'monitors' new messages in source chat and notify us about them, 
also can to change text attributes via openAI.
"""

import asyncio
import time
from typing import Optional

from aiogram import types
from aiogram.fsm.context import FSMContext
from pyrogram import types as pyg_types

from services.bot.keyboards import post_approval_keyboard
from services.pyrogram_service.pyrogram_client import PyrogramService
from services.bot import senders
from services.bot.state_manager import Form
from services.database.dao import update_source_channel
from services.database.dao import get_message_id_from_source_channel_by_user_id
from services.shared.config import Config
from services.shared.logger import setup_logger
from typing import List

logger = setup_logger(__name__)
pyrogram_service = PyrogramService.get_instance()

TIMELAP_MESSAGE = 2


async def send_media_group(media_group: List[pyg_types.Message], state: FSMContext):
        """
        Send messages if they were grouped in one post (media group)

        -----------
        Parameters:

        media_group: List[pyg_types.Message] 
                     List of messages which are required to send

        state: aiogram.fsm.context.FSMContext 
                A machine of states which set `approve_post` state after sending message/s
        """
        
        if media_group:
            while True:
                try:
                    await pyrogram_service.client.send_media_group(
                        chat_id=Config.BOT_USERNAME, 
                        media=media_group
                    )
                except Exception as e:
                    logger.warning(
                        f"While media group messages are sending an error was occured - {e}"
                    )
                    break
                else:
                    await state.set_state(Form.approve_post)
                    break
        media_group.clear()

async def process_next_post(message: types.Message, state: FSMContext, source_channel: Optional[str]=None):
    """
    Checks if chat `source_channel` could consist a new unprocessed message and send it to the bot

    -----------
    Parameters:

    message: aiogram.types.Message
             User instruction Message object

    state: aiogram.fsm.context.FSMContext 
           A machine of states which set `approve_post` state after sending message

    source_channel: str | None 
                    Chat where we retrieve messages from
    """
    data = await state.get_data()
    source_channel = source_channel if source_channel else data.get('source_channel')
    if not source_channel:
        await message.answer("Source channel is not set. Please set the source channel and try again.")
        return

    last_message = await pyrogram_service.get_last_message(source_channel)
    last_processed_message_id = await get_message_id_from_source_channel_by_user_id(
        channel_name=source_channel, 
        user_id=message.from_user.id
    ) or last_message.id - 1
    await update_source_channel(source_channel, last_message.id)
    await state.update_data(last_processed_message_id=last_message.id)

    last_processed_media_group_id = 0
    media_group = []
    offset = last_message.id + 1
    iteration = 1
    while True:
        last_messages = pyrogram_service.get_last_messages(
            source_channel, 
            offset
        )
        async for last_message in last_messages:
            logger.debug(
                f"Iteration No.: {iteration} "\
                f"id of current message: {last_message.id}, "\
                f"id of last processed message: {last_processed_message_id}"
            )
            iteration +=1
            if last_message.id <= last_processed_message_id:
                await send_media_group(media_group, state)
                await message.answer(
                    f"All posts were processed. Pass..."\
                    f"Details: from source channel: {source_channel}, last_message_id: {last_message.id}, "\
                    f"last processed message_id, that recorded in state.data: {last_processed_message_id}"\
                    f"message_id as a parameter of method `process_next_post` message.id {message.message_id}"
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
                    classname_media = senders.get_classname_media(last_message.media)
                    input = getattr(pyg_types, f"InputMedia{classname_media}")
                except AttributeError:
                    logger.info(f"Class input media named {classname_media} wasn't found in the using version of pyrogram.")
                    continue
                media_instance: pyg_types.InputMedia = input(media=media.file_id)
                attached_text = last_message.text or last_message.caption
                media_instance.caption, _ = senders.Base.cut_text(attached_text)
                media_group.append(media_instance)
            else:
                await senders.send(message, last_message, post_approval_keyboard())
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
    """
    Investigates chat `source_channel` for new messages every minute and send them to the bot.
    Also it notifies about `destination_channel`

    -----------
    Parameters:

    message: aiogram.types.Message
             User instruction Message object

    state: aiogram.fsm.context.FSMContext 
           A machine of states which set `approve_post` state after sending message/s 

    source_channel: str | None 
                    Chat where we retrieve messages from

    destination_channel: str | None 
                         Chat where messages will be sent (notify only)

    user_id: int 
             id of user that monitors `source_channel`
             It's a part of composite key to get `Source_Channel` object
    """
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
                "Pyrogram detect a new message"\
                f"last message id is: {last_message.id},"\
                f"last processed message id is: {last_processed_message_id},"\
                f"message_id (from message at aiogram's input): {message.message_id},"\
                f"source_channel: {source_channel},"\
                f"destination_channel: {destination_channel}"
            )

            await message.answer(f"New message was processed and sent to {destination_channel}")

        # Ждем 5 минут перед следующей проверкой
        await asyncio.sleep(60)
