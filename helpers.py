import logging
from pprint import pprint

from const import SELF_CHANNEL_USERNAME

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def validate_username(username: str):
    if len(username) < 3:
        return False
    if username[0] != '@':
        username = '@' + username
    return username


def get_commands():
    commands = ""
    try:
        with open('files/commands.txt', 'rb') as file:
            for command in file.readlines():
                commands += '/' + command.decode("utf-8")
        return commands
    except FileNotFoundError:
        log.error("File could not be opened.")


def get_channel():
    from model import Channel
    try:
        return Channel.get(Channel.username == SELF_CHANNEL_USERNAME)
    except Channel.DoesNotExist:
        return False


def botlist_url_for_category(category):
    return 'http://t.me/{}/{}'.format(get_channel().username, category.current_message_id)


def format_keyword(kw):
    kw = kw[1:] if kw[0] == '#' else kw
    kw = kw.replace(' ', '_')
    kw = kw.replace('-', '_')
    kw = kw.lower()
    return kw
