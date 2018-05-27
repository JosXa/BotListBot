import pytest

import settings
from tgintegration import BotIntegrationClient


@pytest.fixture(scope="session")
def client():
    # setup
    print('Initializing integration test client')

    c = BotIntegrationClient(
        bot_under_test=settings.BOT_UNDER_TEST,
        max_wait_response=8,
        min_wait_consecutive=1.5,
        global_action_delay=1.5,
        session_name=settings.TEST_USERBOT_SESSION,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        phone_number=settings.TEST_USERBOT_PHONE
    )
    print("Starting client...")
    c.start()
    if c.peer_id in settings.MODERATORS:
        print("Restarting bot...")
        c.send_command_await("r", num_expected=2)  # restart bot
    # c.clear_chat()
    yield c
    # teardown
    c.stop()
