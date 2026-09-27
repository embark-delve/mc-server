"""One local administrator and a separate Minecraft access list."""

import contextlib
import fcntl
import hashlib
import json
import os
import re
import secrets
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from src.utils.file_manager import atomic_json


def password_hash(password: str, salt: str) -> str:
    return hashlib.scrypt(
        password.encode(),
        salt=bytes.fromhex(salt),
        n=32768,
        r=8,
        p=3,
        maxmem=64 * 1024 * 1024,
        dklen=32,
    ).hex()


class Accounts:
    """Admin authentication never creates website accounts for game players."""

    def __init__(self, base: Path) -> None:
        identity = hashlib.sha256(str(base.resolve()).encode()).hexdigest()[:20]
        self.path = base.parent / f".clubhouse-{identity}.json"

    def read(self) -> dict[str, Any]:
        if self.path.is_symlink():
            raise ValueError("Access store cannot be a symlink")
        if not self.path.exists():
            return {"admin": None, "allowed": [], "removed": [], "banned": []}
        if self.path.stat().st_mode & 0o077:
            raise ValueError("Access store must be private (mode 0600)")
        value: dict[str, Any] = json.loads(self.path.read_text())
        if "admin" not in value:
            raise ValueError("Unrecognized access store schema")
        return value

    @contextlib.contextmanager
    def edit(self) -> Iterator[dict[str, Any]]:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(
            str(self.path) + ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
        )
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            data = self.read()
            yield data
            atomic_json(self.path, data)
        finally:
            os.close(fd)

    def set_admin(self, username: str, password: str) -> None:
        username = username.lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,31}", username):
            raise ValueError(
                "Admin username must be 3–32 letters, numbers, underscores or hyphens"
            )
        if not 15 <= len(password) <= 128:
            raise ValueError("Use a unique password of 15–128 characters")
        salt = secrets.token_hex(16)
        encoded = password_hash(password, salt)
        with self.edit() as data:
            data["admin"] = {
                "username": username,
                "salt": salt,
                "hash": encoded,
                "revision": secrets.token_hex(16),
            }

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        if len(password) > 128 or len(username) > 32:
            return None
        admin = self.read()["admin"]
        encoded = password_hash(password, admin["salt"] if admin else "00" * 16)
        if (
            not admin
            or not secrets.compare_digest(encoded, admin["hash"])
            or username.lower() != admin["username"]
        ):
            return None
        return {
            "username": admin["username"],
            "role": "admin",
            "revision": admin["revision"],
        }

    def valid_session(self, username: str, revision: str) -> str | None:
        admin = self.read()["admin"]
        if admin and admin["username"] == username and admin["revision"] == revision:
            return "admin"
        return None

    def change_player(self, minecraft: str, action: str) -> None:
        if action not in {"add", "ban", "unban", "remove"} or not re.fullmatch(
            r"[A-Za-z0-9_]{3,16}", minecraft
        ):
            raise ValueError("Invalid player action or Minecraft username")
        name = minecraft.lower()
        with self.edit() as data:
            if action == "add":
                if name in data["banned"]:
                    raise ValueError("Unban this player before adding them")
                data["allowed"] = sorted(set(data["allowed"]) | {name})
                data["removed"] = [x for x in data["removed"] if x != name]
            elif action == "ban":
                data["banned"] = sorted(set(data["banned"]) | {name})
            elif action == "unban":
                data["banned"] = [x for x in data["banned"] if x != name]
            else:
                data["removed"] = sorted(set(data["removed"]) | {name})
                data["allowed"] = [x for x in data["allowed"] if x != name]

    def players(self, configured: list[str]) -> list[dict[str, str]]:
        data = self.read()
        names = {
            name.lower()
            for name in configured + data["allowed"] + data["banned"] + data["removed"]
        }
        return [
            {
                "minecraft": name,
                "status": "banned"
                if name in data["banned"]
                else "removed"
                if name in data["removed"]
                else "allowed",
            }
            for name in sorted(names)
        ]

    def allowlist(self, configured: list[str]) -> list[str]:
        data = self.read()
        denied = set(data["removed"]) | set(data["banned"])
        names = {name.lower(): name for name in configured}
        names.update({name: name for name in data["allowed"]})
        return sorted(name for lower, name in names.items() if lower not in denied)
