from dataclasses import dataclass, asdict, fields
from abc import ABC
from datetime import datetime
import json


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
    message_id: int | None = None
    timestamp: datetime | None = None
    type: str = "message_request"

    def set_timestamp_now(self):
        self.timestamp = datetime.now()
        return self


@dataclass(kw_only=True)
class TimestampResponse(Package):
    message_id: int
    timestamp: datetime
    type: str = "timestamp_response"

    @classmethod
    def from_message(cls, msg: Message):
        if msg.timestamp is None or msg.message_id is None:
            raise ValueError("В сообщении нет времени или id")
        return cls(message_id=msg.message_id, timestamp=msg.timestamp)


@dataclass(kw_only=True)
class SystemMessage(Package):
    msg_type: str
    body: str
    type: str = "system_message"
