from src.bot.bot import Bot
from src.relay.dispatcher.dispatcher_interface import (
    DispatchResult,
    DispatcherInterface,
)
from src.relay.message_factory import make_system_message

RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"


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

    async def _send_dispatch_error(self, client_handler, dispatch_result: DispatchResult):
        await self.async_send_text_to(client_handler, dispatch_result.format_error())

    async def _cmd_join_channel(self, client_handler, name: str):
        res = await self.dispatcher.subscribe(name, client_handler.user_code)
        if not res.ok:
            await self._send_dispatch_error(client_handler, res)
            return
        await self.async_send_text_to(
            client_handler, f"You have subscribed to the room: {name}"
        )

    async def _cmd_create_channel(self, client_handler, name: str):
        res = await self.dispatcher.add_channel(name, client_handler.user_code)
        if not res.ok:
            await self._send_dispatch_error(client_handler, res)
            return
        await self.async_send_text_to(client_handler, f"Room {name} successfully created")
        await self._cmd_join_channel(client_handler, name)

    async def _cmd_direct(self, client_handler, code: str):
        res = await self.dispatcher.validate_direct_message(client_handler.user_code, code)
        if not res.ok:
            await self._send_dispatch_error(client_handler, res)
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
        if not res.ok:
            await self._send_dispatch_error(client_handler, res)
            return
        await self.async_send_text_to(client_handler, "You are now a moderator")

    async def _cmd_verify_user(self, client_handler, code: str):
        res = await self.dispatcher.verify_user(client_handler.user_code, code)
        if not res.ok:
            await self._send_dispatch_error(client_handler, res)
            return
        await self.async_send_text_to(client_handler, f"User {code} is verified")

    def _make_message(self, text: str):
        return make_system_message(
            chat=self.chat_name,
            sender=self.bot_name,
            text=text,
        )
