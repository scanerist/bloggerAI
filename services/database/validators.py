from pyrogram.errors import exceptions
from sqlalchemy.orm import validates

from services.pyrogram_service.pyrogram_client import PyrogramService

pyrogram_service = PyrogramService.get_instance()


class ChannelValidatorMixin:

    @validates('channel_name')
    def validate_channel_name(self, key, channel_name: str):
        if not channel_name.startswith("@"):
            raise ValueError(f"Channel name {channel_name} should start with @")
        try:
            pyrogram_service.get_last_message(channel_name)
        except exceptions.UsernameInvalid as e:
            raise ValueError(f"Unsupported format channel name: {channel_name}")
        return channel_name
    
__all__ = (
    ChannelValidatorMixin,
)