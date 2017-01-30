ADMINS = [62056065, 918962]
SAVE_CONVERSATIONS = True
TTS_TIMEOUT = 120  # seconds
SHOW_LETTER_AFTER_NUM_MSGS = 5
BOT_CONSIDERED_NEW = 30  # days
SELF_BOT_NAME = "bot_list_bot"
SELF_CHANNEL_NAME = ""
PROMOTION_MESSAGE = "*Join* @BOTLIST\n*Share your bots in* @BotListChat"
HELP_MESSAGE = """
This bot was built to automate the process of receiving bots and adding them to the @BotList for review before they're published. It also creates "Share"  and "Copy Link" inline buttons for each category of the list and allows you to send individual categories to your friends via inline search.
(i.e.: `@BotListBot music`)

This bot will also organise each category and send the final formated message on the @BotList to allow you to navigate the list with ease just by pressing on a category name.
"""


class BotStates:
    ADMIN_MENU, \
    DUMMY, \
    ADMIN_ADDING_BOT, \
    EDITING_BOT = \
        range(4)


class CallbackStates:
    SHOWING_BOT_DETAILS, \
    SELECTING_BOT, \
    SELECTING_CATEGORY, \
    APPROVING_BOTS, \
    DUMMY2, \
    DUMMY3, \
        = range(6)


class CallbackActions:
    BACK = 'back'
    CATEGORY_SELECTED = 'cat_selected'
    ACCEPT_BOT_CAT_SELECTED = 'accbotcatsel'
    ACCEPT_BOT = 'acceptbot'
    RESEND_BOTLIST = 'resendbotlist'
    SELECT_CATEGORY = 'selcat'
    SEND_BOTLIST = 'sendbotlist'
    EDIT_BOT_SELECT_BOT = 'ebsb'
    EDIT_BOT_CAT_SELECTED = 'ebcs'
    EDIT_BOT_SELECT_CAT = 'editbotslcat'
    ADD_BOT_SELECT_CAT = 'addbot'
    SEND_BOT_DETAILS = 'sbdtls'
    SELECT_BOT_IN_CATEGORY = 'test'
