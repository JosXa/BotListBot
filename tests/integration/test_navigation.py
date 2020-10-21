from botlistbot import captions
from tgintegration import BotIntegrationClient


def test_categories(client: BotIntegrationClient):
    # Responses implement __eq__
    assert (client.send_command_await("categories")
            == client.send_message_await(captions.CATEGORIES))

    cat = client.send_command_await("categories", num_expected=1)
    social = cat.inline_keyboards[0].press_button_await(pattern=r'.*Social')
    ilkb = social.inline_keyboards[0]
    assert ilkb.num_buttons > 3
    share_btn = ilkb.find_button(r'Share')
    assert 'Social' in share_btn.switch_inline_query
    # assert isinstance(share_btn, )

