import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PHONE_NUMBER = os.getenv("PHONE_NUMBER")
    DB_URL = os.getenv("DB_URL")
