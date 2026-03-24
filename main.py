#!/usr/bin/env python3
from threading import Thread

from client import Client
from tui_adapter import TUI_Adapter


class APP:
    def __init__(self):
        self.client = Client()
        self.tui_adapter = TUI_Adapter(self.client)

        self.client.on_got_message = self.tui_adapter.update_messages

    def run(self):
        self.tui_adapter.run()
        Thread(target=self.client.run).start()
        self.client.stop()


if __name__ == "__main__":
    app = APP()
    app.run()
