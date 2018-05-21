import os

import sys
from decouple import config
from datetime import timedelta

DEV = config("DEV", default=False, cast=bool)

### BOT CONFIGURATION ###
BOT_TOKEN = config('BOT_TOKEN', default=None) or (sys.argv[1] if len(sys.argv) > 1 else None)
LOG_DIR = config('LOG_DIR', default=os.path.dirname(os.path.abspath(__file__)))
BOT_THUMBNAIL_DIR = config('BOT_THUMBNAIL_DIR',
                           default=os.path.expanduser(
                               '/home/joscha/data/botlistbot/bot-profile-pictures'))
MODERATORS = [
    62056065,  # JosXa
    918962,  # T3CHNO
    7679610,
    278941742,
    127782573,
    43740047,
    317434635,
    2591224,  # OWL
    473862645  # Lulzx
]
ADMINS = [62056065, 918962]
BOT_CONSIDERED_NEW = 1  # Revision difference
WORKER_COUNT = 5 if DEV else 20
TEST_BOT_NAME = "josxasandboxbot"
LIVE_BOT_NAME = "botlistbot"
SELF_BOT_NAME = TEST_BOT_NAME if DEV else LIVE_BOT_NAME
SELF_BOT_ID = "182355371" if DEV else "265482650"
BOTLIST_NOTIFICATIONS_ID = -1001074366879
BOTLISTCHAT_ID = -1001118582923 if DEV else -1001067163791
BLSF_ID = -1001098339113
SELF_CHANNEL_USERNAME = "botlist_testchannel" if DEV else "botlist"
REGEX_BOT_IN_TEXT = r'.*(@[a-zA-Z0-9_]{3,31}).*'
REGEX_BOT_ONLY = r'(@[a-zA-Z0-9_]{3,31})'
PAGE_SIZE_SUGGESTIONS_LIST = 5
PAGE_SIZE_BOT_APPROVAL = 5
MAX_SEARCH_RESULTS = 25
MAX_BOTS_PER_MESSAGE = 140
BOT_ACCEPTED_IDLE_TIME = 2  # minutes
SUGGESTION_LIMIT = 25
API_URL = "localhost" if DEV else "josxa.jumpingcrab.com"
API_PORT = 6060

### BOTCHECKER
RUN_BOTCHECKER = False
API_ID = 34057
API_HASH = 'a89154bb0cde970cae0848dc7f7a6108'
USERBOT_PHONE = "+79661570814"
USERBOT_SESSION = "/home/joscha/accounts/pyrogram/79661570814"
# TEST_USERBOT_PHONE = "+79684132863"
# TEST_USERBOT_SESSION = "/home/joscha/accounts/pyrogram/79684132863"
BOTCHECKER_CONCURRENT_COUNT = 10
BOTCHECKER_INTERVAL = 3600 * 3
DELETE_CONVERSATION_AFTER_PING = True
NOTIFY_NEW_PROFILE_PICTURE = not DEV
DOWNLOAD_PROFILE_PICTURES = not DEV
DISABLE_BOT_INACTIVITY_DELTA = timedelta(days=15)

OFFLINE_DETERMINERS = ["under maintenance"]
BOTBUILDER_DETERMINERS = ["use /off to pause your subscription", "use /stop to unsubscribe", "manybot", "chatfuelbot"]
BLOCKED_KEYWORDS = ["must", "bot", "online", "offline", "type", "start", "remove"]  # TODO implement

DEBUG_LOG_FILE = "botlistbot.log"

if not os.path.exists(BOT_THUMBNAIL_DIR):
    os.makedirs(BOT_THUMBNAIL_DIR)

### TESTS
BOT_UNDER_TEST = TEST_BOT_NAME if DEV else LIVE_BOT_NAME
TEST_USERBOT_PHONE = "+491728656978"
TEST_USERBOT_SESSION = "/home/joscha/accounts/pyrogram/JosXa"
TEST_GROUP_ID = 1118582923

