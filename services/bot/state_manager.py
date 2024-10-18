from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    source_channel = State()
    destination_channel = State()
    user_instruction = State()
    approve_post = State()
    continue_posting = State()
    update_instruction = State()
