import random

import captions
import mdformat

PROMOTION_MESSAGE = "*ᴊᴏɪɴ ᴛʜᴇ* @BotList 💙\n*sʜᴀʀᴇ* ʏᴏᴜʀ ʙᴏᴛs ɪɴ @BotListChat"
HELP_MESSAGE_ENGLISH = """*ɢʀᴇᴇᴛɪɴɢs ʜᴜᴍᴀɴᴏɪᴅs* 🤖

I'm the bot in charge of maintaining the @BotList channel, the *most reliable and unbiased bot catalog* out there. I was built to simplify navigation and to automate the process of submitting, reviewing and publishing bots by the @BotListChat community.

▫️ Add me to your groups and subscribe to BotList updates.
▫️ Send individual @BotList categories to your friends via inline search (i.e. type `@botlistbot music` in any chat).
▫️ Join the @BotListChat community and contribute to the BotList: `#new @newbot🔎 - description`

First steps: Start off by using the /category command and use the available buttons from there on.

ᴏɴᴇ sᴛᴇᴘ ᴄʟᴏsᴇʀ ᴛᴏ ᴡᴏʀʟᴅ ᴅᴏᴍɪɴᴀᴛɪᴏɴ 🤖"""
# HELP_MESSAGE_SPANISH = """*ɢʀᴇᴇᴛɪɴɢs ʜᴜᴍᴀɴᴏɪᴅs* 🤖
#
# Soy el bot encargado de mantener el canal @BotList y proporcionar a los usuarios de Telegram como tú el *catálogo de bot más fiable e imparcial* de una _manera interactiva_.
#
# ▫️ Agregame a tus grupos y recibe una notificación cuando se actualice el @BotList.
# ▫️ Envíeme acategorías individuales del @BotList a tus amigos a través de búsqueda en línea (p.e: escribe @botlistbot música en cualquier chat).
# ▫️ Únete a la comunidad @BotListChat y contribuye al BotList: #new @ nuevobot🔎 - descripción
#
# Primeros pasos: Empieza con el comando /category y utiliza los botones disponibles en pantalla desde ahí.
#
# Un paso más cerca de la dominación mundial... 🤖
# """
CONTRIBUTING = """You can use the following `#tags` with a bot `@username` to contribute to the BotList:

• #new — Submit a fresh bot. Use 🔎 if it supports inline queries and flag emojis to denote the language. Everything after the `-` character can be your description of the bot.
• #offline — Mark a bot as offline.
• #spam — Tell us that a bot spams too much.

There are also the corresponding /new, /offline and /spam commands.
The moderators will approve your submission as soon as possible.

*Next step*: Have a look at the /examples!
"""
EXAMPLES = """*Examples for contributing to the BotList:*

• "Wow! I found this nice #new bot: @coolbot 🔎🇮🇹 - Cools your drinks in the fridge."
• /new @coolbot 🔎🇮🇹 - Cools your drinks in the fridge.

• "Oh no... guys?! @unresponsive\_bot is #offline 😞"
• /offline @unresponsive\_bot

• "Aaaargh, @spambot's #spam is too crazy!"
• /spam @spambot
"""
REJECTION_PRIVATE_MESSAGE = """Sorry, but your bot submission {} was rejected.

It does not suffice the standards we impose for inclusion in the @BotList for one of the following reasons:

▫️A better bot with the same functionality is already in the @BotList.
▫️The user interface is bad in terms of usability and/or simplicity.
▫The bot is still in an early development stage
▫️Contains ads or exclusively adult content
▫️English language not supported per default (exceptions are possible)
▫NO MANYBOTS!!! 👺

For further information, please ask in the @BotListChat."""
ACCEPTANCE_PRIVATE_MESSAGE = """Congratulations, your bot submission {} has been accepted for the @BotList. You can already see it by using the /category command, and it is going to be in the @BotList in the next two weeks."""
BOTLIST_UPDATE_NOTIFICATION = """⚠️@BotList *update!*
There are {n_bots} new bots:

{new_bots}

Share your bots in @BotListChat"""
SEARCH_MESSAGE = mdformat.action_hint("What would you like to search for?")
SEARCH_RESULTS = """I found *{num_results} bot{plural}* in the @BotList for *{query}*:\n
{bots}
"""
KEYWORD_BEST_PRACTICES = """The following rules for keywords apply:
▫️Keep the keywords as short as possible
▫️Use singular where applicable (#̶v̶i̶d̶e̶o̶s̶ video)
▫️Try to tag every supported platform (e.g. #vimeo, #youtube, #twitch, ...)
▫Try to tag every supported action (#search, #upload, #download, ...)
▫Try to tag every supported format (#mp3, #webm, #mp4, ...)
▫Keep it specific (only tag #share if the bot has a dedicated 'Share' button)
▫Tag bots made with _bot creators_ (e.g. #manybot)
▫Use #related if the bot is not standalone, but needs another application to work properly, e.g. an Android App
▫Always think in the perspective of a user in need of a bot. What query might he be putting in the search field?
"""
NEW_BOTS_INLINEQUERY = "New Bots"
SELECT_CATEGORY = "Please select a category"
SHOW_IN_CATEGORY = "Show category"
REROUTE_PRIVATE_CHAT = mdformat.action_hint("Please use this command in a private chat or make use of inlinequeries.")
BOTLISTCHAT_RULES = """*Here are the rules for @BotListChat:*\n\nShare your bots, comment, test and have fun😜👍

Rules: Speak in English, Don't spam/advertise channels or groups that aren't bot related, respect other members, use common sense. 🤖

⭐️⭐️⭐️⭐️⭐️
[Give @BotList a rating](https://goo.gl/rtSs5B)"""
BAN_MESSAGE = mdformat.action_hint("Please send me the username to ban and remove all bot submissions")
UNBAN_MESSAGE = mdformat.action_hint("Please send me the username of the user to revoke ban state for")
FAVORITES_HEADLINE = "*{}* 🔽\n_― from_ @BotList".format(captions.FAVORITES)
ADD_FAVORITE = mdformat.action_hint("Please send me the @username of a bot to add to your favorites")


def random_call_to_action():
    CHOICES = ["Check out", "You might like", "What about", "You should try", "Have a look at"]
    return random.choice(CHOICES)
