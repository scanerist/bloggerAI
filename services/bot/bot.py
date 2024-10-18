from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from services.shared.config import Config
from aiogram.types import BotCommand

class BloggerAiBot:
    def __init__(self):
        self.bot = Bot(token=Config.BOT_TOKEN)
        self.storage = MemoryStorage()
        self.dispatcher = Dispatcher(storage=self.storage)

    def get_dispatcher(self) -> Dispatcher:
        return self.dispatcher

    def get_bot(self) -> Bot:
        return self.bot





