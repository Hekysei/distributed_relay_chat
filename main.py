#!/usr/bin/env python3

from src.app.tui_adapter import TUI_Adapter
from src.app.app_client import APPClient


class APP:
    def __init__(self):
        self.client = APPClient()
        self.tui_adapter = TUI_Adapter(self.client)

        self.client.on_message_callback = self.tui_adapter.update_messages
        self.client.on_chat_added_callback = self.tui_adapter.update_bar
        self.client.on_chat_removed_callback = self.tui_adapter.handle_chat_removed

    def run(self):
        self.tui_adapter.run()
        # self.client.disconnect()


if __name__ == "__main__":
    app = APP()
    app.run()
