import unittest

from telegram import Message

def _make_message(text):
    return Message(chat=None,  text=text)

class TestExplore(unittest.TestCase):

    def test_extract_bot_mentions_single(self):
        test_message = _make_message("")

