import asyncio
from typing import Optional

from aiogram import types
from aiogram.fsm.context import FSMContext

from services.bot.keyboards import post_approval_keyboard
from services.openai_service.openai_client import OpenAIService
from services.pyrogram_service.pyrogram_client import PyrogramService
from services.bot.state_manager import Form
from services.database.dao import update_source_channel
from services.database.dao import get_message_id_from_source_channel_by_user_id

openai_service = OpenAIService()
pyrogram_service = PyrogramService.get_instance()


async def process_next_post(message: types.Message, state: FSMContext, source_channel: Optional[str] = None):
    data = await state.get_data()
    source_channel = source_channel if source_channel else data.get('source_channel')
    if not source_channel:
        await message.answer("Source channel is not set. Please set the source channel and try again.")
        return

    instruction = data.get('instruction')
    last_message = await pyrogram_service.get_last_message(source_channel)
    content: str = last_message.text or last_message.caption or ""
    if last_message.id == data.get('last_processed_message_id'):
        await message.answer("Все посты обработаны. Пропуск...")
        return
    if not content:
        await message.answer("Пустой пост. Пропуск...")
        await process_next_post(message, state)
        return
    modified_content = await openai_service.modify_post(content, instruction)

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

        # Если есть новое сообщение, обрабатываем его
        if last_message.id > last_processed_message_id:
            await process_next_post(message, state, source_channel)
            print(last_message.id, last_processed_message_id, message.message_id, source_channel, destination_channel)

            await message.answer(f"Новое сообщение обработано и отправлено в {destination_channel}")

        # Ждем 5 минут перед следующей проверкой
        await asyncio.sleep(60)
