from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable

from src.package.package import Message
from src.relay.message_factory import make_system_message
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
    BROADCAST = "broadcast"
    VERIFY_USER = "verify_user"


@dataclass(frozen=True, slots=True)
class AccessRule:
    allowed_roles: frozenset[UserRole]


class ProxyDispatcher(DispatcherInterface):
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
            PermissionAction.BROADCAST: AccessRule(room_roles),
            PermissionAction.VERIFY_USER: AccessRule(frozenset({UserRole.MODERATOR})),
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
        return await self.dispatcher.direct_message(sender_code, recipient_code, msg)

    async def validate_direct_message(
        self, sender_code: str, recipient_code: str
    ) -> DispatchResult:
        return await self.dispatcher.validate_direct_message(sender_code, recipient_code)

    async def subscribe(self, channel_name: str, user_code: str) -> DispatchResult:
        if not self._has_access(PermissionAction.SUBSCRIBE_CHANNEL, user_code):
            return DispatchResult(False, DispatchCode.ACCESS_DENIED, user_code)
        return await self.dispatcher.subscribe(channel_name, user_code)

    async def unsubscribe(self, channel_name: str, user_code: str):
        await self.dispatcher.unsubscribe(channel_name, user_code)

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
        if self.user_roles[target_user_code] != UserRole.MODERATOR:
            self.user_roles[target_user_code] = UserRole.VERIFIED
        return DispatchResult(True, DispatchCode.USER_VERIFIED, target_user_code)

    async def _send_welcome_message_from_moderator(self, user_code: str):
        if self.moderator_code is None or self.moderator_code == user_code:
            return
        await self.dispatcher.send_message(
            user_code,
            make_system_message(
                chat=f"u/{self.moderator_code}",
                sender="moderator",
                text="Welcome! This is an automatic direct message from the moderator.",
            ),
        )

