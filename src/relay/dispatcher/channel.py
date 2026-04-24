from src.package.package import Message
from src.relay.dispatcher.dispatcher_interface import DispatcherInterface


class Channel:
    def __init__(self, name: str, dispatcher: DispatcherInterface):
        self.name = name
        self.dispatcher = dispatcher
        self.members: set[str] = set()

    async def send_message(self, sender_code: str, msg: Message):
        for user_code in self.members:
            if user_code != sender_code:
                await self.dispatcher.users_funs[user_code](msg)

    async def send_text_to_self(self, text: str):
        await self.send_message(
            "",
            Message(
                chat=self.name,
                sender="relay",
                text=text,
            ).set_timestamp_now(),
        )

    async def subscribe(self, user_code: str):
        self.members.add(user_code)
        await self.send_text_to_self(f"user {user_code} entered the room.")

    async def unsubscribe(self, user_code: str):
        self.members.remove(user_code)
        await self.send_text_to_self(f"user {user_code} left the chat.")
