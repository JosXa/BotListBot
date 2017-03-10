import util

PROMOTION_MESSAGE = "*Join* @BotList\n*Share your bots in* @BotListChat"
HELP_MESSAGE_ENGLISH = """*ɢʀᴇᴇᴛɪɴɢs ʜᴜᴍᴀɴᴏɪᴅs* 🤖

I'm the bot in charge of maintaining the @BotList channel, the *most reliable and unbiased bot catalog* out there. I was built to simplify navigation and to automate the process of submitting, reviewing and publishing bots by the @BotListChat community.

▫️ Add me to your groups and subscribe to BotList updates.
▫️ Send individual @BotList categories to your friends via inline search (i.e. type `@bot_list_bot music` in any chat).
▫️ Join the @BotListChat community and /contribute to the BotList: `#new @newbot🔎 - description`

First steps: Start off by using the /category command and use the available buttons from there on.

ᴏɴᴇ sᴛᴇᴘ ᴄʟᴏsᴇʀ ᴛᴏ ᴡᴏʀʟᴅ ᴅᴏᴍɪɴᴀᴛɪᴏɴ 🤖"""
HELP_MESSAGE_SPANISH = """*ɢʀᴇᴇᴛɪɴɢs ʜᴜᴍᴀɴᴏɪᴅs* 🤖

Soy el bot encargado de mantener el canal @BotList y proporcionar a los usuarios de Telegram como tú el *catálogo de bot más fiable e imparcial* de una _manera interactiva_.

▫️ Agregame a tus grupos y recibe una notificación cuando se actualice el @BotList.
▫️ Envíeme acategorías individuales del @BotList a tus amigos a través de búsqueda en línea (p.e: escribe @bot_list_bot música en cualquier chat).
▫️ Únete a la comunidad @BotListChat y contribuye al BotList: #new @ nuevobot🔎 - descripción

Primeros pasos: Empieza con el comando /category y utiliza los botones disponibles en pantalla desde ahí.

Un paso más cerca de la dominación mundial... 🤖
Developed and maintained by @Josxa."""
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
▫NO MANYBOTS!!! 👺

For further information, please ask in the @BotListChat."""
ACCEPTANCE_PRIVATE_MESSAGE = """Congratulations, your bot submission {} has been accepted for the @BotList. You can already see it by using the /category command, and it is going to be in the @BotList in the next two weeks."""
BOTLIST_UPDATE_NOTIFICATION = """⚠️@BotList *update!*
There are {n_bots} new bots:

{new_bots}

Share your bots in @BotListChat"""
SEARCH_MESSAGE = util.action_hint("What would you like to search for?")
SEARCH_RESULTS = """I found {num_results} bot{plural} in the @BotList matching your request:
{bots}
"""
KEYWORD_BEST_PRACTICES = """The following rules for keywords apply:
▫️Keep the keywords as short as possible
▫️Use singular where applicable (#̶v̶i̶d̶e̶o̶s̶ video)
▫️Try to tag every supported platform (e.g. #vimeo, #youtube, #twitch, ...)
▫Try to tag every supported action (#search, #upload, #download, ...)
▫Keep it specific (only tag #share if the bot has a dedicated 'Share' button)
▫Tag bots made with _bot creators_ (e.g. #manybot)
▫Use #related if the bot is not standalone, but needs another application to work properly, e.g. an Android App
"""
