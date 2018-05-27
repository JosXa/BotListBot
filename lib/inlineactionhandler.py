import json
import logging
from pprint import pprint
from typing import Callable, Dict

from telegram import Update
from telegram.ext.handler import Handler


class InlineActionHandler(Handler):
    def __init__(self,
                 action: int,
                 callback: Callable,
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

        super(InlineActionHandler, self).__init__(
            callback,
            pass_update_queue=pass_update_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data,
            pass_chat_data=pass_chat_data)

        self.action = action
        self.pass_groups = pass_groups
        self.pass_groupdict = pass_groupdict
        self.log = logging.getLogger(__name__)

    def check_update(self, update):
        if isinstance(update, Update) and update.callback_query:
            obj = update.callback_manager.lookup_callback(update.callback_query.data)
            if obj is None:
                return False
            return obj['action'] == self.action

    def handle_update(self, update, dispatcher):
        optional_args = self.collect_optional_args(dispatcher, update)
        obj = update.callback_manager.lookup_callback(update.callback_query.data)

        data = obj['data']
        update.callback_data = data

        return self.callback(dispatcher.bot, update, **optional_args)
