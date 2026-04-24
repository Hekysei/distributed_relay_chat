from src.package.package import Message


def make_system_message(chat: str, sender: str, text: str) -> Message:
    return Message(
        chat=chat,
        sender=sender,
        text=text,
    ).set_timestamp_now()
