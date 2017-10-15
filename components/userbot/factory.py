import os
import random
from pprint import pprint

import settings
from telethon import TelegramClient


class NoSessionAvailableError(Exception):
    pass


class SetupRequiredError(Exception):
    pass


class UserbotFactory:
    def __init__(self, sessions_dir, api_id, api_hash):
        self.sessions_dir = sessions_dir
        self.api_id = api_id
        self.api_hash = api_hash

        self._available_sessions = []
        self._used_sessions = []

        self._evaluate_sessions()

    def _evaluate_sessions(self):
        if not os.path.exists(self.sessions_dir):
            raise ValueError("The sessions directory at {} does "
                             "not exist.".format(self.sessions_dir))
        files = os.listdir(self.sessions_dir)
        sessions = [os.path.splitext(f)[0] for f in files if os.path.splitext(f)[1] == '.session']
        self._available_sessions = [s for s in sessions if s not in self._used_sessions]
        return self._available_sessions

    def create_client(self, *args, **kwargs):
        self._evaluate_sessions()
        if len(self._available_sessions) == 0:
            raise NoSessionAvailableError("No more sessions available.")

        session = self._get_next_session()
        session_file = os.path.join(self.sessions_dir, session)
        client = TelegramClient(
            session_file,
            self.api_id,
            self.api_hash,
            *args,
            **kwargs
        )

        self._available_sessions.remove(session)
        self._used_sessions.append(session)

        client.connect()
        if not client.is_user_authorized():
            raise SetupRequiredError("The client at {} is not authorized.".format(session_file))

        return client

    def release_client(self, client: TelegramClient):
        self._used_sessions.remove(client.session)
        self._evaluate_sessions()

    @property
    def available_sessions(self):
        return self._available_sessions

    @property
    def sessions_in_use(self):
        return self._used_sessions

    def _get_next_session(self):
        return self._available_sessions[0]

if __name__ == '__main__':
    api_id = 34057
    api_hash = 'a89154bb0cde970cae0848dc7f7a6108'

    factory = UserbotFactory(
        settings.USERBOT_ACCOUNTS_DIR,
        api_id,
        api_hash
    )
    pprint(factory._evaluate_sessions())

