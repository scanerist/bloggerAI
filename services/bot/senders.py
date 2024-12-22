"""
Template which allows to send single object of pyrogram.types.Message 
throught aiogram.types.Message object
"""

import re
import time

from aiogram import Bot, types
from aiogram.exceptions import TelegramNetworkError
from aiogram.utils.keyboard import KeyboardBuilder
from pydantic import ValidationError
from pyrogram.errors import FileReferenceExpired
import pyrogram.types as pyg_types

from services.pyrogram_service.pyrogram_client import PyrogramService
from services.shared.config import Config
from services.shared.logger import setup_logger
from typing import Union

bot = Bot(token=Config.BOT_TOKEN)
logger = setup_logger(__name__)
pyrogram_service = PyrogramService.get_instance()
FILE_SIZE_LIMIT = 50 #No more than 50 Mb
TEXT_SIZE_LIMIT = 1024 #No more than 1024 characters

def get_classname_media(media: pyg_types.Object):
    """
    Returns class name for message's media attribute 
    """
    if media.value:
        return media.value.title().replace("_", "")
    else:
        return str(media)

class Base():
    """
    Class with functional, which sets basic parameters:
    text attributes and `reply_markup` for sending messages
    considering telegram api limitations and sends messages of 
    pyrogram.types.Message type throght aiogram
    """

    def __init__(
            self, 
            aio_message: types.Message, 
            pyg_message: pyg_types.Message,
            reply_markup: KeyboardBuilder
        ):
        self.message = aio_message
        self.last_message = pyg_message
        self.caption = pyg_message.caption
        self.text = pyg_message.text
        self.reply_markup = reply_markup
        self.kwargs = {}
        self.params = {}

    def set_kwargs(self, params: dict=dict(), full_rewrite=False, clear=False):
        self.kwargs.update(params)
        if clear:
            self.kwargs.clear()
            return
        if full_rewrite:
            self.kwargs = params

    @classmethod
    def cut_text(self, caption: Union[str, None]=None, text: Union[str, None]=None):
        """
        Cut message's text attributes `caption`, `text` and return new values of them

        ----------
        Parameters

        caption: str

        text: str

        -------
        Returns

        text_attributes: tuple(new_caption: str, new_text: str) 

        where:
        
        new_caption: str
                     New value for message's attribute `caption`

        new_text: str
                  New value for message's attribute `text`
        """
        new_caption = caption
        new_text = text
        if caption:
            if len(caption) > TEXT_SIZE_LIMIT:
                new_caption = caption.split(".")[0]
                new_text = caption + "\n\b"
                new_text = new_text + text if text else new_text
            while len(new_caption) > TEXT_SIZE_LIMIT:
                index, _ = list(re.finditer(r"[\s]+|[\S]+", new_caption.split(" ")))[-1].span()
                new_caption = new_caption[:index]
                logger.info(f"New caption: {new_caption} was cuted at pos. {index}, {new_caption[index]}")
        return new_caption, new_text


    def set_params(self, media: pyg_types.Object=None):
        new_caption, new_text = self.cut_text(self.caption, self.text)
        self.params["text"] = new_text
        self.params["caption"] = new_caption
        self.params["reply_markup"] = self.reply_markup

    async def send(self, *args, **kwargs):
        try:
            media = args[0]
        except IndexError:
            media=kwargs.get("media")
        self.set_params(media)
        forward_from_message_id = self.last_message.forward_from_message_id
        if not any((self.caption, self.text)) and forward_from_message_id:

            forwarded_message = await pyrogram_service.get_messages(
                chat_id=self.last_message.forward_from_chat.id,
                message_id=forward_from_message_id
            )
            await send(self.message, forwarded_message, self.reply_markup)
        else:
            await self.message.answer(
                **self.params,
                **self.kwargs
            )

    async def __call__(self, *args, **kwargs):
        await self.send(*args, **kwargs)

class SendMethod(Base):
    """
    Aim of this class is the same as class `Base` except for 
    support an additional media content than just only text
    if the message includes such content.

    Applies for such types of messages which includes 
    a specific content besides the text
    """

    async def __call__(self, media: pyg_types.Object, **kwargs):
        method = self.get_send_method()
        await self.send(method, media)

    async def send(self, method: callable=None, media: pyg_types.Object=None):
        self.set_params(media)
        await method(
            **self.params,
            **self.kwargs
        )

    def get_send_method(self,) -> callable:
        """
        Finds the sending method in aiogram.types.Message

        -------
        Returns

        send_method: aiogram.types.message.answer_<A_TYPE_OF_MESSAGE>
        """
        try:
            method_name = self.last_message.media.value
            return getattr(self.message,  f"answer_{method_name}")
        except AttributeError as e:
            raise AttributeError(
                f"Method {method_name} of sending message is absent in the using module - {e}."\
                "Check aiogram version is v >= 3.13"
            )

class Text(Base):
    pass

class WebPage(Base):

    def set_params(self, media: pyg_types.WebPage):
        super().set_params(media)
        text = f"{self.text}. {media.site_name}: {media.url}"
        if self.caption:
            text = f"{self.caption}.\n\b" + text
        if media.title:
            text = f"{media.title}.\n\b" + text
        self.params["text"] = text
    
class Contact(SendMethod):

    def set_params(self, media: pyg_types.Contact):
        super().set_params(self, media)
        self.params.update({
            "phone_number" : media.phone_number,
            "first_name": media.first_name,
            "last_name": media.last_name,
            "vcard": media.vcard,
        })

class Dice(SendMethod):

    def set_params(self, media: pyg_types.Dice):
        super().set_params(media)
        self.params.update({
            "emoji" : media.emoji
        })

class Game(SendMethod):

    def set_params(self, media: pyg_types.Game):
        super().set_params(media)
        self.params.update({
            "game_short_name": media.short_name
        })

