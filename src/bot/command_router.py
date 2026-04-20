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

    def route(self, text: str, *args):
        res = self.get_func_kwargs(text)
        if not res:
            return False
        res[0](*args, **res[1])
        return True

    async def async_route(self, text: str, *args):
        res = self.get_func_kwargs(text)
        if not res:
            return False
        await res[0](*args, **res[1])
        return True

    def get_func_kwargs(self, text: str):
        if words := text.split():
            command = words[0]
            if command in self.commands_dict:
                kwargs = self.commands_dict[command].kwargs.copy()
                if kwargs:
                    kwargs: dict[str, str] | None = self.parse_args(words, kwargs)
                    if not kwargs:
                        return None
                return self.commands_dict[command].function, kwargs

    def parse_args(self, words, args):
        # Support shorthand positional format: /command value1 value2
        positional_values = words[1:]
        if positional_values and not any(word.startswith("--") for word in positional_values):
            if len(positional_values) != len(args):
                return None
            for key, value in zip(args.keys(), positional_values):
                args[key] = value
            return args

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
