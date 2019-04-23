from typing import *
from uuid import uuid4
from redis_collections import Dict as RedisDict
from telegram import InlineKeyboardButton

from models import User


class CallbackManager:
    def __init__(self, redis, user: User):
        self.redis = redis
        key = 'callbacks_{}'.format(user.id)
        self._callbacks = RedisDict(redis=redis, key=key)

    def create_callback(self, action: int, data: Dict) -> str:
        id_ = str(uuid4())

        callback = dict(action=action, data=data)
        self._callbacks[id_] = callback

        return id_

    def inline_button(self, caption: str, action: int, data: Dict = None) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=caption,
            callback_data=self.create_callback(action, data)
        )

    def lookup_callback(self, id_: Union[str, uuid4]) -> Any:
        return self._callbacks.get(id_)
