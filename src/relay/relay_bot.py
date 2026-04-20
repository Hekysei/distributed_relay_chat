from src.bot.bot import Bot
from src.package.package import Message
from src.relay.dispatcher.dispatcher import DispatchCode, Dispatcher

RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"


class RelayBot(Bot):
    def __init__(self, dispatcher: Dispatcher):
        super().__init__(
            RELAY_CHAT_NAME, RELAY_BOT_NAME, lambda *_args, **_kwargs: None
        )
        self.dispatcher = dispatcher

        async def join_channel(client_handler, name):
            res = await self.dispatcher.subscribe(name, client_handler.username)
            if res.ok:
                await self.async_send_text_to(
                    client_handler, f"You have subscribed to the room: {name}"
                )
                return
            if res.code == DispatchCode.NO_SUCH_CHANNEL:
                await self.async_send_text_to(
                    client_handler, f"There is no room with name: {name}"
                )
                return
            await self.async_send_text_to(client_handler, "Unknown or Error")

        async def add_channel(client_handler, name):
            res = await self.dispatcher.add_channel(name)
            if res.ok:
                await self.async_send_text_to(
                    client_handler, f"Room {name} successfully created"
                )
                await join_channel(client_handler, name)
                return
            if res.code == DispatchCode.CHANNEL_ALREADY_EXISTS:
                await self.async_send_text_to(
                    client_handler, f"Room {name} already exists"
                )
                return
            await self.async_send_text_to(client_handler, "Unknown or Error")

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
            if res.code == DispatchCode.USERNAME_TAKEN:
                await self.async_send_text_to(
                    client_handler,
                    f"The name {client_handler.username} is already taken",
                )
                return
            await self.async_send_text_to(client_handler, "Unknown or Error")

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
            if res.code == DispatchCode.USER_NOT_VERIFIED:
                await self.async_send_text_to(
                    client_handler, "Verify first with /v before starting direct chat"
                )
                return
            if res.code == DispatchCode.CANNOT_DIRECT_SELF:
                await self.async_send_text_to(
                    client_handler, "You cannot start a direct chat with yourself"
                )
                return
            if res.code == DispatchCode.NO_SUCH_USER:
                await self.async_send_text_to(
                    client_handler, f"User {name} is offline or does not exist"
                )
                return
            await self.async_send_text_to(client_handler, "Unknown or Error")

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
