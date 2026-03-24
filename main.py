#!/usr/bin/env python3

from threading import Thread

# wrapper нельзя просто отделить от потоков и не сломать его работу
from curses import wrapper

from client import Client
from tui_adapter import TUI_Adapter


class APP:
    def __init__(self):
        self.client = Client()
        self.cli_adapter = TUI_Adapter(self.client)

        self.client.on_got_message = self.cli_adapter.update_messages

    def run(self):
        self.process_gui = Thread(target=wrapper(self.cli_adapter.run_in_wrapper))
        self.process_gui.start()
        self.process_gui.join()
        print(self.process_gui.is_alive())
        print("tui killed")


if __name__ == "__main__":
    app = APP()
    app.run()
