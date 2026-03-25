import curses

from typing import Union

from client import Client


class TUI_Adapter:
    def __init__(self, client: Client):
        self.stdscr: curses.window
        self.client = client

        self.input_buffer = ""
        self.active_chat = list(self.client.chats.keys())[0]  # первый чат
        self.active_chat_idx = 0

        self.msg_win: curses.window
        self.inp_win: curses.window
        self.bar_win: curses.window

        self.is_stoped = False

    def run(self):
        curses.wrapper(self.__run_in_wrapper)

    ### РАБОТА TUI ###
    def __run_in_wrapper(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.fresah_draw()

        curses.curs_set(0)
        # curses.use_default_colors()
        try:
            while not self.is_stoped:
                self.iter()
        except KeyboardInterrupt:
            self.is_stoped = True

    def iter(self):
        # int - специальные ключи, str - символ
        c: Union[int, str] = self.stdscr.get_wch()
        if c == "\t":
            self.step_chat()
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

    ### ОБРАБОТКА СОБЫТИЙ ###
    def backspace(self):
        if self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]
            self.update_input()

    def enter(self):
        if text := self.input_buffer.strip():
            self.input_buffer = ""
            self.update_input()
            self.client.send_text(self.active_chat, text)

    def step_chat(self, step=1):
        chats = list(self.client.chats.keys())
        self.active_chat_idx = (self.active_chat_idx + step) % len(chats)
        self.active_chat = chats[self.active_chat_idx]
        self.update_bar()
        self.update_messages()

    def handle_chat_removed(self):
        self.step_chat(0)
        self.update_bar()

    ### РАБОТА С ОКНАМИ ###
    def fresah_draw(self):
        self.stdscr.erase()
        self.stdscr.refresh()

        self.resize_windows()

        self.update_messages()
        self.update_input()
        self.update_bar()

    def create_window(self, h, w, y, x) -> curses.window:
        area = curses.newwin(h, w, y, x)
        area.border()
        area.refresh()
        return curses.newwin(h - 2, w - 2, y + 1, x + 1)

    def resize_windows(self):

        height, width = self.stdscr.getmaxyx()

        bar_width = 20
        msg_width = width - bar_width

        inp_height = 3
        msg_height = height - inp_height

        self.bar_win = self.create_window(height, bar_width, 0, 0)
        self.msg_win = self.create_window(msg_height, msg_width, 0, bar_width)
        self.inp_win = self.create_window(inp_height, msg_width, msg_height, bar_width)

        self.stdscr.refresh()

        self.msg_win.scrollok(False)
        self.inp_win.scrollok(False)

    def update_messages(self):
        if not self.is_stoped:
            self.msg_win.erase()
            height, width = self.msg_win.getmaxyx()

            i = height - 1
            for msg in reversed(self.client.chats[self.active_chat]):
                row = f"{msg.author}: {msg.text}"
                self.msg_win.insstr(i, 0, row[:width])
                i -= 1
                if i == -1:
                    break

            self.msg_win.refresh()

    def update_input(self):
        if not self.is_stoped:
            self.inp_win.erase()
            _, width = self.inp_win.getmaxyx()

            self.inp_win.insstr(0, 0, ">" + self.input_buffer[:width])
            self.inp_win.refresh()

    def update_bar(self):
        if not self.is_stoped:
            self.bar_win.clear()

            for i, chat in enumerate(self.client.chats.keys()):
                self.bar_win.insstr(i, 1, chat)

            self.bar_win.addch(self.active_chat_idx, 0, ">")

            self.bar_win.refresh()
