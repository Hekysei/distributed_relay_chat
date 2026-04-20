from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable

from src.package.package import Message
from src.relay.dispatcher.channel import Channel
from src.relay.dispatcher.dispatcher_interface import DispatcherInterface


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


class Dispatcher(DispatcherInterface):
    def __init__(self):
        self.channels: dict[str, Channel] = dict()
        self.users_funs: dict[str, Callable[[Message], Awaitable[None]]] = dict()
        self.users_channels: dict[str, set[str]] = dict()

    ### ADD / REMOVE CHANNELS ###
    async def add_channel(self, channel_name: str) -> DispatchResult:
        if channel_name in self.channels:
            return DispatchResult(False, DispatchCode.CHANNEL_ALREADY_EXISTS, channel_name)
        self.channels[channel_name] = Channel(channel_name, self)
        return DispatchResult(True, DispatchCode.CHANNEL_CREATED)

    async def remove_channel(self, channel_name: str):
        users = self.channels[channel_name].members
        self.channels.pop(channel_name)
        for username in users:
            await self.unsubscribe(channel_name, username)

    ### ADD / REMOVE USER ###
    async def add_user(
        self, username: str, send_func: Callable[[Message], Awaitable[None]]
    ) -> DispatchResult:
        if username in self.users_funs:
            return DispatchResult(False, DispatchCode.USERNAME_TAKEN, username)
        self.users_funs[username] = send_func
        self.users_channels[username] = set()
        return DispatchResult(True, DispatchCode.USER_ADDED)

    async def remove_user(self, username):
        if username in self.users_funs:
            channels = self.users_channels[username]
            self.users_channels.pop(username)
            for channel_name in channels:
                await self.unsubscribe(channel_name, username)
            self.users_funs.pop(username)

    ### SEND_MESSAGE ###
    async def broadcast(self, msg: Message):
        await self.channels[msg.chat].send_message(msg)

    async def send_message(self, addressee, msg):
        await self.users_funs[addressee](msg)

    async def direct_message(
        self, sender_username: str, recipient_username: str, msg: Message
    ) -> DispatchResult:
        validation_result = await self.validate_direct_message(
            sender_username, recipient_username
        )
        if not validation_result.ok:
            return validation_result
        recipient_msg = Message(
            chat=f"u/{sender_username}",
            sender=msg.sender,
            text=msg.text,
            message_id=msg.message_id,
            timestamp=msg.timestamp,
            type=msg.type,
        )
        await self.users_funs[recipient_username](recipient_msg)
        return DispatchResult(True, DispatchCode.DIRECT_SENT)

    async def validate_direct_message(
        self, sender_username: str, recipient_username: str
    ) -> DispatchResult:
        if sender_username not in self.users_funs:
            return DispatchResult(False, DispatchCode.USER_NOT_VERIFIED, sender_username)
        if sender_username == recipient_username:
            return DispatchResult(False, DispatchCode.CANNOT_DIRECT_SELF, sender_username)
        if recipient_username not in self.users_funs:
            return DispatchResult(False, DispatchCode.NO_SUCH_USER, recipient_username)
        return DispatchResult(True, DispatchCode.DIRECT_SENT)

    ### SUBSCRIPTIONS ###
    async def subscribe(self, channel_name: str, username: str) -> DispatchResult:
        if channel_name not in self.channels:
            return DispatchResult(False, DispatchCode.NO_SUCH_CHANNEL, channel_name)
        if username not in self.users_channels:
            return DispatchResult(False, DispatchCode.USER_NOT_VERIFIED, username)
        await self.channels[channel_name].subscribe(username)
        self.users_channels[username].add(channel_name)
        return DispatchResult(True, DispatchCode.SUBSCRIBED)

    async def unsubscribe(self, channel_name: str, username: str):
        if channel_name in self.channels:
            await self.channels[channel_name].unsubscribe(username)
        if username in self.users_channels:
            self.users_channels[username].remove(channel_name)
