from abc import ABC
from typing import Callable

from src.package.package import Message

class DispatcherInterface(ABC):
    users_funs: dict[str, Callable[[Message]]]

    async def broadcast(self, msg: Message):
        pass
