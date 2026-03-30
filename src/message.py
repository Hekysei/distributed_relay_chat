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
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str | bytes):
        data: dict = json.loads(json_str)
        class_fields = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in class_fields}
        return cls(**filtered_data)


@dataclass(kw_only=True)
class Message(Package):
    chat: str
    sender: str
    text: str
    message_id: str | None = None
    timestamp: str | None = None
    type: str = "message_request"


@dataclass(kw_only=True)
class TimestampResponse(Package):
    message_id: str
    timestamp: str
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


# @dataclass(kw_only=True)
# class Message(Package):
#     chat: str
#     text: str
#     timestamp: datetime | None = None
#     user_uuid: str | None = None
#
#     def set_time(self):
#         self.timestamp = datetime.now()
#
#     def set_user_uuid(self, uuid: str):
#         self.user_uuid = uuid
#
#
# def json_to_message(json_str: str | bytes) -> Message:
#     data = json.loads(json_str)
#     if data["timestamp"]:
#         data["timestamp"] = datetime.fromisoformat(data["timestamp"])
#     return Message(**data)
#
#
# def message_to_json(msg: Message) -> str:
#     data = asdict(msg)
#     if data["timestamp"]:
#         data["timestamp"] = data["timestamp"].isoformat()
#     return json.dumps(data)
