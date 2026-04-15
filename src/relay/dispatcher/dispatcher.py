from dataclasses import dataclass
from enum import Enum
from typing import Callable

from src.package.package import Message
from src.relay.dispatcher.channel import Channel
from src.relay.dispatcher.dispatcher_interface import DispatcherInterface


class DispatchCode(str, Enum):
    CHANNEL_CREATED = "channel_created"
    CHANNEL_ALREADY_EXISTS = "channel_already_exists"
    USER_ADDED = "user_added"
    USERNAME_TAKEN = "username_taken"
    SUBSCRIBED = "subscribed"
    NO_SUCH_CHANNEL = "no_such_channel"
    USER_NOT_VERIFIED = "user_not_verified"


@dataclass(frozen=True, slots=True)
class DispatchResult:
    ok: bool
    code: DispatchCode


class Dispatcher(DispatcherInterface):
    def __init__(self):
        self.channels: dict[str, Channel] = dict()
        self.users_funs: dict[str, Callable[[Message]]] = dict()
        self.users_channels: dict[str, set[str]] = dict()

    ### ADD / REMOVE CHANNELS ###
    async def add_channel(self, channel_name: str) -> DispatchResult:
        if channel_name in self.channels:
            return DispatchResult(False, DispatchCode.CHANNEL_ALREADY_EXISTS)
        self.channels[channel_name] = Channel(channel_name, self)
        return DispatchResult(True, DispatchCode.CHANNEL_CREATED)

    async def remove_channel(self, channel_name: str):
        users = self.channels[channel_name].members
        self.channels.pop(channel_name)
        for username in users:
            await self.unsubscribe(channel_name, username)

    ### ADD / REMOVE USER ###
    async def add_user(
        self, username: str, send_func: Callable[[Message]]
    ) -> DispatchResult:
        if username in self.users_funs:
            return DispatchResult(False, DispatchCode.USERNAME_TAKEN)
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
        self.users_funs[addressee](msg)

    ### SUBSCRIPTIONS ###
    async def subscribe(self, channel_name: str, username: str) -> DispatchResult:
        if channel_name not in self.channels:
            return DispatchResult(False, DispatchCode.NO_SUCH_CHANNEL)
        if username not in self.users_channels:
            return DispatchResult(False, DispatchCode.USER_NOT_VERIFIED)
        await self.channels[channel_name].subscribe(username)
        self.users_channels[username].add(channel_name)
        return DispatchResult(True, DispatchCode.SUBSCRIBED)

    async def unsubscribe(self, channel_name: str, username: str):
        if channel_name in self.channels:
            await self.channels[channel_name].unsubscribe(username)
        if username in self.users_channels:
            self.users_channels[username].remove(channel_name)
