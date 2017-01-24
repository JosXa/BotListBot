SAVE_CONVERSATIONS = True
TTS_TIMEOUT = 120  # seconds
SHOW_LETTER_AFTER_NUM_MSGS = 5
BOT_CONSIDERED_NEW = 30  # days
SELF_BOT_NAME = "botlist_testbot"
PROMOTION_MESSAGE = "Join @BOTLIST\nShare your bots in @BotListChat"


class BotStates:
    ADMIN_MENU, DUMMY, ADDING_BOT = range(3)


class CallbackActions:
    SELECT_CATEGORY = 'selcat'
    SEND_BOTLIST = 'sendbotlist'
    EDIT_BOT_SELECT_BOT = 'ebsb'
    EDIT_BOT_CAT_SELECTED = 'ebcs'
    EDIT_BOT_SELECT_CAT = 'editbotslcat'
    ADD_BOT_SELECT_CAT = 'addbot'
    SEND_BOT_DETAILS = 'sbdtls'
    SELECT_BOT_IN_CATEGORY = 'test'


