#!/usr/bin/env python3

from tui_adapter import TUI_Adapter


class APP:
    def __init__(self):
        self.tui_adapter = TUI_Adapter()


    def run(self):
        self.tui_adapter.run()


if __name__ == "__main__":
    app = APP()
    app.run()
