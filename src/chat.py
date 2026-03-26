from src.message import Message
from src.bot import Bot

class Chat:
    def __init__(self, name):
        self.name = name
        self.messages: list[Message] = []

    def _add_message(self, msg: Message):
        self.messages.append(msg)

    def send_message(self, msg: Message):
        self._add_message(msg)


class ChatBot(Chat):
    def __init__(self, name, bot_name):
        super().__init__(name)
        self.bot = Bot(
            lambda text: self._add_message(Message(name, bot_name, text)),
        )

    def add_commands(self, commands: list):
        for command in commands:
            self.bot.add_command(*command)

    def send_message(self, msg: Message):
        super().send_message(msg)
        self.bot.on_text(msg.text)


