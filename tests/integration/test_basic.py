from tgintegration import BotIntegrationClient


def test_start(client: BotIntegrationClient):
    res = client.send_command_await("/start", num_expected=3)
    assert res.num_messages == 3
    assert res[0].sticker


def test_help(client: BotIntegrationClient):
    res = client.send_command_await("/help", num_expected=1)
    assert 'reliable and unbiased bot catalog' in res.full_text.lower()
    kb = res[0].reply_markup.inline_keyboard
    assert len(kb[0]) == 3
    assert len(kb[1]) == 1

    contributing = res.press_inline_button(pattern=r'.*Contributing')
    assert "to contribute to the botlist" in contributing.full_text.lower()

    help_ = res.press_inline_button(pattern=r'.*Help')
    assert "first steps" in help_.full_text.lower()

    examples = res.press_inline_button(pattern=r'.*Examples')
    assert "Examples for contributing to the BotList:" in examples.full_text
