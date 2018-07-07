import weakref

from lib.markdownformatter import MarkdownFormatter
from models import User
from telegram import Update, Update as TelegramUpdate
from telegram.ext import CallbackContext, Dispatcher

hooks_added = False
old_de_json = TelegramUpdate.de_json


# class Update(TelegramUpdate):
#     def __init__(self, **kwargs):
#         super(Update, self).__init__(**kwargs)
#
#         self._callback_manager: CallbackManager = None
#
#     def de_json(self, data, bot):
#         old_de_json(data, bot)
#
#     @property
#     def callback_manager(self) -> CallbackManager:
#         if self._callback_manager is None:
#             self._callback_manager = CallbackManager(appglobals.redis, self)
#         return self._callback_manager


class Context(CallbackContext):
    """
    Only viable for updates, not jobs.
    """

    def __init__(self, dispatcher: Dispatcher, update: Update = None):
        super(Context, self).__init__(dispatcher)

        self._update: Update = weakref.proxy(update) if update else None
        self._user: User = None
        self._formatter: MarkdownFormatter = None

    @property
    def user(self) -> User:
        if self._user is None:
            self._user = User.from_telegram_object(self._update.effective_user)
        return self._user

    @property
    def formatter(self) -> MarkdownFormatter:
        if self._formatter is None:
            self._formatter = MarkdownFormatter(self.bot, self.message_id)
        return self._formatter

    @property
    def message_id(self) -> int:
        return self._update.effective_message.message_id

    @classmethod
    def from_update(cls, update: Update, dispatcher: Dispatcher):
        self = cls(dispatcher, update)
        if update is not None and isinstance(update, Update):
            chat = update.effective_chat
            user = update.effective_user

            if chat:
                self.chat_data = dispatcher.chat_data[chat.id]
            if user:
                self.user_data = dispatcher.user_data[user.id]
            self._telegram_user = user
        return self


def patch_ptb_object(ptb_class, patched_class, init_method_name):
    setattr(ptb_class, init_method_name, getattr(patched_class, init_method_name))
    print(f"Patched `{ptb_class}.{init_method_name}` to be `{patched_class}.{init_method_name}`")


def add_hooks():
    global hooks_added
    if hooks_added:
        raise ValueError("Context hooks were already added.")
    # patch_ptb_object(CallbackContext, Context, "from_update")
    # patch_ptb_object(TelegramUpdate, Update, "de_json")
    hooks_added = True
