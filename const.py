### START OF CONFIGURATION ###

# PREFERENCES
from model import Channel

ADMINS = [62056065, 918962]
BOT_CONSIDERED_NEW = 15  # days
SELF_BOT_NAME = "bot_list_bot"
SELF_BOT_ID = "265482650"
SELF_CHANNEL_USERNAME = "botlist"
REGEX_BOT_IN_TEXT = r'.*(@[a-zA-Z]+[a-zA-Z0-9_\-]{3,}).*'
REGEX_BOT_ONLY = r'(@[a-zA-Z]+[a-zA-Z0-9_\-]{3,})'


# MESSAGES
PROMOTION_MESSAGE = "*Join* @BOTLIST\n*Share your bots in* @BotListChat"
HELP_MESSAGE = """
This bot is a mirror of the @BotList.
It was built to simplify navigation and to automate the process of submitting, reviewing and adding bots to the @BotList by the @BotListChat community.

*Try it out:* Start off by using the /category command and use the available buttons from there on.
You can also send individual @BotList categories to your friends via inline search (i.e. type `@bot_list_bot music` in any chat).

If you want to check before contributing, you can also send me the `@username` of a bot and I will see whether it exists in the @BotList.
"""
CONTRIBUTING_MESSAGE = """
You can use the following `#tag`s with a bot `@username` to contribute to the BotList:

• #new — Submit a fresh bot. Use 🔎 if it supports inline queries and flag emojis to denote the language.
• #offline — Mark a bot as offline.

There are also the /new and /offline commands.

The moderators will approve your submission as soon as possible.
"""
EXAMPLES_MESSAGE = """
*Examples for contributing to the BotList:*
• Wow! I found this cool #new bot: @coolbot 🔎🇮🇹
• /new @coolbot 🔎🇮🇹

• Eh... guys?! @unresponsive\_bot is #offline 😞
• /offline @unresponsive\_bot
"""

### END OF CONFIGURATION ###

from helpers import get_commands

COMMANDS = get_commands()


def get_channel():
    try:
        return Channel.get(Channel.username == SELF_CHANNEL_USERNAME)
    except Channel.DoesNotExist:
        return False


big_range = list(range(512))


class BotStates:
    SENDING_USERNAME, \
    SENDING_NAME, \
    SENDING_EXTRA, \
    SENDING_DESCRIPTION, \
    ADMIN_MENU, \
    DUMMY, \
    ADMIN_ADDING_BOT, \
    EDITING_BOT, \
    *rest = big_range


class CallbackStates:
    SHOWING_BOT_DETAILS, \
    SELECTING_BOT, \
    SELECTING_CATEGORY, \
    APPROVING_BOTS, \
    DUMMY2, \
    DUMMY3, \
    *rest = big_range


class CallbackActions:
    REJECT_SUGGESTION, \
    ACCEPT_SUGGESTION, \
    PERMALINK, \
    CONFIRM_DELETE_BOT, \
    DELETE_BOT, \
    EDIT_BOT_OFFLINE, \
    REJECT_BOT, \
    SET_COUNTRY, \
    EDIT_BOT, \
    BOT_ACCEPTED, \
    BACK, \
    CATEGORY_SELECTED, \
    ACCEPT_BOT_CAT_SELECTED, \
    ACCEPT_BOT, \
    RESEND_BOTLIST, \
    SELECT_CATEGORY, \
    SEND_BOTLIST, \
    EDIT_BOT_SELECT_BOT, \
    EDIT_BOT_CAT_SELECTED, \
    EDIT_BOT_SELECT_CAT, \
    ADD_BOT_SELECT_CAT, \
    SEND_BOT_DETAILS, \
    SELECT_BOT_FROM_CATEGORY, \
    EDIT_BOT_NAME, \
    EDIT_BOT_USERNAME, \
    EDIT_BOT_DESCRIPTION, \
    EDIT_BOT_COUNTRY, \
    EDIT_BOT_EXTRA, \
    EDIT_BOT_INLINEQUERIES, \
    EDIT_BOT_OFFICIAL, \
    *rest = big_range
