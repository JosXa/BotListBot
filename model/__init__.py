from model.bot import Bot
from model.category import Category
from model.channel import Channel
from model.country import Country
from model.group import Group
from model.user import User
from model.suggestion import Suggestion

if __name__ == "__main__":
    Category.create_table(fail_silently=True)
    Bot.create_table(fail_silently=True)
    Country.create_table(fail_silently=True)
    Channel.create_table(fail_silently=True)
    User.create_table(fail_silently=True)
    Suggestion.create_table(fail_silently=True)
    Group.create_table(fail_silently=True)

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
