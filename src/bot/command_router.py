from dataclasses import dataclass
from typing import Callable


@dataclass
class FuncArgsPair:
    function: Callable
    kwargs: dict[str, str]


class CommandRouter:
    def __init__(self):
        self.commands_dict: dict[str, FuncArgsPair] = {}

    def add_command(self, command: str, function: Callable, args: dict[str, str]):
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
        words = text.split()
        if not words:
            return None
        pair = self.commands_dict.get(words[0])
        if not pair:
            return None
        kwargs = pair.kwargs.copy()
        if kwargs:
            kwargs = self.parse_args(words, kwargs)
            if not kwargs:
                return None
        return pair.function, kwargs

    def parse_args(self, words, args):
        positional_values = words[1:]
        if len(positional_values) > len(args):
            return None
        for key, value in zip(args.keys(), positional_values):
            args[key] = value
        return args
