from services.bot.bot_utils import process_next_post
from services.bot.state_manager import Form
from services.shared.logger import setup_logger
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext



parse_setting_router = Router()

@parse_setting_router.callback_query(F.data == "skip")
async def process_skip(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Пропуск поста...")
    await process_next_post(callback_query.message, state)

@parse_setting_router.callback_query(F.data == "stop")
async def process_stop(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Публикация остановлена.")
    await state.clear()


@parse_setting_router.callback_query(F.data == "change_instruction")
async def process_change_instruction(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите новую инструкцию.")
    await state.set_state(Form.update_instruction)


@parse_setting_router.message(Form.update_instruction)
async def process_new_instruction(message: types.Message, state: FSMContext):
    new_instruction = message.text.strip()
    await state.update_data(instruction=new_instruction)
    await message.answer(f"Новая инструкция сохранена: {new_instruction}")
    await process_next_post(message, state)