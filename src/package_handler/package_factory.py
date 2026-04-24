import json

from typing import Type, Callable

from src.package.package import Message, Package, TimestampResponse, SystemMessage
from src.package_handler.package_handler import PackageHandler


TYPE_CLASS: dict[str, Type[Package]] = {
    "message_request": Message,
    "timestamp_response": TimestampResponse,
    "system_message": SystemMessage,
}


class PackageFactory:
    def __init__(self, handler: PackageHandler):
        self._handlers: dict[str, Callable] = {
            "message_request": handler.on_msg,
            "timestamp_response": handler.on_tsr,
            "system_message": handler.on_sys_msg,
        }

    def get_handler_and_instance(self, json_str: str | bytes):
        data = json.loads(json_str)
        pkg_type = data.get("type")

        if pkg_type not in self._handlers:
            raise ValueError(f"Неизвестный тип пакета: {pkg_type}")

        package_class: Type[Package] = TYPE_CLASS[pkg_type]
        return self._handlers[pkg_type], package_class.from_json(json_str)

    async def process_json(self, json_str: str | bytes):
        handler, instance = self.get_handler_and_instance(json_str)
        await handler(instance)
