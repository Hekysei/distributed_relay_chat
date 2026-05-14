from dataclasses import dataclass

from src.bot.bot import Bot
from src.client.client import Client
from src.moderator.moderator_accounts import ModeratorAccountStore
from src.package.package import Message, SystemMessage
from src.relay.dispatcher.dispatcher_interface import DispatchCode

RELAY_BOT_CHAT = "r/relay"
USER_DIRECT_PREFIX = "u/"


@dataclass(frozen=True, slots=True)
class ModerationContext:
    relay_user_code: str
    username: str


class ModeratorClient(Client):
    def __init__(self) -> None:
        super().__init__()
        self._message_seq = 0
        self._accounts = ModeratorAccountStore()

        async def _discard_bot_outgoing(_msg: Message) -> None:
            pass

        self._user_commands = Bot("mod/commands", "moderator", _discard_bot_outgoing)
        self._user_commands.add_commands(
            [
                (
                    "/register",
                    self._cmd_register,
                    {"password1": "", "password2": ""},
                ),
                (
                    "/login",
                    self._cmd_login,
                    {"password": ""},
                ),
            ]
        )

    async def on_connected(self) -> None:
        self.username = "moderator"
        await super().on_connected()
        await self._send_user_text(RELAY_BOT_CHAT, "/mod")
        print(
            "Moderator session started. Users message m/moderator: "
            "/register <password> <password> if the name is new, "
            "/login <password> if the name is already registered. "
            "They must set their display name on the client first. "
            "Relay notifies this process when a client disconnects (client_disconnected)."
        )

    async def _send_user_text(self, chat: str, text: str) -> None:
        self._message_seq += 1
        msg = Message(
            chat=chat,
            sender=self.username,
            text=text,
            message_id=self._message_seq,
        )
        await self.send_message(msg)

    async def _notify_relay_user(self, relay_user_code: str, text: str) -> None:
        await self._send_user_text(f"{USER_DIRECT_PREFIX}{relay_user_code}", text)

    async def _request_verify(self, relay_user_code: str) -> None:
        await self._send_user_text(RELAY_BOT_CHAT, f"/verify {relay_user_code}")

    @staticmethod
    def _relay_target_user_code(relay_line: str) -> str | None:
        """Parse relay bot lines shaped like DispatchResult.format_error (code: params)."""
        if ": " not in relay_line:
            return None
        head, tail = relay_line.split(": ", 1)
        tail = tail.strip()
        if not tail:
            return None
        if head in (
            DispatchCode.USER_VERIFIED.value,
            DispatchCode.USER_ALREADY_VERIFIED.value,
            DispatchCode.NO_SUCH_USER.value,
        ):
            return tail
        return None

    async def _cmd_register(
        self, ctx: ModerationContext, password1: str, password2: str
    ) -> None:
        relay_user_code = ctx.relay_user_code
        username = ctx.username
        if not password1 or not password2:
            await self._notify_relay_user(
                relay_user_code,
                "Usage: /register <password> <password>",
            )
            return
        if password1 != password2:
            await self._notify_relay_user(
                relay_user_code,
                "Passwords do not match.",
            )
            return
        if self._accounts.is_registered(username):
            await self._notify_relay_user(
                relay_user_code,
                "Username already taken. Use /login <password>.",
            )
            return
        ok, err = self._accounts.register(username, password1)
        if not ok:
            await self._notify_relay_user(relay_user_code, err)
            return
        ok_bind, err_bind = self._accounts.bind_session(username, relay_user_code)
        if not ok_bind:
            self._accounts.delete_account(username)
            await self._notify_relay_user(relay_user_code, err_bind)
            return
        await self._request_verify(relay_user_code)

    async def _cmd_login(self, ctx: ModerationContext, password: str) -> None:
        relay_user_code = ctx.relay_user_code
        username = ctx.username
        if not password:
            await self._notify_relay_user(
                relay_user_code,
                "Usage: /login <password>",
            )
            return
        if not self._accounts.is_registered(username):
            await self._notify_relay_user(
                relay_user_code,
                "Unknown username. Use /register <password> <password>.",
            )
            return
        if not self._accounts.check_password(username, password):
            await self._notify_relay_user(relay_user_code, "Wrong password.")
            return
        ok_bind, err_bind = self._accounts.bind_session(username, relay_user_code)
        if not ok_bind:
            await self._notify_relay_user(relay_user_code, err_bind)
            return
        await self._request_verify(relay_user_code)

    async def on_msg(self, msg: Message) -> None:
        line = msg.text.replace("\n", " ").strip()
        print(f"[{msg.chat}] {msg.sender}: {line}")

        if msg.chat == RELAY_BOT_CHAT:
            target = self._relay_target_user_code(msg.text.strip())
            if target:
                await self._notify_relay_user(target, f"[relay] {msg.text}")
                if not msg.text.startswith(DispatchCode.USER_VERIFIED.value):
                    self._accounts.clear_relay_user(target)
            return

        if not msg.chat.startswith(USER_DIRECT_PREFIX):
            return

        relay_user_code = msg.chat[len(USER_DIRECT_PREFIX) :].strip()
        username = (msg.sender or "").strip()
        if not relay_user_code:
            return
        if not username:
            await self._notify_relay_user(
                relay_user_code,
                "Set your username on the client before auth.",
            )
            return

        words = line.split()
        if words:
            words[0] = words[0].lower()
            normalized = " ".join(words)
        else:
            normalized = line

        ctx = ModerationContext(relay_user_code, username)
        routed = await self._user_commands.command_router.async_route(normalized, ctx)
        if not routed:
            await self._notify_relay_user(
                relay_user_code,
                "Commands: /register <password> <password> or /login <password>",
            )

    async def on_sys_msg(self, sys_msg: SystemMessage) -> None:
        if sys_msg.msg_type == "set_username":
            await self.set_username(sys_msg.body)
            return
        if sys_msg.msg_type == "client_disconnected":
            code = (sys_msg.body or "").strip()
            released = self._accounts.clear_relay_user(code)
            if released:
                print(f"Relay client disconnected {code}; released account session {released!r}.")
            else:
                print(f"Relay client disconnected {code} (no active named session).")
            return
        print(f"[system {sys_msg.msg_type}] {sys_msg.body}")
