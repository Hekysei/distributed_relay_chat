#!/usr/bin/env python3

from threading import Thread

from curses import wrapper, window

from tui_adapter import TUI_Adapter
from client import Client


class APP:
    def __init__(self):
        self.client = Client()

    def run(self):
        wrapper(self.__run_in_wrapper)

    def __run_in_wrapper(self, stdscr: window):
        tui_adapter = TUI_Adapter(stdscr, self.client)
        self.client.on_message_callback = tui_adapter.update_messages
        self.client.on_chat_added_callback = tui_adapter.update_bar

        Thread(target=self.client.run).start()
        tui_adapter.run()

        self.client.stop()


if __name__ == "__main__":
    app = APP()
    app.run()
