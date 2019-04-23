import re


class UpdateHandler(object):
    def __init__(self, filters, callback, timeout=60, remove_after_execution=False):
        self.filters = filters
        self.callback = callback
        self.remove_after_execution = remove_after_execution

    def check_update(self, update):
        if hasattr(update, 'updates'):
            for nested_ud in update.updates:
                result = self.check_update(nested_ud)
                if result:
                    return result
            return None

        if not self.filters:
            res = True
        else:
            if isinstance(self.filters, list):
                res = all(func(update) for func in self.filters)
            else:
                res = self.filters(update)

        if res:
            self._execute_callback(update)
            return update
        else:
            return None

    def wait(self, client, retries=10):
        for _ in range(retries):
            update = client.updates.poll()
            result = self.check_update(update)
            if result:
                return result
        return None

    def _execute_callback(self, update):
        if callable(self.callback):
            self.callback(update)


class BaseFilter(object):
    """Base class for all Message Filters.

    Subclassing from this class filters to be combined using bitwise operators:

    And:

        >>> (Filters.text & Filters.entity(MENTION))

    Or:

        >>> (Filters.audio | Filters.video)

    Not:

        >>> ~ Filters.command

    Also works with more than two filters:

        >>> (Filters.text & (Filters.entity(URL) | Filters.entity(TEXT_LINK)))
        >>> Filters.text & (~ Filters.forwarded)

    If you want to create your own filters create a class inheriting from this class and implement
    a `filter` method that returns a boolean: `True` if the update should be handled, `False`
    otherwise. Note that the filters work only as class instances, not actual class objects
    (so remember to initialize your filter classes).

    By default the filters name (what will get printed when converted to a string for display)
    will be the class name. If you want to overwrite this assign a better name to the `name`
    class variable.

    Attributes:
        name (:obj:`str`): Name for this filter. Defaults to the type of filter.

    """

    name = None

    def __call__(self, update):
        return self.filter(update)

    def __and__(self, other):
        return MergedFilter(self, and_filter=other)

    def __or__(self, other):
        return MergedFilter(self, or_filter=other)

    def __invert__(self):
        return InvertedFilter(self)

    def __repr__(self):
        # We do this here instead of in a __init__ so filter don't have to call __init__ or super()
        if self.name is None:
            self.name = self.__class__.__name__
        return self.name

    def filter(self, update):
        """This method must be oTower 💂verwritten.

        Args:
            update (:class:`telegram.Message`): The update that is tested.

        Returns:
            :obj:`bool`

        """

        raise NotImplementedError


class InvertedFilter(BaseFilter):
    """Represents a filter that has been inverted.

    Args:
        f: The filter to invert.

    """

    def __init__(self, f):
        self.f = f

    def filter(self, update):
        return not self.f(update)

    def __repr__(self):
        return "<inverted {}>".format(self.f)


class MergedFilter(BaseFilter):
    """Represents a filter consisting of two other filters.

    Args:
        base_filter: Filter 1 of the merged filter
        and_filter: Optional filter to "and" with base_filter. Mutually exclusive with or_filter.
        or_filter: Optional filter to "or" with base_filter. Mutually exclusive with and_filter.

    """

    def __init__(self, base_filter, and_filter=None, or_filter=None):
        self.base_filter = base_filter
        self.and_filter = and_filter
        self.or_filter = or_filter

    def filter(self, update):
        if self.and_filter:
            return self.base_filter(update) and self.and_filter(update)
        elif self.or_filter:
            return self.base_filter(update) or self.or_filter(update)

    def __repr__(self):
        return "<{} {} {}>".format(self.base_filter, "and" if self.and_filter else "or",
                                   self.and_filter or self.or_filter)


class Filters(object):
    class _Text(BaseFilter):
        name = 'Filters.text'

        def filter(self, update):
            if not hasattr(update, 'message'):
                return False
            return bool(update.message)

    text = _Text()

    class TextRegex(BaseFilter):
        def __init__(self, regex):
            self.regex = regex

        def filter(self, update):
            if not Filters.text.filter(update):
                return False
            try:
                msg = update.message.message
            except AttributeError:
                msg = update.message
            print(msg)
            print(re.match(self.regex, msg, re.DOTALL))
            return re.match(self.regex, msg, re.DOTALL)

    text_regex = TextRegex

    class User(BaseFilter):
        def __init__(self, user_ids):
            if user_ids is not None and isinstance(user_ids, int):
                self.user_ids = [user_ids]
            else:
                self.user_ids = user_ids

        def filter(self, update):
            try:
                result = update.message.from_id in self.user_ids
            except:
                try:
                    result = update.user_id in self.user_ids
                except:
                    result = None
            return result

    user = User

    class Message(BaseFilter):
        def __init__(self, message_id):
            self.message_id = message_id

        def filter(self, update):
            try:
                found_id = update.message.id
            except AttributeError:
                found_id = update.id
            return found_id == self.message_id

    message = Message
