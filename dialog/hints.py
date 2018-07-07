import captions
import settings
from dialog import messages

HINTS = {
    '#inline': {
        'message': "Consider using me in inline-mode 😇\n`@BotListBot {query}`",
        'default': "Your search terms",
        'buttons': [{
            'text': '🔎 Try it out',
            'switch_inline_query': '{query}'
        }],
        'help': 'Give a query that will be used for a `switch_to_inline`-button'
    },
    '#rules': {
        'message': messages.BOTLISTCHAT_RULES,
        'help': 'Send the rules of @BotListChat'
    },
    '#manybot': {
        'message': "We (the @BotList moderators) set a *high standard for bots on the* @BotList. "
                   "Bots built with bot builders like @Manybot or @Chatfuelbot certainly have "
                   "their place, but usually *lack the quality* we impose for inclusion to the "
                   "list. We prefer when bot makers actually take their time and effort to "
                   "program bots without using a sandbox kindergarten tool as the ones mentioned "
                   "above. Don't get us wrong, there are great tools out there built with these "
                   "bot builders, and if you feel like the BotList is lacking some feature that "
                   "this bot brings, feel free to submit it. But as a rule of thumb, Manybots are "
                   "*generally too spammy, not very useful and not worth the effort*. "
                   "Thank you 🙏🏻",
        'help': 'Send our Manybot policy'
    },
    '#private': {
        'message': "Please don't spam the group with {query}, and go to a private "
                   "chat with me instead. Thanks a lot, the other members will appreciate it 😊",
        'default': 'searches or commands',
        'buttons': [{
            'text': captions.SWITCH_PRIVATE,
            'url': "https://t.me/{}".format(settings.SELF_BOT_NAME)
        }],
        'help': 'Tell a member to stop spamming and switch to a private chat'
    },
    '#userbot': {
        'message': "Refer to [this article](http://telegra.ph/How-a-"
                   "Userbot-superacharges-your-Telegram-Bot-07-09) to learn more about *Userbots*.",
        'help': "@JosXa's article about Userbots"
    }
}
