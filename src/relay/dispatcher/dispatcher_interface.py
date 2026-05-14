from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable

from src.package.package import Message


class DispatchCode(str, Enum):
    CHANNEL_CREATED = "Channel created"
    CHANNEL_ALREADY_EXISTS = "Room already exists"
    USER_ADDED = "User connected"
    SUBSCRIBED = "Subscribed to room"
    NO_SUCH_CHANNEL = "There is no room with name"
    USER_NOT_CONNECTED = "User is not connected"
    NO_SUCH_USER = "User is offline or does not exist"
    DIRECT_SENT = "Direct message sent"
    BROADCAST_SENT = "Message sent to room"
    CANNOT_DIRECT_SELF = "You cannot start direct chat with yourself"
    ACCESS_DENIED = "Access denied"
    USER_VERIFIED = "User verified"
    USER_ALREADY_VERIFIED = "User already verified"
    MODERATOR_GRANTED = "Moderator role granted"
    MODERATOR_ALREADY_EXISTS = "Moderator already exists"
    LEFT_ROOM = "Left room"
    NOT_IN_ROOM = "You are not in that room"
    USER_KICKED = "User removed from room"
    CANNOT_KICK_SELF = "Use /leave to exit a room; moderators cannot kick themselves"
    TARGET_NOT_IN_ROOM = "That user is not in the room"


@dataclass(frozen=True, slots=True)
class DispatchResult:
    ok: bool
    code: DispatchCode
    params: str | None = None

    def format_error(self) -> str:
        if self.params:
            return f"{self.code.value}: {self.params}"
        return self.code.value


class DispatcherInterface(ABC):
    users_funs: dict[str, Callable[[Message], Awaitable[None]]]

    @abstractmethod
    async def add_channel(
        self, channel_name: str, user_code: str | None = None
    ) -> DispatchResult:
        raise NotImplementedError

    @abstractmethod
    async def remove_channel(self, channel_name: str):
        raise NotImplementedError

    @abstractmethod
    async def broadcast(self, sender_code: str, msg: Message) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def send_message(self, addressee: str, msg: Message):
        raise NotImplementedError

    @abstractmethod
    async def add_user(
        self, send_func: Callable[[Message], Awaitable[None]]
    ) -> tuple[str, "DispatchResult"]:
        raise NotImplementedError

    @abstractmethod
    async def remove_user(self, user_code: str):
        raise NotImplementedError

    @abstractmethod
    async def subscribe(self, channel_name: str, user_code: str) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def unsubscribe(
        self, channel_name: str, user_code: str, room_notice: str | None = None
    ):
        raise NotImplementedError

    @abstractmethod
    async def leave_channel(self, channel_name: str, user_code: str) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def kick_from_channel(
        self, moderator_code: str, channel_name: str, target_user_code: str
    ) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def direct_message(
        self, sender_code: str, recipient_code: str, msg: Message
    ) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def validate_direct_message(
        self, sender_code: str, recipient_code: str
    ) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def claim_moderator(self, user_code: str) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def verify_user(
        self, moderator_code: str, target_user_code: str
    ) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def direct_message_to_moderator(
        self, sender_code: str, msg: Message
    ) -> "DispatchResult":
        raise NotImplementedError

