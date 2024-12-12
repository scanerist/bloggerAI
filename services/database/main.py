import asyncio
import time

from sqlalchemy.exc import OperationalError

from services.database.db import engine
from services.database.models import Base


async def create_db():

    while True:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
        except RuntimeError as e:
            print(f"CONNECTION ERROR {e}. TRY TO RE-CONNECT AGAIN...")
            time.sleep(2)
            continue
        except OperationalError as e:
            print(f"OPERATION WAS ENDED WITH ERROR: {e}")
            break
        else:
            print("CONNECTION COMPLETE")
            break

if __name__ == "__main__":
    asyncio.run(create_db())