import asyncio
import time

from sqlalchemy.exc import OperationalError

from services.database.db import engine
from services.database.models import Base


async def create_db():

    while True:
        try:
            async with engine.begin() as conn:
                #await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
                
        except RuntimeError as e:
            print(f"ОШИБКА СОЕДИНЕНИЯ {e}. ПОВТОРНАЯ ПОПЫТКА СОЕДИНЕНИЯ")
            time.sleep(2)
            continue
        except OperationalError as e:
            print(f"ОПЕРАЦИЯ ЗАВЕРШИЛАСЬ С ОШИБКОЙ {e}")
            break
        else:
            print("СОЕДИНЕНИЕ УСТАНОВЛЕНО")
            break

if __name__ == "__main__":
    asyncio.run(create_db())