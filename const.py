### START OF CONFIGURATION ###

# PREFERENCES
ADMINS = [62056065, 918962]
BOT_CONSIDERED_NEW = 30  # days
SELF_BOT_NAME = "bot_list_bot"
SELF_CHANNEL_USERNAME = "botlist_testchannel"
BOT_REGEX = r'.*(@[a-zA-Z0-9_\-]*).*'

# MESSAGES
PROMOTION_MESSAGE = "*Join* @BOTLIST\n*Share your bots in* @BotListChat"
HELP_MESSAGE = """
This bot was built to automate the process of receiving bots and adding them to the @BotList for review before they're published. It also creates "Share"  and "Copy Link" inline buttons for each category and allows you to send individual categories to your friends via inline search (i.e.: `@BotListBot music`).

This bot will also organise each category and send the final formated message on the @BotList to allow you to navigate the list with ease just by pressing on a category name.
"""

### END OF CONFIGURATION ###

from helpers import get_commands

COMMANDS = get_commands()

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
