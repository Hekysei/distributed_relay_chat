from typing import Callable

class Client:
    def __init__(self):
        self.messages = ["welcome"]

        self.on_got_message : Callable[[], None] = (lambda: None)

    def add_message(self, message: str):
        self.messages.append(message)
        self.on_got_message()
