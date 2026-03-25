from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class Message:
    room: str
    author: str
    text: str
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


def json_to_message(json_str: str | bytes) -> Message:
    data = json.loads(json_str)
    data["timestamp"] = datetime.fromisoformat(data["timestamp"])
    return Message(**data)


def message_to_json(msg: Message) -> str:
    data = asdict(msg)
    data["timestamp"] = data["timestamp"].isoformat()
    return json.dumps(data)
