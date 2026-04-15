from typing import Callable

from src.package.package import Message
from src.relay.dispatcher.channel import Channel
from src.relay.dispatcher.dispatcher_interface import DispatcherInterface


class Dispatcher(DispatcherInterface):
    def __init__(self):
        self.channels: dict[str, Channel] = dict()
        self.users_funs: dict[str, Callable[[Message]]] = dict()
        self.users_channels: dict[str, set[str]] = dict()

    ### ADD / REMOVE CHANNELS ###
    async def add_channel(self, channel_name: str) -> str:
        if channel_name in self.channels:
            return f"Room {channel_name} already exists"
        self.channels[channel_name] = Channel(channel_name, self)
        return f"Room {channel_name} successfully created"

    async def remove_channel(self, channel_name: str):
        users = self.channels[channel_name].members
        self.channels.pop(channel_name)
        for username in users:
            await self.unsubscribe(channel_name, username)

    ### ADD / REMOVE USER ###
    async def add_user(self, username: str, send_func: Callable[[Message]]) -> str:
        if username in self.users_funs:
            return f"The name {username} is already taken"
        self.users_funs[username] = send_func
        self.users_channels[username] = set()
        return f"You are verified. Your name: {username}"

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
    async def subscribe(self, channel_name: str, username: str) -> str:
        if channel_name in self.channels:
            await self.channels[channel_name].subscribe(username)
            self.users_channels[username].add(channel_name)
            return f"You have subscribed to the room: {channel_name}"
        else:
            return f"There is no room with name: {channel_name}"

    async def unsubscribe(self, channel_name: str, username: str):
        if channel_name in self.channels:
            await self.channels[channel_name].unsubscribe(username)
        if username in self.users_channels:
            self.users_channels[username].remove(channel_name)
