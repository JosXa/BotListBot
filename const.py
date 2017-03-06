import os
### START OF CONFIGURATION ###

# PREFERENCES

ADMINS = [62056065, 918962]
BOT_CONSIDERED_NEW = 15  # days
SELF_BOT_NAME = "bot_list_bot"
SELF_BOT_ID = "182355371" if os.environ.get("DEV") == "True" else "265482650"
SELF_CHANNEL_USERNAME = "botlist"
REGEX_BOT_IN_TEXT = r'.*(@[a-zA-Z]+[a-zA-Z0-9_\-]{3,}).*'
REGEX_BOT_ONLY = r'(@[a-zA-Z]+[a-zA-Z0-9_\-]{3,})'
PAGE_SIZE_SUGGESTIONS_LIST = 10
PAGE_SIZE_APPROVALS_LIST = 10

# MESSAGES
PROMOTION_MESSAGE = "*Join* @BotList*!*\n*Share your bots in* @BotListChat"
HELP_MESSAGE_ENGLISH = """*ɢʀᴇᴇᴛɪɴɢs ʜᴜᴍᴀɴᴏɪᴅs* 🤖

I'm the bot in charge of maintaining the @BotList channel, the *most reliable and unbiased bot catalog* out there. I was built to simplify navigation and to automate the process of submitting, reviewing and publishing bots by the @BotListChat community.

▫️ Add me to your groups and subscribe to BotList updates.
▫️ Send individual @BotList categories to your friends via inline search (i.e. type `@bot_list_bot music` in any chat).
▫️ Join the @BotListChat community and /contribute to the BotList: `#new @newbot🔎 - description`

First steps: Start off by using the /category command and use the available buttons from there on.

One step closer to world domination... 🤖"""
HELP_MESSAGE_SPANISH = """*ɢʀᴇᴇᴛɪɴɢs ʜᴜᴍᴀɴᴏɪᴅs* 🤖

Soy el bot encargado de mantener el canal @BotList y proporcionar a los usuarios de Telegram como tú el *catálogo de bot más fiable e imparcial* de una _manera interactiva_.

▫️ Agregame a tus grupos y recibe una notificación cuando se actualice el @BotList.
▫️ Envíeme acategorías individuales del @BotList a tus amigos a través de búsqueda en línea (p.e: escribe @bot_list_bot música en cualquier chat).
▫️ Únete a la comunidad @BotListChat y contribuye al BotList: #new @ nuevobot🔎 - descripción

Primeros pasos: Empieza con el comando /category y utiliza los botones disponibles en pantalla desde ahí.

Un paso más cerca de la dominación mundial... 🤖
"""
CONTRIBUTING_MESSAGE = """You can use the following `#tag`s with a bot `@username` to contribute to the BotList:

• #new — Submit a fresh bot. Use 🔎 if it supports inline queries and flag emojis to denote the language. Everything after the `-` character can be your description of the bot (see /examples).
• #offline — Mark a bot as offline.

There are also the corresponding /new and /offline commands.

The moderators will approve your submission as soon as possible.
"""
EXAMPLES_MESSAGE = """*Examples for contributing to the BotList:*

• "Wow! I found this nice #new bot: @coolbot 🔎🇮🇹 - Cools your drinks in the fridge."
• /new @coolbot 🔎🇮🇹 - Cools your drinks in the fridge.

• "Oh no... guys?! @unresponsive\_bot is #offline 😞"
• /offline @unresponsive\_bot
"""
REJECTION_PRIVATE_MESSAGE = """Sorry, but your bot submission {} was rejected.

It does not suffice the standards we impose for inclusion in the @BotList for one of the following reasons:

▫️A better bot with the same functionality is already in the @BotList.
▫️The user interface is bad in terms of usability and/or simplicity.
▫️Contains ads or adult content
▫️English language not supported per default

For further information, please ask in the @BotListChat."""
ACCEPTANCE_PRIVATE_MESSAGE = """Congratulations, your bot submission {} has been accepted for the @BotList. You can already see it by using the /category command, and it is going to be in the @BotList in the next two weeks."""
BOTLIST_UPDATE_NOTIFICATION = """⚠️@BotList *update!*
There are {n_bots} new bots:

{new_bots}

Share your bots in @BotListChat"""

### END OF CONFIGURATION ###

from helpers import get_commands

COMMANDS = get_commands()


def get_channel():
    from model import Channel
    try:
        return Channel.get(Channel.username == SELF_CHANNEL_USERNAME)
    except Channel.DoesNotExist:
        return False


big_range = list(range(512))


# CONSTANTS

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
