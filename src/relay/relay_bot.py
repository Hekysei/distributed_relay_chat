from src.bot.bot import Bot
from src.relay.dispatcher.dispatcher_interface import (
    DispatchResult,
    DispatcherInterface,
)
from src.relay.message_factory import make_system_message

RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"
ROOM_CHAT_PREFIX = "c/"


class RelayBot(Bot):
    def __init__(self, dispatcher: DispatcherInterface):
        super().__init__(
            RELAY_CHAT_NAME, RELAY_BOT_NAME, lambda *_args, **_kwargs: None
        )
        self.dispatcher = dispatcher

        name_kwargs = {
            "name": "blank_name",
        }
        code_kwargs = {
            "code": "blank_code",
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
                "/direct",
                self._cmd_direct,
                code_kwargs,
            ),
            (
                "/mod",
                self._cmd_claim_moderator,
                {},
            ),
            (
                "/verify",
                self._cmd_verify_user,
                code_kwargs,
            ),
        ]
        self.add_commands(CLIENT_COMMANDS)

    async def async_send_text_to(self, client_handler, text: str):
        await client_handler.send_message(self._make_message(text))

    async def async_on_text_for(self, client_handler, text: str):
        res = await self.command_router.async_route(text, client_handler)
        if not res:
            await self.async_send_text_to(client_handler, "Unknown or Error")

    async def _send_dispatch_code(self, client_handler, dispatch_result: DispatchResult):
        await self.async_send_text_to(client_handler, dispatch_result.format_error())
        return dispatch_result.ok

    async def _cmd_join_channel(self, client_handler, name: str):
        channel_name = self._room_chat_name(name)
        res = await self.dispatcher.subscribe(channel_name, client_handler.user_code)
        await self._send_dispatch_code(client_handler, res)

    async def _cmd_create_channel(self, client_handler, name: str):
        channel_name = self._room_chat_name(name)
        res = await self.dispatcher.add_channel(channel_name, client_handler.user_code)
        if not await self._send_dispatch_code(client_handler, res):
            return
        await self._cmd_join_channel(client_handler, channel_name)

    async def _cmd_direct(self, client_handler, code: str):
        res = await self.dispatcher.validate_direct_message(client_handler.user_code, code)
        if not await self._send_dispatch_code(client_handler, res):
            return
        initiator_msg = make_system_message(
            chat=f"u/{code}",
            sender=self.bot_name,
            text=f"Direct chat with {code} started",
        )
        recipient_msg = make_system_message(
            chat=f"u/{client_handler.user_code}",
            sender=self.bot_name,
            text=f"{client_handler.username} ({client_handler.user_code}) started a direct chat with you",
        )
        await client_handler.send_message(initiator_msg)
        await self.dispatcher.send_message(code, recipient_msg)

    async def _cmd_claim_moderator(self, client_handler):
        res = await self.dispatcher.claim_moderator(client_handler.user_code)
        await self._send_dispatch_code(client_handler, res)

    async def _cmd_verify_user(self, client_handler, code: str):
        res = await self.dispatcher.verify_user(client_handler.user_code, code)
        await self._send_dispatch_code(client_handler, res)
        if not res.ok:
            return
        verified_msg = make_system_message(
            chat=self.chat_name,
            sender=self.bot_name,
            text="You have been verified by a moderator",
        )
        await self.dispatcher.send_message(code, verified_msg)

    def _make_message(self, text: str):
        return make_system_message(
            chat=self.chat_name,
            sender=self.bot_name,
            text=text,
        )

    def _room_chat_name(self, name: str) -> str:
        if name.startswith(ROOM_CHAT_PREFIX):
            return name
        return f"{ROOM_CHAT_PREFIX}{name}"
