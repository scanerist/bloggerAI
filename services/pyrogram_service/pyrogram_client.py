
from pyrogram import Client
from services.shared.config import Config

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

    async def get_last_message(self, channel: str):
        async for message in self.client.get_chat_history(channel, limit=1):
            return message

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