import logging

import requests

from model import Bot

log = logging.getLogger('requests').setLevel(logging.WARNING)


class PWRTelegram:
    BASE_URL = 'https://api.pwrtelegram.xyz/'

    def __init__(self, access_token=None):
        self.access_token = access_token

        self.set_method_url()

    def set_method_url(self):
        self.METHOD_URL = '{}user{}'.format(self.BASE_URL, self.access_token)

    def login(self, phone_number):
        self._temp_token = requests.get('{}phonelogin?phone={}'.format(
            self.BASE_URL, phone_number
        ))
        pprint(self._temp_token.json())
        return self._temp_token

    def complete_phone_login(self, login_code):
        if self._temp_token is None:
            raise AttributeError('Run login first.')
        self.access_token = requests.get(
            '{}/user{}/completephonelogin?code={}'.format(
                self.BASE_URL,
                self._temp_token,
                login_code)).json()['result']
        self.set_method_url()

    def send_message(self, chat_id, text):
        payload = {'peer': chat_id,
                   'message': text}
        result = requests.get('{}/messages.sendMessage'.format(self.METHOD_URL), params=payload).json()
        return result['result'] if result['ok'] else None

    def await_response(self, message, text=None, file=None):
        """
        Use regular expressions to match response text or file name
        :param text:
        :param file:
        :return:
        """
        data = {'allowed_updates': ['message'],
                'offset': -2}
        peer_id = message['users'][-1]['id']
        mid = message['updates'][0]['id']

        def bar():
            result = requests.get('{}/getUpdates'.format(self.METHOD_URL), params=data).json()['result']
            for r in result:
                try:
                    update = r['update']
                    if update['message']['from_id'] == peer_id:
                        if update['message']['id'] == mid + 1:
                            return update
                except (KeyError, AttributeError):
                    continue

        return timeout(bar, timeout_duration=10, default=False)


def timeout(func, args=(), kwargs={}, timeout_duration=1, default=None):
    '''
    This function will spwan a thread and run the given function using the args, kwargs and
    return the given default value if the timeout_duration is exceeded
    '''
    import threading
    class InterruptableThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.result = default

        def run(self):
            try:
                self.result = func(*args, **kwargs)
            except:
                self.result = default

    it = InterruptableThread()
    it.start()
    it.join(timeout_duration)
    if it.isAlive():
        return default
    else:
        return it.result


if __name__ == '__main__':
    pwt = PWRTelegram()
    pwt.login('+491728656978')
    login_code = input('Login code: ')
    pwt.complete_phone_login(login_code)
    print(pwt.access_token)
    print(pwt.METHOD_URL)
    msg = pwt.send_message(62056065, 'Hello World!')

    pwt = PWRTelegram('your_api_key')
    b = Bot.get(Bot.username == '@bold')
    print('Sending /start to {}...'.format(b.username))
    msg = pwt.send_message(b.username, '/start')
    print('Awaiting response...')
    if msg:
        resp = pwt.await_response(msg)
        if resp:
            print('{} answered.'.format(b.username))
        else:
            print('{} is offline.'.format(b.username))
    else:
        print('Could not contact {}.'.format(b.username))
