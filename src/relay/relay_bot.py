from src.bot.bot import Bot

RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"


class RelayBot(Bot):
    def __init__(self, client_handler):
        super().__init__(RELAY_CHAT_NAME, RELAY_BOT_NAME, client_handler.send_message)

        async def join_channel(name):
            res = await client_handler.dispatcher.subscribe(
                name, client_handler.username
            )
            await self.async_send_text(res)

        async def add_channel(name):
            res = await client_handler.dispatcher.add_channel(name)
            await self.async_send_text(res)
            await join_channel(name)

        async def verify():
            res = await client_handler.dispatcher.add_user(
                client_handler.username, client_handler.send_message
            )
            await self.async_send_text(res)

        name_kwargs = {
            "name": "blank_name",
        }
        CLIENT_COMMANDS = [
            (
                "/create",
                add_channel,
                name_kwargs,
            ),
            (
                "/join",
                join_channel,
                name_kwargs,
            ),
            (
                "/v",
                verify,
                {},
            ),
        ]
        self.add_commands(CLIENT_COMMANDS)
