from typing import Callable


from src.command_router import CommandRouter
from src.message import Message


class Bot:
    def __init__(self, chat_name, bot_name, send_message):
        self.chat_name = chat_name
        self.bot_name = bot_name

        self.command_router = CommandRouter()

        self.send_message: Callable[[Message]] = send_message

    def add_command(self, command: str, function: Callable[...], args: dict[str, str]):
        self.command_router.add_command(command, function, args)

    def add_commands(self, commands: list):
        for command in commands:
            self.add_command(*command)

    def send_text(self, text: str):
        self.send_message(Message(chat=self.chat_name, sender=self.bot_name, text=text))

    async def async_send_text(self, text: str):
        await self.send_message(
            Message(chat=self.chat_name, sender=self.bot_name, text=text)
        )

    def on_text(self, text: str):
        if not self.command_router.route(text):
            self.send_text("Unknown or Error")

    async def async_on_text(self, text: str):
        if not await self.command_router.async_route(text):
            await self.async_send_text("Unknown or Error")
