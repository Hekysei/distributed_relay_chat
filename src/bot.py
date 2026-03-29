from typing import Callable


from src.command_router import CommandRouter
from src.message import Message

greetings = [
    "Welcome!",
    "Commands:",
    "/c, /connect - connect to relay",
    "/d - disconnect",
]


class Bot:
    def __init__(self, chat_name, bot_name, send_message):
        self.chat_name = chat_name
        self.bot_name = bot_name

        self.command_router = CommandRouter()

        self.send_message: Callable[[Message]] = send_message
        for greet in greetings:
            self.send_text(greet)

    def add_command(self, command: str, function: Callable[...], args: dict[str, str]):
        self.command_router.add_command(command, function, args)

    def send_text(self, text: str):
        self.send_message(Message(self.chat_name, self.bot_name, text))

    def on_text(self, text: str):
        if text.startswith("/") and not self.command_router.route(text):
            self.send_text("Unknown or Error")
