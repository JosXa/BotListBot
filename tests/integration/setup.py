from tgintegration.botintegrationclient import BotIntegrationClient

import settings
from tests.integration.conftest import client

if __name__ == '__main__':
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
    c.start()

