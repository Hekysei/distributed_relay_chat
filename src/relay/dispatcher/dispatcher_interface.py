from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable

from src.package.package import Message

if TYPE_CHECKING:
    from src.relay.dispatcher.dispatcher import DispatchResult


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
