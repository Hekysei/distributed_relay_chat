import json

from typing import Type, Callable

from src.package.package import Message, Package, TimestampResponse, SystemMessage


class Handler:
    @staticmethod
    def handle_message(pkg: Message):
        print(f"[Handler] Сообщение от {pkg.sender} в чат {pkg.chat}: {pkg.text}")

    @staticmethod
    def handle_timestamp(pkg: TimestampResponse):
        print(
            f"[Handler] Подтверждение получения ID {pkg.message_id} в {pkg.timestamp}"
        )

    @staticmethod
    def handle_system(pkg: SystemMessage):
        print(f"[Handler] Системное уведомление ({pkg.msg_type}): {pkg.body}")


class PackageFactory:
    _registry: dict[str, tuple[Type[Package], Callable]] = {
        "message_request": (Message, Handler.handle_message),
        "timestamp_response": (TimestampResponse, Handler.handle_timestamp),
        "system_message": (SystemMessage, Handler.handle_system),
    }

    @classmethod
    def process_json(cls, json_str: str):
        data = json.loads(json_str)
        pkg_type = data.get("type")

        if pkg_type not in cls._registry:
            raise ValueError(f"Неизвестный тип пакета: {pkg_type}")

        package_class, handler = cls._registry[pkg_type]
        instance = package_class.from_json(data)
        return handler(instance)
