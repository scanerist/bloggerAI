import asyncio

from aiogram.types import BotCommand, BotCommandScopeDefault

from services.bot.bot import BloggerAiBot
from services.bot.handlers import start_handler, new_channel_parse_handler, channel_list_handler, parse_settings_handler, back_handler
from services.pyrogram_service.pyrogram_client import PyrogramService
from services.shared.logger import setup_logger

logger = setup_logger(__name__)

blogger_bot = BloggerAiBot()
dp = blogger_bot.get_dispatcher()
bot = blogger_bot.get_bot()

async def set_commands():
    commands = [BotCommand(command='start', description='Старт')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

async def start_bot():
    await set_commands()

async def main():


    pyrogram_service = PyrogramService.get_instance()
    await pyrogram_service.start()
    logger.info("Pyrogram service started")

    dp.include_router(start_handler.start_router)
    dp.include_router(new_channel_parse_handler.new_channel_router)
    dp.include_router(channel_list_handler.channel_list_router)
    dp.include_router(parse_settings_handler.parse_setting_router)
    dp.startup.register(start_bot)
    dp.include_router(back_handler.back_router)
    await dp.start_polling(bot)
    logger.info("Bot started")


if __name__ == "__main__":
    asyncio.run(main())