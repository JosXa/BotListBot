from __future__ import absolute_import

import json
import unittest
from pprint import pprint

from components import explore
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

from ptbtest import ChatGenerator
from ptbtest import MessageGenerator
from ptbtest import Mockbot
from ptbtest import UserGenerator

class TestExplore(unittest.TestCase):
    def setUp(self):
        # For use within the tests we nee some stuff. Starting with a Mockbot
        self.bot = Mockbot()
        # Some generators for users and chats
        self.ug = UserGenerator()
        self.cg = ChatGenerator()
        # And a Messagegenerator and updater (for use with the bot.)
        self.mg = MessageGenerator(self.bot)
        self.updater = Updater(bot=self.bot)

    def test_help(self):
        # Then register the handler with he updater's dispatcher and start polling
        self.updater.dispatcher.add_handler(CommandHandler("explore", explore.explore, pass_chat_data=True))
        self.updater.start_polling()
        # We want to simulate a message. Since we don't care wich user sends it we let the MessageGenerator
        # create random ones
        update = self.mg.get_message(text="/explore")
        # We insert the update with the bot so the updater can retrieve it.
        self.bot.insertUpdate(update)
        # sent_messages is the list with calls to the bot's outbound actions. Since we hope the message we inserted
        # only triggered one sendMessage action it's length should be 1.
        self.assertEqual(len(self.bot.sent_messages), 1)
        sent = self.bot.sent_messages[0]
        self.assertEqual(sent['method'], "sendMessage")
        self.updater.stop()

    def test_start(self):
        def start(bot, update):
            update.message.reply_text('Hi!')

        self.updater.dispatcher.add_handler(CommandHandler("start", start))
        self.updater.start_polling()
        # Here you can see how we would handle having our own user and chat
        user = self.ug.get_user(first_name="Test", last_name="The Bot")
        chat = self.cg.get_chat(user=user)
        update = self.mg.get_message(user=user, chat=chat, text="/start")
        self.bot.insertUpdate(update)
        self.assertEqual(len(self.bot.sent_messages), 1)
        sent = self.bot.sent_messages[0]
        self.assertEqual(sent['method'], "sendMessage")
        self.assertEqual(sent['text'], "Hi!")
        self.updater.stop()

    def test_echo(self):
        def echo(bot, update):
            update.message.reply_text(update.message.text)

        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, echo))
        self.updater.start_polling()
        update = self.mg.get_message(text="first message")
        update2 = self.mg.get_message(text="second message")
        self.bot.insertUpdate(update)
        self.bot.insertUpdate(update2)
        self.assertEqual(len(self.bot.sent_messages), 2)
        sent = self.bot.sent_messages
        self.assertEqual(sent[0]['method'], "sendMessage")
        self.assertEqual(sent[0]['text'], "first message")
        self.assertEqual(sent[1]['text'], "second message")
        self.updater.stop()


if __name__ == '__main__':
    unittest.main()
