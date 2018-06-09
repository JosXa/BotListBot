from models import Bot
from models import User

if __name__ == '__main__':
    all_bots = Bot.select()
    for bot in all_bots:
        if bot.spam is None:
            bot.spam = False
        if bot.official is None:
            bot.official = False
        if bot.inlinequeries is None:
            bot.inlinequeries = False
        if bot.offline is None:
            bot.offline = False
        bot.save()

    all_users = User.select()
    for user in all_users:
        if user.favorites_layout is None:
            user.favorites_layout = 'categories'
        user.save()

