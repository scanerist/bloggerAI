import asyncio
from services.shared.logger import setup_logger
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from services.bot.keyboards import main_menu_keyboard

start_router = Router()
logger = setup_logger(__name__)

@start_router.message(F.text == "/start")
async def start_handler(message: types.Message, state: FSMContext):
    await message.answer("Добро пожаловать в бот Blogger AI", reply_markup=main_menu_keyboard())
    logger.info("User started the bot")
    await state.clear()