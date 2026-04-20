from src.bot.bot import Bot
from src.package.package import Message
from src.relay.dispatcher.dispatcher import Dispatcher

RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"


class RelayBot(Bot):
    def __init__(self, dispatcher: Dispatcher):
        super().__init__(
            RELAY_CHAT_NAME, RELAY_BOT_NAME, lambda *_args, **_kwargs: None
        )
        self.dispatcher = dispatcher

        def format_dispatch_error(res):
            if res.params:
                return f"{res.code.value}: {res.params}"
            return res.code.value

        async def join_channel(client_handler, name):
            res = await self.dispatcher.subscribe(name, client_handler.username)
            if res.ok:
                await self.async_send_text_to(
                    client_handler, f"You have subscribed to the room: {name}"
                )
                return
            await self.async_send_text_to(client_handler, format_dispatch_error(res))

        async def add_channel(client_handler, name):
            res = await self.dispatcher.add_channel(name)
            if res.ok:
                await self.async_send_text_to(
                    client_handler, f"Room {name} successfully created"
                )
                await join_channel(client_handler, name)
                return
            await self.async_send_text_to(client_handler, format_dispatch_error(res))

        async def verify(client_handler):
            res = await self.dispatcher.add_user(
                client_handler.username, client_handler.send_message
            )
            if res.ok:
                await self.async_send_text_to(
                    client_handler,
                    f"You are verified. Your name: {client_handler.username}",
                )
                return
            await self.async_send_text_to(client_handler, format_dispatch_error(res))

        async def direct(client_handler, name):
            res = await self.dispatcher.validate_direct_message(
                client_handler.username, name
            )
            if res.ok:
                initiator_msg = Message(
                    chat=f"u/{name}",
                    sender=self.bot_name,
                    text=f"Direct chat with {name} started",
                ).set_timestamp_now()
                recipient_msg = Message(
                    chat=f"u/{client_handler.username}",
                    sender=self.bot_name,
                    text=f"{client_handler.username} started a direct chat with you",
                ).set_timestamp_now()
                await client_handler.send_message(initiator_msg)
                await self.dispatcher.send_message(name, recipient_msg)
                return
            await self.async_send_text_to(client_handler, format_dispatch_error(res))

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
            (
                "/direct",
                direct,
                name_kwargs,
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
        return Message(
            chat=self.chat_name,
            sender=self.bot_name,
            text=text,
        ).set_timestamp_now()
