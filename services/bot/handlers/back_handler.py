from services.shared.logger import setup_logger
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from services.bot.handlers.start_handler import start_handler
from services.bot.keyboards import main_menu_keyboard

back_router = Router()
@back_router.callback_query(F.data == "back")
async def process_back(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик возврата на главное меню."""
    await callback_query.message.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await start_handler(callback_query.message, state)
    await state.clear()