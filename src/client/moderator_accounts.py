from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

_ITERATIONS = 100_000

_RESERVED = frozenset({"moderator", "relay", "blank_name"})


@dataclass(frozen=True, slots=True)
class _AccountRecord:
    salt: bytes
    password_hash: bytes


class ModeratorAccountStore:
    """In-memory accounts and one active relay session per username (relay user_code)."""

    def __init__(self) -> None:
        self._accounts: dict[str, _AccountRecord] = {}
        self._active_by_username: dict[str, str] = {}
        self._username_by_relay: dict[str, str] = {}

    @staticmethod
    def _hash_password(password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            _ITERATIONS,
        )

    def is_registered(self, username: str) -> bool:
        return username in self._accounts

    def delete_account(self, username: str) -> None:
        self._accounts.pop(username.strip(), None)

    def register(self, username: str, password: str) -> tuple[bool, str]:
        name = username.strip()
        if not name:
            return False, "Set a non-empty username on the client before registering."
        if name.lower() in _RESERVED:
            return False, "This username is reserved."
        if name in self._accounts:
            return False, "Username already taken. Use /login <password>."
        salt = secrets.token_bytes(16)
        ph = self._hash_password(password, salt)
        self._accounts[name] = _AccountRecord(salt=salt, password_hash=ph)
        return True, ""

    def check_password(self, username: str, password: str) -> bool:
        rec = self._accounts.get(username)
        if rec is None:
            return False
        return secrets.compare_digest(
            rec.password_hash,
            self._hash_password(password, rec.salt),
        )

    def bind_session(self, username: str, relay_user_code: str) -> tuple[bool, str]:
        name = username.strip()
        current = self._active_by_username.get(name)
        if current is not None and current != relay_user_code:
            return (
                False,
                "This account is already in use from another client.",
            )
        self._active_by_username[name] = relay_user_code
        self._username_by_relay[relay_user_code] = name
        return True, ""

    def clear_relay_user(self, relay_user_code: str) -> str | None:
        """Drop session for this relay connection id; returns released username if any."""
        username = self._username_by_relay.pop(relay_user_code, None)
        if username is None:
            return None
        if self._active_by_username.get(username) == relay_user_code:
            del self._active_by_username[username]
        return username
