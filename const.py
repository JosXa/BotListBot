import os

### START OF CONFIGURATION ###

# PREFERENCES

MODERATORS = [62056065, 918962, 7679610, 278941742, 127782573, 43740047]
ADMINS = [62056065, 918962]
BOT_CONSIDERED_NEW = 14  # days
SELF_BOT_NAME = "botlistbot"
SELF_BOT_ID = "182355371" if bool(os.environ.get("DEV")) else "265482650"
BOTLISTCHAT_ID = -1001118582923 if bool(os.environ.get("DEV")) else -1001067163791
SELF_CHANNEL_USERNAME = "botlist_testchannel" if bool(os.environ.get("DEV")) else "botlist"
REGEX_BOT_IN_TEXT = r'.*(@[a-zA-Z0-9_]{3,31}).*'
REGEX_BOT_ONLY = r'((@[a-zA-Z0-9_]{3,31}))'
PAGE_SIZE_SUGGESTIONS_LIST = 5
PAGE_SIZE_APPROVALS_LIST = 10
MAX_SEARCH_RESULTS = 25
MAX_BOTS_PER_MESSAGE = 140
BOT_ACCEPTED_IDLE_TIME = 2  # minutes
SUGGESTION_LIMIT = 25

### END OF CONFIGURATION ###

big_range = list(range(512))


# CONSTANTS

class BotStates:
    SEARCHING, \
    SENDING_KEYWORDS, \
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
    *rest = big_range


class DeepLinkingActions:
    FAVORITES = 'favorites'
    SEARCH = 'search'
    RULES = 'rules'
    CONTRIBUTING = 'contributing'
    EXAMPLES = 'examples'


class CallbackActions:
    APPLY_ALL_CHANGES, \
    REFRESH_EDIT_BOT, \
    HELP, \
    CHANGE_SUGGESTION, \
    CHANGE_SUGGESTION_TEXT, \
    NONE_ACTION, \
    COUNT_THANK_YOU, \
    CONTRIBUTING, \
    EXAMPLES, \
    ADD_TO_FAVORITES, \
    SEND_FAVORITES_LIST, \
    TOGGLE_FAVORITES_LAYOUT, \
    REMOVE_FAVORITE, \
    ADD_ANYWAY, \
    ADD_FAVORITE, \
    REMOVE_FAVORITE_MENU, \
    INLINE_QUERY_CATEGORIES, \
    EDIT_BOT_SPAM, \
    ABORT_SETTING_KEYWORDS, \
    REMOVE_KEYWORD, \
    EDIT_BOT_KEYWORDS, \
    NEW_BOTS_SELECTED, \
    DISABLE_NOTIFICATIONS, \
    SET_NOTIFICATIONS, \
    SWITCH_APPROVALS_PAGE, \
    SWITCH_SUGGESTIONS_PAGE, \
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
    APPROVE_REJECT_BOTS, \
    DELETE_CONVERSATION, \
    *rest = big_range


class Layouts:
    _LAYOUTS = {
        'categories': {
            'caption': '📚 Bots per Category',
            'next': 'single'
        },
        'single': {
            'caption': '📜 Single list of Bots',
            'next': 'categories'
        }
    }

    @property
    def choices(self):
        return list(self._LAYOUTS.keys())

    @property
    def default(self):
        return self.choices[0]

    @staticmethod
    def get_caption(layout):
        print(layout)
        return Layouts._LAYOUTS[layout]['caption']

    @staticmethod
    def get_next(layout):
        return Layouts._LAYOUTS[layout]['next']