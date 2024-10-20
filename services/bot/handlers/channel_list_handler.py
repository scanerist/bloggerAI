from services.bot.keyboards import back_button
from services.shared.logger import setup_logger
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from services.database.dao import get_all_destination_channels_by_user_id, get_all_source_channels_by_user_id, get_all_instructions_by_user_id


channel_list_router = Router()

@channel_list_router.callback_query(F.data == "channel_list")
async def process_channel_list(callback_query: types.CallbackQuery, state: FSMContext):
    source_channels = list(await get_all_source_channels_by_user_id(callback_query.from_user.id))
    destination_channels = list(await get_all_destination_channels_by_user_id(callback_query.from_user.id))
    instructions = list(await get_all_instructions_by_user_id(callback_query.from_user.id))
    if not source_channels or not destination_channels or not instructions:
        await callback_query.message.answer( "Список каналов пуст.", reply_markup=back_button())
        return

    channel_info = "Список каналов:\n\n"
    min_length = min(len(source_channels), len(destination_channels), len(instructions))
    for idx in range(min_length):
        channel_info += (
            f"{idx}. Исходный канал: {source_channels[idx]}\n"
            f"   Канал назначения: {destination_channels[idx]}\n"
            f"   Текущая инструкция: {instructions[idx]}\n\n"
        )

    await callback_query.message.answer(channel_info, reply_markup=back_button())
