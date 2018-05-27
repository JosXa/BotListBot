from tgintegration import BotIntegrationClient


def test_explore_button(client: BotIntegrationClient):
    res = client.send_command_await("/start", num_expected=3)
    btn = next(x for x in res.keyboard_buttons if 'explore' in x.lower())

    explore = client.send_message_await(btn)
    assert explore.num_messages == 1

    count = 10
    while "explored all the bots" not in explore.full_text:
        if count == 0:
            break  # ok
        explore = explore.inline_keyboards[0].press_button_await(pattern=r'.*🔄')  # emoji
        count -= 1


