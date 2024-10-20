from .base import connection
from services.shared.logger import setup_logger
from .models import User, DestinationChannel, SourceChannel, Instruction
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

logger = setup_logger(__name__)

@connection
async def set_user(session, username: str, user_tg_id: int):
    try:
        user = await session.scalar(select(User).filter_by(id=user_tg_id))
        if not user:
            new_user = User(id=user_tg_id, username=username)
            session.add(new_user)
            await session.commit()
            logger.info(f"User {username} with id {user_tg_id} added to the database")
            return None
        else:
            logger.info(f"User {username} with id {user_tg_id} already exists in the database")
            return user
    except SQLAlchemyError as e:
        logger.error(f"Error while adding user {username} with id {user_tg_id} to the database: {e}")
        return e

@connection
async def set_source_channel(session, channel_name: str, user_id: int, last_processed_message_id: int = 0):
    try:
        user = await session.scalar(select(User).filter_by(id=user_id))
        if not user:
            logger.error(f"User with id {user_id} not found in the database")
            return None
        source_channel = SourceChannel(channel_name=channel_name, user_id=user_id, last_processed_message_id=last_processed_message_id)
        if await session.scalar(select(SourceChannel).filter_by(channel_name=channel_name)) and await session.scalar(select(SourceChannel).filter_by(user_id=user_id)):
            logger.info(f"Source channel {channel_name} already exists in the database")
            return source_channel
        session.add(source_channel)
        await session.commit()
        logger.info(f"Source channel {channel_name} added to the database for user {user.username}")
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error while adding source channel: {e}")
        return e

@connection
async def set_destination_channel(session, channel_name: str, user_id: int):
    try:
        user = await session.scalar(select(User).filter_by(id=user_id))
        if not user:
            logger.error(f"User with id {user_id} not found in the database")
            return None
        destination_channel = DestinationChannel(channel_name=channel_name, user_id=user_id)
        if await session.scalar(select(DestinationChannel).filter_by(channel_name=channel_name)):
            logger.info(f"Destination channel {channel_name} already exists in the database")
            return destination_channel
        session.add(destination_channel)
        await session.commit()
        logger.info(f"Destination channel {channel_name} added to the database for user {user.username}")
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error while adding destination channel {e}")
        return e

@connection
async def set_instruction(session, text: str, user_id: int):
    try:
        user = await session.scalar(select(User).filter_by(id=user_id))
        if not user:
            logger.error(f"User  with id {user_id} not found in the database")
            return None
        instruction = Instruction(text=text, user_id=user_id)
        session.add(instruction)
        await session.commit()
        logger.info(f"Instruction {text} added to the database ")
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error while adding instruction {text} for destination channel to the database: {e}")
        return e

@connection
async def get_source_channel_by_id(session, user_id: int):
    try:
        source_channel = await session.scalar(select(SourceChannel.channel_name).filter_by(user_id=user_id))
        if not source_channel:
            logger.error(f"Source channel  not found in the database")
            return None
        return source_channel
    except SQLAlchemyError as e:
        logger.error(f"Error while getting source channel from the database: {e}")
        return e

@connection
async def get_destination_channel_by_id(session, user_id: int):
    try:
        destination_channel = await session.scalar(select(DestinationChannel.channel_name).filter_by(user_id=user_id))
        if not destination_channel:
            logger.error(f"Destination channel  not found in the database")
            return None
        return destination_channel
    except SQLAlchemyError as e:
        logger.error(f"Error while getting destination channel from the database: {e}")
        return e

@connection
async def get_instruction_by_id(session, user_id: int):
    try:
        instruction = await session.scalar(select(User).filter_by(id=user_id))
        if not instruction:
            logger.error(f"Instruction  not found in the database")
            return None
        return instruction
    except SQLAlchemyError as e:
        logger.error(f"Error while getting instruction from the database: {e}")
        return e

@connection
async def get_user_by_id(session, user_id: int):
    try:
        user = await session.scalar(select(User).filter_by(id=user_id))
        if not user:
            logger.error(f"User  not found in the database")
            return None
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error while getting user from the database: {e}")
        return e

@connection
async def get_all_source_channels_by_user_id(session, user_id: int):
    try:
        source_channels = await session.execute(select(SourceChannel.channel_name).filter_by(user_id=user_id))
        return source_channels.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error while getting all source channels from the database: {e}")
        return e

@connection
async def get_all_destination_channels_by_user_id(session, user_id: int):
    try:
        destination_channels = await session.execute(select(DestinationChannel.channel_name).filter_by(user_id=user_id))
        return destination_channels.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error while getting all destination channels from the database: {e}")
        return e


@connection
async def get_all_instructions_by_user_id(session, user_id: int):
    try:
        instructions = await session.execute(select(Instruction.text).filter_by(user_id=user_id))
        return instructions.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error while getting all instructions from the database: {e}")
        return e

@connection
async def delete_source_channel(session, channel_name: str):
    try:
        source_channel = await session.scalar(select(SourceChannel).filter_by(channel_name=channel_name))
        if not source_channel:
            logger.error(f"Source channel {channel_name} not found in the database")
            return None
        session.delete(source_channel)
        await session.commit()
        logger.info(f"Source channel {channel_name} deleted from the database")
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error while deleting source channel {channel_name} from the database: {e}")
        return e

@connection
async def delete_destination_channel(session, channel_name: str):
    try:
        destination_channel = await session.scalar(select(DestinationChannel).filter_by(channel_name=channel_name))
        if not destination_channel:
            logger.error(f"Destination channel {channel_name} not found in the database")
            return None
        session.delete(destination_channel)
        await session.commit()
        logger.info(f"Destination channel {channel_name} deleted from the database")
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error while deleting destination channel {channel_name} from the database: {e}")
        return e

@connection
async def delete_instruction(session, text: str):
    try:
        instruction = await session.scalar(select(Instruction).filter_by(text=text))
        if not instruction:
            logger.error(f"Instruction {text} not found in the database")
            return None
        session.delete(instruction)
        await session.commit()
        logger.info(f"Instruction {text} deleted from the database")
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error while deleting instruction {text} from the database: {e}")
        return e

@connection
async def update_source_channel(session, channel_name: str, last_processed_message_id: int):
    try:
        source_channel = await session.scalar(select(SourceChannel).filter_by(channel_name=channel_name))
        if not source_channel:
            logger.error(f"Source channel {channel_name} not found in the database")
            return None
        source_channel.last_processed_message_id = last_processed_message_id
        await session.commit()
        logger.info(f"Source channel {channel_name} updated in the database")
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error while updating source channel {channel_name} in the database: {e}")
        return e

@connection
async def get_message_id_from_source_channel_by_user_id(session, channel_name: str, user_id: int):
    try:
        source_channel = await session.scalar(select(SourceChannel).filter_by(channel_name=channel_name, user_id=user_id))
        if not source_channel:
            logger.error(f"Source channel {channel_name} not found in the database")
            return None
        return source_channel.last_processed_message_id
    except SQLAlchemyError as e:
        logger.error(f"Error while getting message id from source channel {channel_name} from the database: {e}")
        return e

