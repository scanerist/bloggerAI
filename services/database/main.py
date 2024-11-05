import asyncio
import time

from sqlalchemy.util import *

from services.database.db import engine
from services.database.models import Base


async def create_db():

    if engine.dialect.has_schema(engine.url):
        return
    while True:
        try:
            async with engine.begin() as conn:
                #await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            print(f"ОШИБКА СОЕДИНЕНИЯ {e}. ПОВТОРНАЯ ПОПЫТКА СОЕДИНЕНИЯ")
            time.sleep(2)
            continue
        else:
            print("СОЕДИНЕНИЕ УСТАНОВЛЕНО")
            break

if __name__ == "__main__":
    asyncio.run(create_db())