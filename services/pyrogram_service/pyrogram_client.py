from collections.abc import AsyncGenerator
from typing import List, Union

from pyrogram import Client
import pyrogram.types as pyg_types

from services.shared.config import Config
from services.shared.logger import setup_logger


logger = setup_logger(__name__)

LIMIT_NUM_MESSAGES = 20

class PyrogramService:
    _instance = None

    def __init__(self):
        self.client = Client(
            "BH",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            phone_number=Config.PHONE_NUMBER
        )

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self):
        await self.client.start()

    async def stop(self):
        await self.client.stop()

    async def get_last_message(self, channel: str) -> pyg_types.Message:
        async for message in self.client.get_chat_history(channel, limit=1):
            return message
        
    async def get_last_messages(self, channel: str, last_id: int, limit: int=LIMIT_NUM_MESSAGES) -> AsyncGenerator[pyg_types.Message]:
        async for message in self.client.get_chat_history(channel, offset_id=last_id, limit=limit):
            logger.info(f"message: {message}")
            yield message
    
    async def get_messages(self, chat_id: Union[str, int], message_id: Union[int, List[int]]):
        return (await self.client.get_messages(chat_id, message_id))

    async def send_message(self, channel: str, text: str, photo=None, video=None, audio=None, voice=None):
        if photo:
            await self.client.send_photo(channel, photo, caption=text)
        elif video:
            await self.client.send_video(channel, video, caption=text)
        elif audio:
            await self.client.send_audio(channel, audio, caption=text)
        elif voice:
            await self.client.send_voice(channel, voice, caption=text)
        else:
            await self.client.send_message(channel, text)

    async def get_chat_member(self, channel: str, user_id: int):
        return await self.client.get_chat_member(channel, user_id)