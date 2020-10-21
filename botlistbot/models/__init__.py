from botlistbot.models.bot import Bot
from botlistbot.models.category import Category
from botlistbot.models.channel import Channel
from botlistbot.models.apiaccess import APIAccess
from botlistbot.models.country import Country
from botlistbot.models.group import Group
from botlistbot.models.keywordmodel import Keyword
from botlistbot.models.notifications import Notifications
from botlistbot.models.user import User
from botlistbot.models.suggestion import Suggestion
from botlistbot.models.favorite import Favorite
from botlistbot.models.message import Message
from botlistbot.models.statistic import Statistic
from botlistbot.models.statistic import track_activity
from botlistbot.models.revision import Revision


if __name__ == "__main__":
    Category.create_table(fail_silently=True)
    Bot.create_table(fail_silently=True)
    Country.create_table(fail_silently=True)
    Channel.create_table(fail_silently=True)
    User.create_table(fail_silently=True)
    Suggestion.create_table(fail_silently=True)
    Group.create_table(fail_silently=True)
    Notifications.create_table(fail_silently=True)
    Keyword.create_table(fail_silently=True)
    Favorite.create_table(fail_silently=True)
    APIAccess.create_table(fail_silently=True)

    APIAccess.insert({
        'user': User.get(User.username == 'Josxa'),
        'token': '5f25218eb541b992b926c2e831d9e611853158e9bd69af56a760b717922029a9',
    }).execute()

    # Country.insert_many([
    #     {'name': 'Italy', 'emoji': '🇮🇹'},
    #     {'name': 'Brazil', 'emoji': '🇧🇷'},
    #     {'name': 'Great Britain', 'emoji': '🇬🇧'},
    #     {'name': 'Spin', 'emoji': '🇪🇸'},
    #     {'name': 'Iran', 'emoji': '🇮🇷'},
    #     {'name': 'Indonesia', 'emoji': '🇮🇩'},
    #     {'name': 'Russia', 'emoji': '🇷🇺'},
    #     {'name': 'India', 'emoji': '🇮🇳'},
    #     {'name': 'Argentina', 'emoji': '🇦🇷'},
    # ]).execute()

    # Category.insert_many([
    #     {'emojis': ':joy::performing_arts:', 'name': 'Humor', 'extra': None},
    #     {'emojis': ':raising_hand::wave:', 'name': '🏼Promoting', 'extra': 'Divulgacion'},
    #     {'emojis': ':cyclone:', 'name': 'Miscellaneous', 'extra': 'Miscelaneo'},
    #     {'emojis': ':busts_in_silhouette::loudspeaker:', 'name': 'Social', 'extra': None},
    #     {'emojis': ':credit_card:', 'name': 'Shopping', 'extra': 'Compras'}
    # ]).execute()
    #
    # Bot.insert_many([
    #     {'category': Category.get(name='Humor'),
    #      'name': 'Cuánta Razón',
    #      'username': '@cuanta_razon_bot',
    #      'date_added': datetime.date.today(),
    #      'language': Country.get(name='England'),
    #      },
    #     {'category': Category.get(name='Humor'),
    #      'name': 'Dogefy',
    #      'username': '@dogefy_bot',
    #      'date_added': datetime.date.today(),
    #      'language': Country.get(name='England'),
    #      },
    #     {'category': Category.get(name='Humor'),
    #      'name': 'devRant Bot',
    #      'username': '@devrantbot',
    #      'date_added': datetime.date.today(),
    #      'language': Country.get(name='England'),
    #      },
    #     {'category': Category.get(name='Shopping'),
    #      'name': 'Alternative Bot Store',
    #      'username': '@AlternativeStoreBot',
    #      'date_added': datetime.date.today(),
    #      'language': Country.get(name='England'),
    #      },
    #     {'category': Category.get(name='Shopping'),
    #      'name': '@canalestelegrambot',
    #      'username': '@canalesbot',
    #      'date_added': datetime.date.today(),
    #      'language': Country.get(name='England'),
    #      },
    # ]).execute()
