import json
import logging
from pprint import pprint
from typing import Callable, Dict

from telegram import Update
from telegram.ext.handler import Handler


class InlineCallbackHandler(Handler):
    def __init__(self,
                 action,
                 callback,
                 serialize: Callable[[Dict], Dict] = None,
                 pass_update_queue=False,
                 pass_job_queue=False,
                 pass_groups=False,
                 pass_groupdict=False,
                 pass_user_data=False,
                 pass_chat_data=False):
        """
        This class maps an action to the appropriate callback as the counterpart to InlineCallbackButton.

        Pass a function ``serialize(callback_data, update)`` returning a dict of values to create objects for the parameters
        you specified in the parameters of ``InlineCallbackButton``.

        Example:
            Assuming you want to create an object `User` in your object-relational-mapper (ORM)

            ```
            def serialize_objects(data, update):
                context = dict()
                context['user'] = User.get_or_create(id=data['id])
                return context
            ```

            You can then pass this function as an argument to the constructor.

            ``InlineCallbackHandler(CallbackActions.CREATE_USER, create_user, serialize=serialize_objects)``

        :param action: The action to use
        :param callback: The corresponding callback handler
        :param serialize: A serialization function with 2 arguments (data, update)
        :param pass_update_queue:
        :param pass_job_queue:
        :param pass_user_data:
        :param pass_chat_data:
        """

        super(InlineCallbackHandler, self).__init__(
            callback,
            pass_update_queue=pass_update_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data,
            pass_chat_data=pass_chat_data)

        if serialize:
            if not hasattr(serialize, '__call__'):
                self.log.error("The `serialization` attribute must be a callable function.")
        self.serialize = serialize
        self.action = action
        self.pass_groups = pass_groups
        self.pass_groupdict = pass_groupdict
        self.log = logging.getLogger(__name__)

    def check_update(self, update):
        if isinstance(update, Update) and update.callback_query:
            if self.action:
                obj = json.loads(str(update.callback_query.data))
                if 'a' in obj:
                    action = obj['a']
                    return action == self.action
                else:
                    self.log.warning("No action in update.")
            else:
                return True

    def handle_update(self, update, dispatcher):
        optional_args = self.collect_optional_args(dispatcher, update)
        obj = json.loads(str(update.callback_query.data))

        # Call the user-defined serialization method
        if self.serialize is not None:
            context = self.serialize(obj)
            optional_args['context'] = context

        return self.callback(dispatcher.bot, update, **optional_args)
