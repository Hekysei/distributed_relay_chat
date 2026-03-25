import curses

from typing import Union

from client import Client


class TUI_Adapter:
    def __init__(self, stdscr: curses.window, client: Client):
        self.stdscr = stdscr
        self.client = client

        self.input_buffer = ""
        self.msg_win: curses.window
        self.input_win: curses.window

        self.is_stoped = False
        self.fresah_draw()

    def run(self):
        # curses.curs_set(1)
        # curses.use_default_colors()

        try:
            while not self.is_stoped:
                self.iter()
        except KeyboardInterrupt:
            self.is_stoped = True

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
                self.is_stoped = True
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
        self.stdscr.erase()
        self.stdscr.border()
        self.stdscr.refresh()

        self.resize_windows()
        self.update_messages()

    def backspace(self):
        if self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]
            self.update_input()

    def enter(self):
        if message := self.input_buffer.strip():
            self.input_buffer = ""
            self.update_input()
            self.client.send_message(message)

    def resize_windows(self):
        height, width = self.stdscr.getmaxyx()
        msg_height = max(1, height - 2)
        input_height = 1

        self.msg_win = curses.newwin(msg_height, width, 0, 0)
        self.input_win = curses.newwin(input_height, width, msg_height + 1, 0)
        self.msg_win.scrollok(True)
        self.input_win.scrollok(True)

    def update_messages(self):
        if not self.is_stoped:

            self.msg_win.clear()

            height, width = self.msg_win.getmaxyx()
            start_idx = max(0, len(self.client.messages) - height)
            shift = max(0, height - len(self.client.messages))

            for i, msg in enumerate(self.client.messages[start_idx:]):
                row = f"{msg.author}: {msg.text}"
                self.msg_win.addstr(shift + i, 0, row[: width - 2])
                
            self.msg_win.refresh()

            self.update_input()


    def update_input(self):
        if not self.is_stoped:
            self.input_win.clear()
            _, width = self.input_win.getmaxyx()
            self.input_win.addstr(0,0,">")
            self.input_win.addstr(0, 1, self.input_buffer[: width - 2])
            self.input_win.refresh()
