from src.bot.bot import Bot
from src.relay.dispatcher.dispatcher import Dispatcher

RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"


class RelayBot(Bot):
    def __init__(self, dispatcher: Dispatcher):
        super().__init__(RELAY_CHAT_NAME, RELAY_BOT_NAME, lambda *_args, **_kwargs: None)
        self.dispatcher = dispatcher

        async def join_channel(client_handler, name):
            res = await self.dispatcher.subscribe(name, client_handler.username)
            await self.async_send_text_to(client_handler, res)

        async def add_channel(client_handler, name):
            res = await self.dispatcher.add_channel(name)
            await self.async_send_text_to(client_handler, res)
            await join_channel(client_handler, name)

        async def verify(client_handler):
            res = await self.dispatcher.add_user(
                client_handler.username, client_handler.send_message
            )
            await self.async_send_text_to(client_handler, res)

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

    async def async_send_text_to(self, client_handler, text: str):
        await client_handler.send_message(self._make_message(text))

    async def async_on_text_for(self, client_handler, text: str):
        res = await self.command_router.async_route(text, client_handler)
        if not res:
            await self.async_send_text_to(client_handler, "Unknown or Error")

    def _make_message(self, text: str):
        # Use Bot's message shape (chat_name/bot_name + timestamp logic in Message itself).
        # Bot.async_send_text can't be used because RelayBot is shared across clients.
        from datetime import datetime
        from src.package.package import Message

        return Message(
            chat=self.chat_name,
            sender=self.bot_name,
            text=text,
            timestamp=datetime.now(),
        )
