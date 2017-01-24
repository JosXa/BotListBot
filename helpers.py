def validate_username(username: str):
    if len(username) == 0:
        return False
    if username[0] != '@':
        username = '@' + username
    return username

