from typing import Callable

from src.package.package import Message


class Channel:
    def __init__(self):
        self.members_funcs: dict[str, Callable[[Message]]] = dict()

    async def send_message(
        self, msg: Message, sender_func: Callable[[Message]] | None = None
    ):
        for func in self.members_funcs.values():
            if func != sender_func:
                await func(msg)

    def subscribe(self, username: str, send_func: Callable[[Message]]):
        self.members_funcs[username] = send_func

    def unsubscribe(self, username: str):
        self.members_funcs.pop(username)


# Dependency Injection
# Pub/Sub
class Dispatcher:
    def __init__(self):
        self.channels: dict[str, Channel] = dict()
        self.users: dict[str, Callable[[Message]]] = dict()

    async def send_message(self, msg: Message, sender_func: Callable[[Message]]):
        await self.channels[msg.chat].send_message(msg, sender_func)

    async def subscribe(
        self, channel_name: str, username: str, send_func: Callable[[Message]]
    ):
        if channel_name in self.channels:
            self.channels[channel_name].subscribe(username, send_func)
            await self.channels[channel_name].send_message(
                Message(
                    chat=channel_name,
                    sender="relay",
                    text=f"{username} has entered the chat.",
                ).set_timestamp_now()
            )
        else:
            await send_func(
                Message(
                    chat="r/relay",
                    sender="dispatcher",
                    text="There is no room with this name",
                ).set_timestamp_now()
            )

    async def unsubscribe(self, channel_name: str, username: str):
        self.channels[channel_name].unsubscribe(username)

    async def create_channel(
        self, channel_name: str, username: str, send_func: Callable[[Message]]
    ):
        self.channels[channel_name] = Channel()
        await self.subscribe(channel_name, username, send_func)

    async def call(self, msg: Message):
        print("call", msg)
