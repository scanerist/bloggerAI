import asyncio
import time

from aiogram.types import BotCommand, BotCommandScopeDefault
from requests.exceptions import RequestException

from services.bot.bot import BloggerAiBot
from services.bot.handlers import start_handler, new_channel_parse_handler, channel_list_handler, parse_settings_handler, back_handler
from services.pyrogram_service.pyrogram_client import PyrogramService
from services.shared.logger import setup_logger

logger = setup_logger(__name__)

blogger_bot = BloggerAiBot()
bot = blogger_bot.get_bot()
dp = blogger_bot.get_dispatcher()

POLLING_TIMEOUT = 10

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
    while True:
        try:
            await dp.start_polling(
                bot, 
                polling_timeout=POLLING_TIMEOUT,
            )
            logger.info("Bot started")
        except RequestException as e:
            logger.info(f"Conncetion failed - {e}. Need to wait 30 seconds...")
            time.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())