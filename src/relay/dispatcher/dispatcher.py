from typing import Awaitable, Callable
from uuid import uuid4

from src.package.package import Message
from src.relay.dispatcher.channel import Channel
from src.relay.dispatcher.dispatcher_interface import (
    DispatchCode,
    DispatchResult,
    DispatcherInterface,
)


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
        self, send_func: Callable[[Message], Awaitable[None]]
    ) -> tuple[str, DispatchResult]:
        user_code = self._make_unique_user_code()
        self.users_funs[user_code] = send_func
        self.users_channels[user_code] = set()
        return user_code, DispatchResult(True, DispatchCode.USER_ADDED)

    async def remove_user(self, user_code: str):
        if user_code in self.users_funs:
            channels = self.users_channels[user_code]
            self.users_channels.pop(user_code)
            for channel_name in channels:
                await self.unsubscribe(channel_name, user_code)
            self.users_funs.pop(user_code)

    ### SEND_MESSAGE ###
    async def broadcast(self, sender_code: str, msg: Message):
        await self.channels[msg.chat].send_message(sender_code, msg)

    async def send_message(self, addressee, msg):
        await self.users_funs[addressee](msg)

    async def direct_message(
        self, sender_code: str, recipient_code: str, msg: Message
    ) -> DispatchResult:
        validation_result = await self.validate_direct_message(
            sender_code, recipient_code
        )
        if not validation_result.ok:
            return validation_result
        recipient_msg = Message(
            chat=f"u/{sender_code}",
            sender=msg.sender,
            text=msg.text,
            message_id=msg.message_id,
            timestamp=msg.timestamp,
            type=msg.type,
        )
        await self.users_funs[recipient_code](recipient_msg)
        return DispatchResult(True, DispatchCode.DIRECT_SENT)

    async def validate_direct_message(
        self, sender_code: str, recipient_code: str
    ) -> DispatchResult:
        if sender_code not in self.users_funs:
            return DispatchResult(False, DispatchCode.USER_NOT_CONNECTED, sender_code)
        if sender_code == recipient_code:
            return DispatchResult(False, DispatchCode.CANNOT_DIRECT_SELF, sender_code)
        if recipient_code not in self.users_funs:
            return DispatchResult(False, DispatchCode.NO_SUCH_USER, recipient_code)
        return DispatchResult(True, DispatchCode.DIRECT_SENT)

    ### SUBSCRIPTIONS ###
    async def subscribe(self, channel_name: str, user_code: str) -> DispatchResult:
        if channel_name not in self.channels:
            return DispatchResult(False, DispatchCode.NO_SUCH_CHANNEL, channel_name)
        if user_code not in self.users_channels:
            return DispatchResult(False, DispatchCode.USER_NOT_CONNECTED, user_code)
        await self.channels[channel_name].subscribe(user_code)
        self.users_channels[user_code].add(channel_name)
        return DispatchResult(True, DispatchCode.SUBSCRIBED)

    async def unsubscribe(self, channel_name: str, user_code: str):
        if channel_name in self.channels:
            await self.channels[channel_name].unsubscribe(user_code)
        if user_code in self.users_channels:
            self.users_channels[user_code].remove(channel_name)

    def _make_unique_user_code(self) -> str:
        while True:
            user_code = str(uuid4())
            if user_code not in self.users_funs:
                return user_code
