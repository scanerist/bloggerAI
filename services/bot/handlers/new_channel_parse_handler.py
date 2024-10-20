import asyncio

from handlers import start_handler
from services.bot.bot_utils import process_next_post, send_content_message
from services.bot.state_manager import Form
from services.shared.logger import setup_logger
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from services.database.dao import set_user, set_source_channel, set_destination_channel, set_instruction, get_message_id_from_source_channel_by_user_id
from services.pyrogram_service.pyrogram_client import PyrogramService

new_channel_router = Router()
logger = setup_logger(__name__)
pyrogram_service = PyrogramService.get_instance()

@new_channel_router.callback_query(F.data == "new_channel")
async def process_new_channel(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    user = await set_user(username=callback_query.from_user.username, user_tg_id=callback_query.from_user.id)
    await callback_query.message.answer("Введите логин исходного канала (например, @source_channel):")
    await state.set_state(Form.source_channel)

@new_channel_router.message(Form.source_channel)
async def process_source_channel(message: types.Message, state: FSMContext):
    source_channel_name = message.text.strip()
    data = await state.get_data()
    await state.update_data(source_channel=source_channel_name)
    current_message_id_of_source_channel = await get_message_id_from_source_channel_by_user_id(source_channel_name, message.from_user.id)
    await state.update_data(last_processed_message_id=current_message_id_of_source_channel)
    await set_source_channel(channel_name=source_channel_name, user_id=message.from_user.id)
    await message.answer("Введите логин канала для публикации (например, @destination_channel):")
    await state.set_state(Form.destination_channel)

@new_channel_router.message(Form.destination_channel)
async def process_destination_channel(message: types.Message, state: FSMContext):
    destination_channel_name = message.text.strip()
    user_id = message.from_user.id
    try:
        member = await message.bot.get_chat_member(destination_channel_name, user_id)
        if member.status in ('administrator', 'creator'):
            data = await state.get_data()
            await message.answer("Вы являетесь администратором канала. Теперь введите инструкцию для изменения поста.")
            print(str(data.get('instruction')), str(data.get('source_channel')), str(data.get('destination_channel')), str(data.get('last_processed_message_id')))
            await set_destination_channel(destination_channel_name, user_id)
            await state.update_data(destination_channel=destination_channel_name)
            await state.set_state(Form.user_instruction)
        else:
            await message.answer("Вы не администратор этого канала.", )
    except Exception as e:
        await message.answer(f"Ошибка проверки формата, попробуйте снова")

@new_channel_router.message(Form.user_instruction)
async def process_user_instruction(message: types.Message, state: FSMContext):
    data = await state.get_data()
    instruction_content = message.text.strip()
    await set_instruction(instruction_content, message.from_user.id)
    await state.update_data(instruction=instruction_content)
    await process_next_post(message, state)


@new_channel_router.callback_query(F.data == "publish")
async def process_publish(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    destination_channel = data.get('destination_channel')
    modified_content = data.get('modified_content')
    last_message = await pyrogram_service.get_last_message(data.get('source_channel'))
    if not destination_channel or not modified_content:
        await callback_query.message.answer(f"Ошибка публикации: не найдены данные. {data}")
        return
    try:
        await send_content_message(destination_channel, modified_content, last_message)
        msg = await callback_query.message.edit_text("Пост опубликован!")
        await state.clear()
        await start_handler(callback_query.message, state)
        await asyncio.sleep(5)
        await msg.delete()
    except Exception as e:
        await callback_query.message.answer(f"Ошибка публикации: {e}")


