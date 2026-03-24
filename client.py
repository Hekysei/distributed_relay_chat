from typing import Callable, Dict, Any

from net_client import NetClient


class Client:
    def __init__(self):
        self.net_client = NetClient()
        self.messages = ["welcome"]

        self.on_got_message: Callable[[], None] = lambda: None

    def run(self):
        if self.net_client.connect():
            for message in self.net_client.recv_loop():
                message: Dict[str, Any]
                self.add_message(str(message))
        self.add_message("Сonnection lost")

    def stop(self):
        self.net_client.ws.close()

    def add_message(self, message: str):
        self.messages.append(message)
        self.on_got_message()

    def send_message(self, message: str):
        self.add_message(message)
        data = {"text": message}
        if not self.net_client.send(data):
            self.add_message("No server")
