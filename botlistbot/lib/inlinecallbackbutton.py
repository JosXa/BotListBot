import json
from telegram import InlineKeyboardButton

# The dictionary key that will be used to encode callback actions in InlineCallbackButtons
ACTION_DICT_KEY = 'a'


class InlineCallbackButton(InlineKeyboardButton):
    def __init__(self, text, callback_action=None, params=None, **kwargs):
        if not isinstance(callback_action, int):
            raise AttributeError('Parameter callback_action must be an integer. '
                                 'Define constants to reference the actions.')
        if params and ACTION_DICT_KEY in params:
            raise AttributeError('Key "{}" can not be used in `params` dict.'.format(ACTION_DICT_KEY))

        # format callback action and parameters to uglified json-string
        json_callback = self._callback_for_action(callback_action, params)

        super(InlineCallbackButton, self).__init__(
            text,
            callback_data=json_callback,
        )

        self.text = text
        self.callback_data = json_callback

    @staticmethod
    def _callback_for_action(action, params=None):
        """
        Generate the merged representation of a callback action and its parameters
        :param action: The action to be used
        :param params: Arbitrary Parameters
        :return: A dict containing callback data
        """
        callback_data = {'a': action}
        if params:
            for key, value in params.items():
                callback_data[key] = value

        # dump dict as uglified json
        dumped = json.dumps(callback_data, separators=(',', ':'))
        if len(dumped) > 64:
            raise ValueError('Your callback_data is getting too long. Telegram allows a maximum of 64 bytes, '
                             'try to pick shorter dictionary keys.')
        return dumped

if __name__ == '__main__':
    btn = InlineCallbackButton('abc', 1, {'id': 'abc'})