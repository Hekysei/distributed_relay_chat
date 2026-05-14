from dataclasses import dataclass, replace
from enum import Enum
from typing import Awaitable, Callable

from src.package.package import Message, SystemMessage
from src.relay.message_factory import make_system_message
from src.relay.relay_bot import RELAY_CHAT_NAME
from src.relay.dispatcher.dispatcher_interface import (
    DispatchCode,
    DispatchResult,
    DispatcherInterface,
)


class UserRole(str, Enum):
    GUEST = "guest"
    VERIFIED = "verified"
    MODERATOR = "moderator"


class PermissionAction(str, Enum):
    CREATE_CHANNEL = "create_channel"
    SUBSCRIBE_CHANNEL = "subscribe_channel"
    LEAVE_CHANNEL = "leave_channel"
    BROADCAST = "broadcast"
    VERIFY_USER = "verify_user"
    KICK_USER = "kick_user"


@dataclass(frozen=True, slots=True)
class AccessRule:
    allowed_roles: frozenset[UserRole]


class ProxyDispatcher(DispatcherInterface):
    MODERATOR_CHAT_NAME = "m/moderator"

    def __init__(
        self,
        dispatcher: DispatcherInterface,
        rules: dict[PermissionAction, AccessRule] | None = None,
    ):
        self.dispatcher = dispatcher
        self.users_funs = dispatcher.users_funs
        self.user_roles: dict[str, UserRole] = {}
        self.moderator_code: str | None = None
        self.rules = rules or self._default_rules()

    @staticmethod
    def _default_rules() -> dict[PermissionAction, AccessRule]:
        room_roles = frozenset({UserRole.VERIFIED, UserRole.MODERATOR})
        return {
            PermissionAction.CREATE_CHANNEL: AccessRule(room_roles),
            PermissionAction.SUBSCRIBE_CHANNEL: AccessRule(room_roles),
            PermissionAction.LEAVE_CHANNEL: AccessRule(room_roles),
            PermissionAction.BROADCAST: AccessRule(room_roles),
            PermissionAction.VERIFY_USER: AccessRule(frozenset({UserRole.MODERATOR})),
            PermissionAction.KICK_USER: AccessRule(frozenset({UserRole.MODERATOR})),
        }

    def set_rule(self, action: PermissionAction, allowed_roles: set[UserRole]):
        self.rules[action] = AccessRule(frozenset(allowed_roles))

    def _has_access(self, action: PermissionAction, user_code: str) -> bool:
        role = self.user_roles.get(user_code, UserRole.GUEST)
        return role in self.rules[action].allowed_roles

    async def add_channel(
        self, channel_name: str, user_code: str | None = None
    ) -> DispatchResult:
        if user_code is None:
            return DispatchResult(False, DispatchCode.ACCESS_DENIED)
        if not self._has_access(PermissionAction.CREATE_CHANNEL, user_code):
            return DispatchResult(False, DispatchCode.ACCESS_DENIED, user_code)
        return await self.dispatcher.add_channel(channel_name, user_code)

    async def remove_channel(self, channel_name: str):
        await self.dispatcher.remove_channel(channel_name)

    async def add_user(
        self, send_func: Callable[[Message], Awaitable[None]]
    ) -> tuple[str, DispatchResult]:
        user_code, result = await self.dispatcher.add_user(send_func)
        if result.ok:
            self.user_roles[user_code] = UserRole.GUEST
            await self._send_welcome_message_from_moderator(user_code)
        return user_code, result

    async def remove_user(self, user_code: str):
        mod = self.moderator_code
        if (
            mod is not None
            and mod != user_code
            and mod in self.users_funs
        ):
            await self.dispatcher.send_message(
                mod,
                SystemMessage(
                    msg_type="client_disconnected",
                    body=user_code,
                ),
            )
        self.user_roles.pop(user_code, None)
        if self.moderator_code == user_code:
            self.moderator_code = None
        await self.dispatcher.remove_user(user_code)

    async def broadcast(self, sender_code: str, msg: Message) -> DispatchResult:
        if not self._has_access(PermissionAction.BROADCAST, sender_code):
            return DispatchResult(False, DispatchCode.ACCESS_DENIED, sender_code)
        return await self.dispatcher.broadcast(sender_code, msg)

    async def send_message(self, addressee: str, msg: Message):
        await self.dispatcher.send_message(addressee, msg)

    async def direct_message(
        self, sender_code: str, recipient_code: str, msg: Message
    ) -> DispatchResult:
        if self.moderator_code is None:
            return await self.dispatcher.direct_message(sender_code, recipient_code, msg)
        if recipient_code == self.moderator_code:
            return await self.direct_message_to_moderator(sender_code, msg)
        if sender_code == self.moderator_code:
            return await self._send_from_moderator(recipient_code, msg)
        return await self.dispatcher.direct_message(sender_code, recipient_code, msg)

    async def validate_direct_message(
        self, sender_code: str, recipient_code: str
    ) -> DispatchResult:
        return await self.dispatcher.validate_direct_message(sender_code, recipient_code)

    async def direct_message_to_moderator(
        self, sender_code: str, msg: Message
    ) -> DispatchResult:
        if self.moderator_code is None:
            return DispatchResult(False, DispatchCode.NO_SUCH_USER, "moderator")
        if sender_code == self.moderator_code:
            return DispatchResult(False, DispatchCode.CANNOT_DIRECT_SELF, sender_code)
        mapped_msg = replace(msg, chat=f"u/{self.moderator_code}")
        return await self.dispatcher.direct_message(
            sender_code, self.moderator_code, mapped_msg
        )

    async def subscribe(self, channel_name: str, user_code: str) -> DispatchResult:
        if not self._has_access(PermissionAction.SUBSCRIBE_CHANNEL, user_code):
            return DispatchResult(False, DispatchCode.ACCESS_DENIED, user_code)
        return await self.dispatcher.subscribe(channel_name, user_code)

    async def unsubscribe(
        self, channel_name: str, user_code: str, room_notice: str | None = None
    ):
        await self.dispatcher.unsubscribe(channel_name, user_code, room_notice)

    async def leave_channel(self, channel_name: str, user_code: str) -> DispatchResult:
        if not self._has_access(PermissionAction.LEAVE_CHANNEL, user_code):
            return DispatchResult(False, DispatchCode.ACCESS_DENIED, user_code)
        return await self.dispatcher.leave_channel(channel_name, user_code)

    async def kick_from_channel(
        self, moderator_code: str, channel_name: str, target_user_code: str
    ) -> DispatchResult:
        if not self._has_access(PermissionAction.KICK_USER, moderator_code):
            return DispatchResult(False, DispatchCode.ACCESS_DENIED, moderator_code)
        if moderator_code == target_user_code:
            return DispatchResult(False, DispatchCode.CANNOT_KICK_SELF)
        if channel_name not in self.dispatcher.channels:
            return DispatchResult(False, DispatchCode.NO_SUCH_CHANNEL, channel_name)
        if target_user_code not in self.dispatcher.users_funs:
            return DispatchResult(False, DispatchCode.NO_SUCH_USER, target_user_code)
        channel = self.dispatcher.channels[channel_name]
        if target_user_code not in channel.members:
            return DispatchResult(False, DispatchCode.TARGET_NOT_IN_ROOM, channel_name)
        room_notice = (
            f"user {target_user_code} was removed from the room by a moderator."
        )
        await self.dispatcher.unsubscribe(channel_name, target_user_code, room_notice)
        await self.dispatcher.send_message(
            target_user_code,
            make_system_message(
                chat=RELAY_CHAT_NAME,
                sender="relay",
                text=f"You were removed from {channel_name} by a moderator.",
            ),
        )
        return DispatchResult(True, DispatchCode.USER_KICKED, target_user_code)

    async def claim_moderator(self, user_code: str) -> DispatchResult:
        if user_code not in self.user_roles:
            return DispatchResult(False, DispatchCode.USER_NOT_CONNECTED, user_code)
        if self.moderator_code is not None:
            return DispatchResult(False, DispatchCode.MODERATOR_ALREADY_EXISTS)
        self.moderator_code = user_code
        self.user_roles[user_code] = UserRole.MODERATOR
        return DispatchResult(True, DispatchCode.MODERATOR_GRANTED, user_code)

    async def verify_user(
        self, moderator_code: str, target_user_code: str
    ) -> DispatchResult:
        if not self._has_access(PermissionAction.VERIFY_USER, moderator_code):
            return DispatchResult(False, DispatchCode.ACCESS_DENIED, moderator_code)
        if target_user_code not in self.user_roles:
            return DispatchResult(False, DispatchCode.NO_SUCH_USER, target_user_code)
        if self.user_roles[target_user_code] == UserRole.VERIFIED:
            return DispatchResult(False, DispatchCode.USER_ALREADY_VERIFIED, target_user_code)
        if self.user_roles[target_user_code] != UserRole.MODERATOR:
            self.user_roles[target_user_code] = UserRole.VERIFIED
        return DispatchResult(True, DispatchCode.USER_VERIFIED, target_user_code)

    async def _send_welcome_message_from_moderator(self, user_code: str):
        if self.moderator_code is None or self.moderator_code == user_code:
            return
        await self.dispatcher.send_message(
            user_code,
            make_system_message(
                chat=self.MODERATOR_CHAT_NAME,
                sender="moderator",
                text="Welcome! This is an automatic direct message from the moderator.",
            ),
        )

    async def _send_from_moderator(self, recipient_code: str, msg: Message) -> DispatchResult:
        validation_result = await self.dispatcher.validate_direct_message(
            self.moderator_code, recipient_code
        )
        if not validation_result.ok:
            return validation_result
        recipient_msg = replace(msg, chat=self.MODERATOR_CHAT_NAME)
        await self.dispatcher.send_message(recipient_code, recipient_msg)
        return DispatchResult(True, DispatchCode.DIRECT_SENT)

