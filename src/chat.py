from src.package.package import Message
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
        self.bot = Bot(name, bot_name, self._add_message)

    def add_commands(self, commands: list):
        self.bot.add_commands(commands)

    def send_message(self, msg: Message):
        super().send_message(msg)
        self.bot.on_text(msg.text)
