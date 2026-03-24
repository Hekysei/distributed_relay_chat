#!/usr/bin/env python3
import curses
from typing import Union, Callable
import threading


class Client:
    def __init__(self):
        self.messages = ["welcome"]

        self.on_got_message : Callable[[], None] = (lambda: None)

    def add_message(self, message: str):
        self.messages.append(message)
        self.on_got_message()

class CLI_Adapter:
    def __init__(self, client: Client):
        self.client: Client = client

        self.input_buffer = ""
        self.stdscr: curses.window
        self.msg_win: curses.window
        self.input_win: curses.window
        self.is_running = False

    def run(self, stdscr: curses.window):
        self.stdscr = stdscr
        curses.curs_set(1)
        curses.use_default_colors()

        self.fresah_draw()

        self.is_running = True
        while self.is_running:
            self.iter()

    def iter(self):
        # int - специальные ключи, str - символ
        c: Union[int, str] = self.stdscr.get_wch()

        if isinstance(c, int):
            if c == curses.KEY_RESIZE:
                self.fresah_draw()
            elif c in (curses.KEY_BACKSPACE, 127):
                self.backspace()
        else:
            if c == "\x1b":
                # ESC
                self.is_running = False
            elif c in ("\n", "\r") or c == curses.KEY_ENTER:
                # Enter
                self.enter()
            elif c in ("\x7f", "\b"):
                # Иногда может прилетать такой backspace
                self.backspace()
            elif c.isprintable() or c.isalpha():
                # Если символ можно напечатать или он есть в алфавите
                self.input_buffer += c
                self.update_input()

    def fresah_draw(self):
        self.stdscr.clear()
        self.stdscr.border()
        self.stdscr.refresh()

        self.resize_windows()
        self.update_messages()
        self.update_input()

    def backspace(self):
        if self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]
            self.update_input()

    def enter(self):
        if message := self.input_buffer.strip():
            self.client.add_message(message)
            self.input_buffer = ""
            self.update_input()


    def resize_windows(self):
        height, width = self.stdscr.getmaxyx()
        msg_height = max(1, height - 2)
        input_height = 1

        self.msg_win = curses.newwin(msg_height, width, 0, 0)
        self.input_win = curses.newwin(input_height, width, msg_height + 1, 0)
        self.msg_win.scrollok(True)
        self.input_win.scrollok(True)

    def update_messages(self):
        self.msg_win.clear()

        height, width = self.msg_win.getmaxyx()
        start_idx = max(0, len(self.client.messages) - height)
        shift = max(0, height - len(self.client.messages))

        for i, msg in enumerate(self.client.messages[start_idx:]):
            self.msg_win.addstr(shift + i, 0, msg[: width - 1])
        self.msg_win.refresh()

    def update_input(self):
        self.input_win.clear()
        _, width = self.input_win.getmaxyx()
        self.input_win.addstr(0, 0, self.input_buffer[: width - 1])
        self.input_win.refresh()


class APP:
    def __init__(self):
        self.client = Client()
        self.cli_adapter = CLI_Adapter(self.client)

        self.client.on_got_message = self.cli_adapter.update_messages

    def run(self):
        self.process_gui = threading.Thread(target=curses.wrapper(self.cli_adapter.run))
        self.process_gui.start()


if __name__ == "__main__":
    app = APP()
    app.run()
