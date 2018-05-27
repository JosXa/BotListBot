from tgintegration import BotIntegrationClient


def test_commands(client: BotIntegrationClient):

    for c in client.command_list:
        print("Sending {} ({})".format(c.command, c.description))

        res = client.send_command_await(c.command)
        assert not res.empty
