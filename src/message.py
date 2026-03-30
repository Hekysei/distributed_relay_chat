from dataclasses import dataclass, asdict, fields
from abc import ABC
from datetime import datetime
import json

from typing import Any, Type, Callable

# c/ - client
# r/ - relay
# u/ - user
# e/ - erroe


@dataclass(kw_only=True)
class Package(ABC):
    type: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, json_str: str | bytes):
        data: dict = json.loads(json_str)
        class_fields = {f.name: f for f in fields(cls)}

        filtered_data = {}
        for key, value in data.items():
            if key in class_fields:
                field_info = class_fields[key]

                if field_info.type == (datetime | None) or field_info.type == datetime:
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value)

                filtered_data[key] = value

        return cls(**filtered_data)


@dataclass(kw_only=True)
class Message(Package):
    chat: str
    sender: str
    text: str
    message_id: str | None = None
    timestamp: datetime | None = None
    type: str = "message_request"


@dataclass(kw_only=True)
class TimestampResponse(Package):
    message_id: str
    timestamp: datetime
    type: str = "timestamp_response"


@dataclass(kw_only=True)
class SystemMessage(Package):
    msg_type: str
    body: str
    type: str = "system_message"


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
