import asyncio

from services.pyrogram_service.pyrogram_client import PyrogramService
from services.shared.logger import setup_logger

logger = setup_logger(__name__)

async def main():


    pyrogram_service = PyrogramService.get_instance()
    await pyrogram_service.start()
    logger.info("Pyrogram service started")

if __name__ == "__main__":
    asyncio.run(main())