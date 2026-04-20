from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable

from src.package.package import Message


class DispatchCode(str, Enum):
    CHANNEL_CREATED = "Channel created"
    CHANNEL_ALREADY_EXISTS = "Room already exists"
    USER_ADDED = "User verified"
    USERNAME_TAKEN = "The name is already taken"
    SUBSCRIBED = "Subscribed to room"
    NO_SUCH_CHANNEL = "There is no room with name"
    USER_NOT_VERIFIED = "User is not verified"
    NO_SUCH_USER = "User is offline or does not exist"
    DIRECT_SENT = "Direct message sent"
    CANNOT_DIRECT_SELF = "You cannot start direct chat with yourself"


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
    async def broadcast(self, msg: Message):
        raise NotImplementedError

    @abstractmethod
    async def send_message(self, addressee: str, msg: Message):
        raise NotImplementedError

    @abstractmethod
    async def add_user(
        self, username: str, send_func: Callable[[Message], Awaitable[None]]
    ) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def remove_user(self, username: str):
        raise NotImplementedError

    @abstractmethod
    async def subscribe(self, channel_name: str, username: str) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def unsubscribe(self, channel_name: str, username: str):
        raise NotImplementedError

    @abstractmethod
    async def direct_message(
        self, sender_username: str, recipient_username: str, msg: Message
    ) -> "DispatchResult":
        raise NotImplementedError

    @abstractmethod
    async def validate_direct_message(
        self, sender_username: str, recipient_username: str
    ) -> "DispatchResult":
        raise NotImplementedError
