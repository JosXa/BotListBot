import logging

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

