import curses
import sys
from threading import Lock

from typing import Union

from src.client.user_client import UserClient
from src.limits import MAX_MESSAGE_TEXT_LENGTH

mutex = Lock()


def _reset_tty_after_tui() -> None:
    """После curses: курсор виден, сброс атрибутов, очистка экрана (убирает «хвост» TUI)."""
    out = getattr(sys, "__stdout__", None)
    if out is None or not out.isatty():
        return
    try:
        out.write("\x1b[?25h\x1b[0m\x1b[2J\x1b[H")
        out.flush()
    except OSError:
        pass


def _wrap_message_lines(prefix: str, text: str, width: int) -> list[str]:
    """Разбивает текст сообщения на строки шириной не больше width.

    Перенос по словам (слова из body через split()). Слишком длинное слово
    обрезается; остаток слова переносится на следующие строки по width.
    """
    if width <= 0:
        return []

    words = text.split()
    lines: list[str] = []

    def take_body_line(cap: int) -> str:
        nonlocal words
        if cap <= 0:
            return ""
        parts: list[str] = []
        used = 0
        while words:
            w = words[0]
            add = len(w) if not parts else 1 + len(w)
            if used + add <= cap:
                parts.append(words.pop(0))
                used += add
            elif not parts:
                chunk = w[:cap]
                if len(w) > cap:
                    words[0] = w[cap:]
                else:
                    words.pop(0)
                return chunk
            else:
                break
        return " ".join(parts)

    first_cap = max(0, width - len(prefix))
    if len(prefix) > width:
        lines.append(prefix[:width])
        rest_prefix = prefix[width:]
        for i in range(0, len(rest_prefix), width):
            lines.append(rest_prefix[i : i + width])
        while words:
            lines.append(take_body_line(width))
        return lines

    first_body = take_body_line(first_cap)
    lines.append(prefix + first_body)
    while words:
        lines.append(take_body_line(width))
    return lines


class TUI_Adapter:
    def __init__(self, client: UserClient):
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
        try:
            try:
                curses.wrapper(self.__run_in_wrapper)
            except KeyboardInterrupt:
                self.is_stoped = True
        finally:
            try:
                curses.endwin()
            except curses.error:
                pass
            _reset_tty_after_tui()

    ### РАБОТА TUI ###
    def __run_in_wrapper(self, stdscr: curses.window):
        self.stdscr = stdscr
        try:
            self.fresah_draw()

            curses.curs_set(0)
            # curses.use_default_colors()
            while not self.is_stoped:
                self.iter()
        except KeyboardInterrupt:
            self.is_stoped = True
        finally:
            try:
                curses.curs_set(1)
            except curses.error:
                pass

    def iter(self):
        # int - специальные ключи, str - символ
        c: Union[int, str] = self.stdscr.get_wch()
        # self.client.send_text(self.active_chat, str(c))
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
                if len(self.input_buffer) < MAX_MESSAGE_TEXT_LENGTH:
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
            self.client.send_user_text(self.active_chat, text)

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

        # Внешняя высота: рамка + 2 строки ввода + рамка (см. create_window).
        inp_height = 4
        msg_height = height - inp_height

        self.bar_win = self.create_window(height, bar_width, 0, 0)
        self.msg_win = self.create_window(msg_height, msg_width, 0, bar_width)
        self.inp_win = self.create_window(inp_height, msg_width, msg_height, bar_width)

        self.stdscr.refresh()

        self.msg_win.scrollok(False)
        self.inp_win.scrollok(False)

    def update_messages(self):
        with mutex:
            if not self.is_stoped:
                self.msg_win.erase()
                height, width = self.msg_win.getmaxyx()

                i = height - 1
                for msg in reversed(self.client.chats[self.active_chat].messages):
                    timestamp = "no__time"
                    if msg.timestamp:
                        timestamp = msg.timestamp.strftime("%H:%M:%S")
                    prefix = f"[{timestamp}] {msg.sender}: "
                    for row in reversed(
                        _wrap_message_lines(prefix, msg.text, width)
                    ):
                        if i < 0:
                            break
                        self.msg_win.insstr(i, 0, row[:width])
                        i -= 1
                    if i < 0:
                        break
                self.msg_win.refresh()

    def update_input(self):
        with mutex:
            if not self.is_stoped:
                self.inp_win.erase()
                inner_height, width = self.inp_win.getmaxyx()
                if inner_height <= 0 or width <= 0:
                    self.inp_win.refresh()
                    return

                lines = _wrap_message_lines(">", self.input_buffer, width)
                if len(lines) > inner_height:
                    lines = lines[-inner_height:]
                for row, line in enumerate(lines):
                    if row >= inner_height:
                        break
                    self.inp_win.insstr(row, 0, line[:width])
                self.inp_win.refresh()

    def update_bar(self):
        with mutex:
            if not self.is_stoped:
                self.bar_win.clear()

                for i, chat in enumerate(self.client.chats.keys()):
                    self.bar_win.insstr(i, 1, chat)

                self.bar_win.addch(self.active_chat_idx, 0, ">")

                self.bar_win.refresh()
