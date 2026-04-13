from src.bot import Bot

RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"

class RelayBot(Bot):
    def __init__(self, client_handler):
        super().__init__(
            RELAY_CHAT_NAME, RELAY_BOT_NAME, client_handler.send_message
        )

        async def create_channel(name):
            await client_handler.dispatcher.create_channel(
                name, client_handler.username, client_handler.send_message
            )

        async def join_channel(name):
            await client_handler.dispatcher.subscribe(
                name, client_handler.username, client_handler.send_message
            )

        name_kwargs = {
            "name": "blank_name",
        }
        CLIENT_COMMANDS = [
            (
                "/create",
                create_channel,
                name_kwargs,
            ),
            (
                "/join",
                join_channel,
                name_kwargs,
            ),
        ]
        self.add_commands(CLIENT_COMMANDS)
