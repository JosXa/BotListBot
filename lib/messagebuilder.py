import collections
from typing import List

from telegram import *
from telegram.utils.helpers import escape


class MessageBuilder(collections.Mapping):
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self._rows = []  # type: List[KeyboardButton]
        self._inline_rows = []  # type: List[InlineKeyboardButton]
        self._text_parts = []  # type: List[str]
        self.disable_web_page_preview = False  # type: bool
        self.resize_keyboard = True  # type: bool

    def add_keyboard_row(self, *row_buttons) -> 'MessageBuilder':
        if len(self._inline_rows) > 0:
            raise ValueError(
                "Cannnot send both a reply and an inline keyboard in the same message."
            )

        if len(row_buttons) == 1:
            if isinstance(row_buttons[0], collections.Iterable):
                row_buttons = row_buttons[0]
            else:
                row_buttons = [row_buttons]

        self._rows.append(row_buttons)
        return self

    def add_inlinekeyboard_row(self, *row_buttons) -> 'MessageBuilder':
        if len(self._rows) > 0:
            raise ValueError(
                "Cannnot send both a reply and an inline keyboard in the same message."
            )

        if len(row_buttons) == 1:
            if isinstance(row_buttons[0], collections.Iterable):
                row_buttons = row_buttons[0]
            else:
                row_buttons = [row_buttons]

        self._inline_rows.append(row_buttons)
        return self

    @staticmethod
    def keyboard_button(text,
                        request_contact=None,
                        request_location=None,
                        **kwargs) -> KeyboardButton:
        return KeyboardButton(
            text,
            request_contact=request_contact,
            request_location=request_location,
            **kwargs)

    @staticmethod
    def inline_button(text,
                      url=None,
                      callback_data=None,
                      switch_inline_query=None,
                      switch_inline_query_current_chat=None,
                      callback_game=None,
                      pay=None,
                      **kwargs) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text,
            url=url,
            callback_data=callback_data,
            switch_inline_query=switch_inline_query,
            switch_inline_query_current_chat=switch_inline_query_current_chat,
            callback_game=callback_game,
            pay=pay,
            **kwargs)

    @property
    def reply_markup(self):
        if self._inline_rows:
            return InlineKeyboardMarkup(self._inline_rows)
        elif self._rows:
            return ReplyKeyboardMarkup(
                self._rows, resize_keyboard=self.resize_keyboard)

    # region text formatting

    def text(self, text) -> 'MessageBuilder':
        self._text_parts.append(escape(text))
        return self

    def bold(self, text) -> 'MessageBuilder':
        self._text_parts.append(f"<b>{escape(text)}</b>")
        return self

    def italic(self, text) -> 'MessageBuilder':
        self._text_parts.append(f"<i>{escape(text)}</i>")
        return self

    def code(self, text) -> 'MessageBuilder':
        self._text_parts.append(f"<pre>{text}</pre>")
        return self

    def smallcaps(self, text) -> 'MessageBuilder':
        smallcaps_chars = 'ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'
        lowercase_ord = 96
        uppercase_ord = 64

        result = ''
        for i in text:
            index = ord(i)
            if 122 >= index >= 97:
                result += smallcaps_chars[index - lowercase_ord - 1]
            elif 90 >= index >= 65:
                result += smallcaps_chars[index - uppercase_ord - 1]
            elif index == 32:
                result += ' '

        self._text_parts.append(result)
        return self

    def strikethrough(self, text) -> 'MessageBuilder':
        SPEC = '̶'
        result = ''.join([x + SPEC if x != ' ' else ' ' for x in text])
        self._text_parts.append(result)
        return self

    def headline1(self, text) -> 'MessageBuilder':
        self._text_parts.append("▶️ <b>{}</b>\n\n".format(escape(text)))
        return self

    # endregion

    def space(self) -> 'MessageBuilder':
        self._text_parts.append(" ")
        return self

    def newline(self, n=1) -> 'MessageBuilder':
        self._text_parts.append("\n" * n)
        return self

    @property
    def parse_mode(self):
        return ParseMode.HTML

    @property
    def full_text(self):
        return ''.join(self._text_parts)

    # region tuple unpacking

    def __getitem__(self, key):
        return self.__dict__()[key]

    def __len__(self):
        return len(self.__dict__())

    def __iter__(self):
        return iter(self.__dict__())

    def __dict__(self):
        return dict(
            text=self.full_text,
            chat_id=self.peer_id,
            parse_mode=self.parse_mode,
            reply_markup=self.reply_markup)

    # endregion
