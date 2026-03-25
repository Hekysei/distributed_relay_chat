#!/usr/bin/env python3


from tui_adapter import TUI_Adapter
from client import Client


class APP:
    def __init__(self):
        self.client = Client()
        self.tui_adapter = TUI_Adapter(self.client)

        self.client.on_message_callback = self.tui_adapter.update_messages
        self.client.on_chat_added_callback = self.tui_adapter.update_bar
        self.client.on_chat_removed_callback = self.tui_adapter.handle_chat_removed

    def run(self):
        self.tui_adapter.run()
        self.client.stop()


if __name__ == "__main__":
    app = APP()
    app.run()
