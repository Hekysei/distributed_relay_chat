from dataclasses import dataclass, asdict
from datetime import datetime
import json


# c/ - client
# r/ - room
# u/ - user


@dataclass
class Message:
    chat: str
    author: str
    text: str
    timestamp: datetime | None = None

    def set_time(self):
        self.timestamp = datetime.now()


def json_to_message(json_str: str | bytes) -> Message:
    data = json.loads(json_str)
    if data["timestamp"]:
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
    return Message(**data)


def message_to_json(msg: Message) -> str:
    data = asdict(msg)
    if data["timestamp"]:
        data["timestamp"] = data["timestamp"].isoformat()
    return json.dumps(data)
