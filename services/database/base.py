from .db import async_session_maker, engine, Base

def connection(func):
    async def wrapper(*args, **kwargs):
        async with async_session_maker() as session:
            async with session.begin():
                return await func(session, *args, **kwargs)
    return wrapper
