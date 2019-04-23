import json
import re

import logging
from pprint import pprint

from future.utils import string_types

from models import Bot
from models import Category
from telegram import Update
from telegram.utils.deprecate import deprecate
from telegram.ext.handler import Handler


class JSONCallbackHandler(Handler):

    def __init__(self,
                 action,
                 callback,
                 mapping=None,
                 pass_update_queue=False,
                 pass_job_queue=False,
                 pass_groups=False,
                 pass_groupdict=False,
                 pass_user_data=False,
                 pass_chat_data=False):
        super(JSONCallbackHandler, self).__init__(
            callback,
            pass_update_queue=pass_update_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data,
            pass_chat_data=pass_chat_data)

        self.action = action
        self.mapping = mapping
        self.pass_groups = pass_groups
        self.pass_groupdict = pass_groupdict
        self.logger = logging.getLogger(__name__)

    def check_update(self, update):
        if isinstance(update, Update) and update.callback_query:
            if self.action:
                obj = json.loads(str(update.callback_query.data))
                if 'a' in obj:
                    action = obj['a']
                    return action == self.action
                else:
                    self.logger.error("No action in update.")
            else:
                return True

    def handle_update(self, update, dispatcher):
        optional_args = self.collect_optional_args(dispatcher, update)
        obj = json.loads(str(update.callback_query.data))

        # Add the ORM-objects to callback arguments
        if self.mapping is not None:
            for key, value in self.mapping.items():
                db_wrapper = value[0]
                method_name = value[1]
                if key in obj:
                    try:
                        model_obj = db_wrapper.get(db_wrapper.id == obj[key])
                        optional_args[method_name] = model_obj
                    except db_wrapper.DoesNotExist:
                        self.logger.error("Field {} with id {} was not found in database.".format(key, obj[key]))
                else:
                    self.logger.error("Expected field {} was not supplied.".format(key))

        return self.callback(dispatcher.bot, update, **optional_args)