class Location(SendMethod):

    def set_params(self, media: pyg_types.Location):
        super().set_params(media)
        self.params.update({
            "latitude": media.latitude,
            "longitude": media.longitude,
        })

class Poll(SendMethod):

    def set_params(self, media: pyg_types.Poll):
        super().set_params(media)
        self.params.update({
            "question": media.question,
            "options": media.options,
            "allows_multiple_answers": media.allows_multiple_answers,
            "explanation": media.explanation,
            "explanation_entities": media.explanation_entities,
            "is_anonymous": media.is_anonymous,
            "is_closed": media.is_closed,
            "type": media.type,
            "open_period": media.open_period,
            "close_date": media.close_date,
        })

class Venue(SendMethod):

    def set_params(self, media: pyg_types.Venue):
        super().set_params(media)
        self.params.update({
            "address": media.address,
            "foursquare_id": media.foursquare_id,
            "foursquare_type": media.foursquare_type,
            "latitude": media.location.latitude,
            "longitude": media.location.longitude,
            "title": media.title,
        })

class File(SendMethod):
    """ 
    This class does the same work as `SendMethod` class except for 
    support the additional media content as a file and related i/o actions.

    Applies for such types of messages which includes a file.
    """

    async def get_file(self) -> str:
        """
        Download and save the file at the server

        -------
        Returns

        file_path: str 
                   File path
        """
        return (
            await pyrogram_service.client.download_media(
                getattr(getattr(self.last_message, self.last_message.media.value), "file_id")
              )
        )
    
    async def __call__(self, media: pyg_types.Object):
        send_method = self.get_send_method()
        message_id = self.last_message.id
        file_size = media.file_size / (10**6)

        if file_size > FILE_SIZE_LIMIT:
            logger.warning(
                f"Message with id={message_id} wasn't sent. Too large attached content."\
                f"File size should be smaller than 50 Mb. Sending file's size is {file_size} Mb"
            )
            return
        try: 
            #Get file path as string, for example: '/code/src/downloads/photo.jpg'
            file_path = await self.get_file()
        except FileReferenceExpired:
            logger.warning(f"Message with id={message_id} wasn't sent. `file_id` of attached content was expired.")
            return
        file_name = file_path.split("/")[-1]
        file_bytes = b""
        with open(file_path, "rb") as file:
            file_bytes = file_bytes.join(file.readlines())

        await self.send(method=send_method, media=media, file=types.BufferedInputFile(file_bytes, file_name))

    async def send(self, method: callable, file: types.BufferedInputFile, media: pyg_types.Object=None):
        self.set_params(media)
        await method(
            file,
            **self.params,
            **self.kwargs
        )

class Animation(File):

    def set_params(self, media: pyg_types.Animation):
        super().set_params(media)
        self.params.update({
            "duration": media.duration,
        })

class Audio(File):

    def set_params(self, media: pyg_types.Audio):
        super().set_params(media)
        self.params.update({
            "duration": media.duration,
            "title": media.title
        })

class Document(File):
    pass

class Photo(File):
    pass

class Sticker(File):

    def set_params(self, media: pyg_types.Sticker):
        super().set_params(media)
        self.params.update({
            "emoji" : media.emoji
        })
        self.set_kwargs(
            {"is_animated": media.is_animated,
            "is_video": media.is_video,
            "file_name": media.file_name,
            "set_name": media.set_name,},
        )

class Video(File):

    def set_params(self, media: pyg_types.Video):
        super().set_params(media)
        self.params.update({
            "duration": media.duration,
            "supports_streaming": media.supports_streaming
        })

class VideoNote(File):

    def set_params(self, media: pyg_types.VideoNote):
        super().set_params(media)
        self.params.update({
            "duration": media.duration,
            "length": media.length
        })

class Voice(File):

    def set_params(self, media: pyg_types.Voice):
        super().set_params(media)
        self.params.update({
            "duration": media.duration
        })


async def send(message: types.Message, last_message: pyg_types.Message, reply_markup: KeyboardBuilder):
    """
    Sends message to the bot. Middleware between pyrogram message `last_message` 
    and sender as a found method of sending throght aiogram

    I.e. Basing of type message info `last_message.media.value`, text or something 
    other it finds corresponding sender class in this module or misses this message
    `last_message`
    -----------
    Parameters:

    message: aiogram.types.Message
             A original user message with text command in the bot's chat

    last_message: pyrogram.types.Message
                  Detected and unprocessed new message in source chat
                  which required to send to the bot

    reply_markup: aiogram.utils.keyboard.KeyboardBuilder
                  instance of this type, which build the keyboard
    """
    media = None
    if last_message.media:
        media = getattr(last_message, last_message.media.value)
        class_name = get_classname_media(last_message.media)
        sender = globals().get(class_name, "Text")
    elif last_message.service:
        logger.info(f"Miss a service message, id: {last_message.id}")
        return
    elif last_message.empty:
        logger.info(f"Miss an empty message, id: {last_message.id}")
        return
    else:
        sender = Text
        if not last_message.text:
            logger.info(f"Unrecognized type of message {last_message}, id: {last_message.id}, `Text` will be used for this one.")

    send = sender(message, last_message, reply_markup)
    while True:
        try:
            await send(media)
        except TelegramNetworkError as e: 
            
            logger.info(f"While a single message is sending an error was occured: {e}. Wait half a minute...")
            if "Request Entity Too Large" in e.message:
                logger.warning(
                    f"Message {last_message} wasn't sent, id {last_message.id}."\
                    "Too large size of sending attached content"
                )
                break
            time.sleep(30)
    
        except ValidationError as e:
            logger.info(f"It seems there is an error in api data. Details: {e}") 
            break
        else: 
            break