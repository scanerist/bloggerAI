from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Новый канал", callback_data="new_channel")
    builder.button(text="Список каналов", callback_data="channel_list")
    return builder.as_markup()

def post_approval_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Опубликовать", callback_data="publish")
    # builder.button(text="Пропустить", callback_data="skip")
    # builder.button(text="Остановить", callback_data="stop")
    # builder.button(text="Изменить инструкцию", callback_data="change_instruction")
    builder.button(text="Назад", callback_data="back")

    return builder.as_markup()

def back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="back")
    return builder.as_markup()