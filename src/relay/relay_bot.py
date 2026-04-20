from src.bot.bot import Bot
from src.relay.dispatcher.dispatcher import Dispatcher
from src.relay.dispatcher.dispatcher_interface import DispatchResult
from src.relay.message_factory import make_system_message

RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"


class RelayBot(Bot):
    def __init__(self, dispatcher: Dispatcher):
        super().__init__(
            RELAY_CHAT_NAME, RELAY_BOT_NAME, lambda *_args, **_kwargs: None
        )
        self.dispatcher = dispatcher

        name_kwargs = {
            "name": "blank_name",
        }
        CLIENT_COMMANDS = [
            (
                "/create",
                self._cmd_create_channel,
                name_kwargs,
            ),
            (
                "/join",
                self._cmd_join_channel,
                name_kwargs,
            ),
            (
                "/v",
                self._cmd_verify,
                {},
            ),
            (
                "/direct",
                self._cmd_direct,
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

    async def _send_dispatch_error(self, client_handler, dispatch_result: DispatchResult):
        await self.async_send_text_to(client_handler, dispatch_result.format_error())

    async def _cmd_join_channel(self, client_handler, name: str):
        res = await self.dispatcher.subscribe(name, client_handler.username)
        if not res.ok:
            await self._send_dispatch_error(client_handler, res)
            return
        await self.async_send_text_to(
            client_handler, f"You have subscribed to the room: {name}"
        )

    async def _cmd_create_channel(self, client_handler, name: str):
        res = await self.dispatcher.add_channel(name)
        if not res.ok:
            await self._send_dispatch_error(client_handler, res)
            return
        await self.async_send_text_to(client_handler, f"Room {name} successfully created")
        await self._cmd_join_channel(client_handler, name)

    async def _cmd_verify(self, client_handler):
        res = await self.dispatcher.add_user(
            client_handler.username, client_handler.send_message
        )
        if not res.ok:
            await self._send_dispatch_error(client_handler, res)
            return
        await self.async_send_text_to(
            client_handler,
            f"You are verified. Your name: {client_handler.username}",
        )

    async def _cmd_direct(self, client_handler, name: str):
        res = await self.dispatcher.validate_direct_message(client_handler.username, name)
        if not res.ok:
            await self._send_dispatch_error(client_handler, res)
            return
        initiator_msg = make_system_message(
            chat=f"u/{name}",
            sender=self.bot_name,
            text=f"Direct chat with {name} started",
        )
        recipient_msg = make_system_message(
            chat=f"u/{client_handler.username}",
            sender=self.bot_name,
            text=f"{client_handler.username} started a direct chat with you",
        )
        await client_handler.send_message(initiator_msg)
        await self.dispatcher.send_message(name, recipient_msg)

    def _make_message(self, text: str):
        return make_system_message(
            chat=self.chat_name,
            sender=self.bot_name,
            text=text,
        )
