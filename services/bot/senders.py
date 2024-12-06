import re
import time

from aiogram import types
from aiogram.exceptions import TelegramNetworkError
from aiogram.utils.keyboard import KeyboardBuilder
from pydantic import ValidationError
from pyrogram.errors import FileReferenceExpired
import pyrogram.types as pyg_types

from services.pyrogram_service.pyrogram_client import PyrogramService
from services.shared.logger import setup_logger

logger = setup_logger(__name__)
pyrogram_service = PyrogramService.get_instance()

class Base():

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

    def set_params(self, media: pyg_types.Object=None):
        new_caption = self.caption
        new_text = self.text

        if self.caption:
            if len(self.caption) > 1024:
                new_caption = self.caption.split(".")[0]
                new_text = self.caption + "\n\b"
                if self.text:
                    new_text += self.text
            while len(new_caption) > 1024:
                new_caption = new_caption.split(" ")
                index, _ = list(re.finditer(r"[\s]+|[\S]+", new_caption))[-1].span()
                new_caption = new_caption[:index]
                logger.info(f"Новый заголовок: {new_caption} обрезан на позиции {index}, {new_caption[index]}")

        self.params["text"] = new_text
        self.params["caption"] = new_caption
        self.params["reply_markup"] = self.reply_markup

    async def send(self, media: pyg_types.Object=None, **kwargs):
        self.set_params(media)
        await self.message.answer(
            **self.params,
            **self.kwargs
        )

    async def __call__(self, media: pyg_types.Object, **kwargs):
        await self.send(media, **kwargs)

class SendMethod(Base):

    async def __call__(self, media: pyg_types.Object, **kwargs):
        method = self.get_send_method()
        await self.send(media, method, **kwargs)

    async def send(self, method: callable=None, media: pyg_types.Object=None, **kwargs):
        self.set_params(media)
        await method(
            **self.params,
            **self.kwargs
        )

    def get_send_method(self,) -> callable:
        try:
            method_name = self.last_message.media.value
            return getattr(self.message,  f"answer_{method_name}")
        except AttributeError as e:
            raise ArithmeticError(
                f"Нет метода {method_name} передачи сообщения в целевом модуле {e}."\
                "Убедитесь, что версия aiogram >= 3.13"
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

    async def get_binIO(self):
        
        return (
            await pyrogram_service.client.download_media(
                getattr(getattr(self.last_message, self.last_message.media.value), "file_id")
              )
        )
    
    async def __call__(self, media: pyg_types.Object):
        send_method = self.get_send_method()
        #ПОУЧАЕТ ПУТЬ ФАЙЛА В СТРОКОВОМ ФОРМАТЕ:
         #/code/src/downloads/photo_2024-11-20_13-52-12_7439358946990620672.jpg
        try:
            file_path = await self.get_binIO()
        except FileReferenceExpired:
            logger.warning(f"Не удалось отправить сообщение. Истёк срок `file_id` вложенного контента")
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
    media = None
    if last_message.media:
        media = getattr(last_message, last_message.media.value)
        class_name = last_message.media.value.title().replace("_", "")
        sender = globals().get(class_name, "Text")
    elif last_message.service:
        logger.info(f"Пропуск служебного сообщения, id: {last_message.id}")
        return
    elif last_message.empty:
        logger.info(f"Пропуск пустого сообщения, id: {last_message.id}")
        return
    else:
        sender = Text
        if not last_message.text:
            logger.info(f"Неопознанный тип сообщения {last_message}, id: {last_message.id}, будет использоваться текст.")

    send = sender(message, last_message, reply_markup)
    while True:
        try:
            await send(media)
        except TelegramNetworkError as e: 
            
            logger.info(f"Произошла ошибка о время отправки одиночного сообщения: {e}. Полуминутная пауза...")
            if "Request Entity Too Large" in e:
                logger.warning(
                    f"Не удалось отправить сообщение {last_message}, id {last_message.id}."\
                    "Слишком большой размер отправляемого контента"
                )
                break
            time.sleep(30)
    
        except ValidationError as e:
            logger.info(f"Ошибка в данных api. Детали: {e}") 
            break
        else: 
            break