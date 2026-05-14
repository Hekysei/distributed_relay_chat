from typing import Callable

from src.bot.command_router import CommandRouter
from src.package.package import Message
from src.relay.message_factory import make_system_message


class Bot:
    def __init__(self, chat_name, bot_name, send_message):
        self.chat_name = chat_name
        self.bot_name = bot_name

        self.command_router = CommandRouter()

        self.send_message: Callable[[Message]] = send_message

    def add_command(self, command: str, function: Callable, args: dict[str, str]):
        self.command_router.add_command(command, function, args)

    def add_commands(self, commands: list):
        for command in commands:
            self.add_command(*command)

    async def async_send_text(self, text: str):
        await self.send_message(
            make_system_message(
                chat=self.chat_name,
                sender=self.bot_name,
                text=text,
            )
        )

    async def async_on_text(self, text: str):
        res = await self.command_router.async_route(text)
        if not res:
            await self.async_send_text("Unknown or Error")
