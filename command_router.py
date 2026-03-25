from dataclasses import dataclass
from typing import Callable


@dataclass
class FuncArgsPair:
    function: Callable[...]
    kwargs: dict[str, str]


class CommandRouter:
    def __init__(self):
        self.commands_dict: dict[str, FuncArgsPair] = {}

    def add_command(self, command: str, function: Callable[...], args: dict[str, str]):
        self.commands_dict[command] = FuncArgsPair(function, args)

    def route(self, text: str):
        if words := text.split():
            command = words[0]
            if command in self.commands_dict:
                kwargs = self.commands_dict[command].kwargs
                if kwargs:
                    kwargs: dict[str, str] | None = self.parse_args(words, kwargs)
                    if not kwargs:
                        return False
                self.commands_dict[command].function(**kwargs)
                return True

    def parse_args(self, words, args):
        i = 1
        while i + 1 < len(words):
            if not words[i].startswith("--"):
                return None
            words[i] = words[i][2:]
            if words[i] not in args:
                return None
            args[words[i]] = words[i + 1]
            i += 2
        if i != len(words):
            return None
        return args
