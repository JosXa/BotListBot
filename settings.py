import os

from decouple import config

if os.environ.get("DEV"):
    print('Debug/Development mode')
    DEV = True
else:
    DEV = False

### BOT CONFIGURATION ###
LOG_DIR = config('LOG_DIR', default=os.path.dirname(os.path.abspath(__file__)))
BOT_THUMBNAIL_DIR = config('BOT_THUMBNAIL_DIR',
                           default=os.path.expanduser(
                               '/home/joscha/data/botlistbot/bot-profile-pictures'))
MODERATORS = [62056065,  # JosXa
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
SELF_BOT_NAME = "josxasandboxbot" if DEV else "botlistbot"
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

USERBOT_SESSION = "/home/joscha/accounts/79671952892"
RUN_BOTCHECKER = True

DEBUG_LOG_FILE = "botlistbot.log"

if not os.path.exists(BOT_THUMBNAIL_DIR):
    os.makedirs(BOT_THUMBNAIL_DIR)
