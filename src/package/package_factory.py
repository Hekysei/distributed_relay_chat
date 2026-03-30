import json
from abc import ABC

from typing import Type, Callable

from src.package.package import Message, Package, TimestampResponse, SystemMessage


class PackageFactory(ABC):
    _classes: dict[str, Type[Package]] = {
        "message_request": Message,
        "timestamp_response": TimestampResponse,
        "system_message": SystemMessage,
    }
    _handlers: dict[str, Callable] = dict()

    def process_json(self, json_str: str | bytes):
        data = json.loads(json_str)
        pkg_type = data.get("type")

        if pkg_type not in self._handlers:
            raise ValueError(f"Неизвестный тип пакета: {pkg_type}")

        package_class: Type[Package] = self._classes[pkg_type]
        handler = self._handlers[pkg_type]
        instance = package_class.from_json(json_str)
        return handler(instance)
