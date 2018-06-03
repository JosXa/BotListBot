from model import User, Bot


def lookup_entity(query, exact=True):
    """
    Searches for a Bot or User contained in the query
    """
    if exact:
        try:
            return Bot.by_username(query, include_disabled=True)
        except Bot.DoesNotExist:
            pass
        try:
            return Bot.get(chat_id=query)
        except Bot.DoesNotExist:
            pass
        try:
            return User.by_username(query)
        except User.DoesNotExist:
            pass
        try:
            return User.get(chat_id=query)
        except User.DoesNotExist:
            pass
        return None
