from src.package.package import Message
from src.relay.dispatcher.dispatcher_interface import DispatcherInterface


class Channel:
    def __init__(self, name: str, dispatcher: DispatcherInterface):
        self.name = name
        self.dispatcher = dispatcher
        self.members: set[str] = set()

    async def send_message(self, msg: Message):
        for name in self.members:
            if name != msg.sender:
                await self.dispatcher.users_funs[name](msg)

    async def send_text_to_self(self, text: str):
        await self.send_message(
            Message(
                chat=self.name,
                sender="relay",
                text=text,
            ).set_timestamp_now()
        )

    async def subscribe(self, username: str):
        self.members.add(username)
        await self.send_text_to_self(f"{username} entered the room.")

    async def unsubscribe(self, username: str):
        self.members.remove(username)
        await self.send_text_to_self(f"{username} left the chat.")

