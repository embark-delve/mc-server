"""Validated configuration; defaults < YAML < environment < explicit CLI flags."""

import copy
import ipaddress
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

DEFAULTS: dict[str, Any] = {
    "server": {
        "type": "docker",
        "flavor": "forge",
        "version": "1.20.1",
        "forge_version": "47.4.23",
        "java_version": "java25",
        "memory": "4G",
        "image": "itzg/minecraft-server:java25",
        "port": 25565,
        "bind_address": "127.0.0.1",
        "allow_lan": False,
        "eula": False,
        "allowlist": [],
        "operators": [],
        "max_players": 8,
        "view_distance": 8,
        "simulation_distance": 6,
        "container_memory": "6G",
        "cpus": 2.0,
        "startup_timeout": 600,
        "stop_timeout": 120,
    },
    "profile": "forge",
    "paths": {"base_dir": None},
    "backup": {"max_backups": 10, "max_restore_bytes": 20 * 1024**3},
    "auto_shutdown": {"enabled": False, "timeout": 120},
    "monitoring": {"enabled": False, "prometheus": False, "cloudwatch": False},
    "debug": False,
}


def memory_bytes(value: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]*[MG]", value):
        raise ValueError("Memory must be a positive integer followed by M or G")
    return int(value[:-1]) * 1024 ** (2 if value[-1] == "M" else 3)


def boolean(value: str) -> bool:
    if value.lower() not in ("true", "false", "1", "0", "yes", "no"):
        raise ValueError("Expected true or false")
    return value.lower() in ("true", "1", "yes")


class Config:
    def __init__(self) -> None:
        self._config = copy.deepcopy(DEFAULTS)

    def from_file(self, config_path: str | Path) -> "Config":
        path = Path(config_path)
        with path.open() as stream:
            data = yaml.safe_load(stream)
        if not isinstance(data, dict):
            raise ValueError("Configuration must be a YAML mapping")
        self._merge(self._config, data)
        base = self.get("paths.base_dir")
        if base is not None:
            if not isinstance(base, str):
                raise ValueError("base_dir must be a path string")
            expanded = Path(base).expanduser()
            self._config["paths"]["base_dir"] = str(
                (path.resolve().parent / expanded).resolve()
            )
        return self

    @staticmethod
    def _merge(target: dict[str, Any], data: dict[str, Any]) -> None:
        for key, value in data.items():
            if key not in target:
                raise ValueError(f"Unknown configuration key: {key}")
            if isinstance(target[key], dict):
                if not isinstance(value, dict):
                    raise ValueError(f"{key} must be a mapping")
                Config._merge(target[key], value)
            else:
                target[key] = value

    def from_env(self) -> "Config":
        fields: dict[str, tuple[str, Callable[[str], Any]]] = {
            "SERVER_TYPE": ("server.type", str),
            "SERVER_FLAVOR": ("server.flavor", str),
            "MINECRAFT_VERSION": ("server.version", str),
            "FORGE_VERSION": ("server.forge_version", str),
            "SERVER_MEMORY": ("server.memory", str),
            "BASE_DIR": ("paths.base_dir", str),
            "MC_PROFILE": ("profile", str),
            "DEBUG": ("debug", boolean),
            "AUTO_SHUTDOWN_ENABLED": ("auto_shutdown.enabled", boolean),
            "AUTO_SHUTDOWN_TIMEOUT": ("auto_shutdown.timeout", int),
            "MONITORING_ENABLED": ("monitoring.enabled", boolean),
        }
        for name, (key, convert) in fields.items():
            if name in os.environ:
                self.set(key, convert(os.environ[name]))
        return self

    def from_args(self, args: dict[str, Any]) -> "Config":
        mapping = {
            "type": "server.type",
            "version": "server.version",
            "flavor": "server.flavor",
            "memory": "server.memory",
            "timeout": "auto_shutdown.timeout",
            "debug": "debug",
            "profile": "profile",
            "base_dir": "paths.base_dir",
            "port": "server.port",
        }
        for key, dest in mapping.items():
            if args.get(key) is not None:
                self.set(dest, args[key])
        if args.get("disable_auto_shutdown") is True:
            self.set("auto_shutdown.enabled", False)
        return self

    def set(self, key: str, value: Any) -> None:
        keys = key.split(".")
        target = self._config
        for part in keys[:-1]:
            target = target[part]
        if keys[-1] not in target:
            raise ValueError(f"Unknown setting: {key}")
        target[keys[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        value: Any = self._config
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value

    def get_all(self) -> dict[str, Any]:
        return copy.deepcopy(self._config)

    def validate(self) -> "Config":
        s = self._config["server"]
        if s["type"] != "docker":
            raise ValueError(
                "Only the local Docker backend is supported; AWS/Kubernetes are disabled"
            )
        if s["flavor"] not in {"forge", "paper", "vanilla"}:
            raise ValueError("Supported flavors: forge, paper, vanilla")
        if not isinstance(s["version"], str) or not re.fullmatch(
            r"\d+(?:\.\d+){1,2}", s["version"]
        ):
            raise ValueError("Set an exact Minecraft version, not latest")
        if s["flavor"] == "forge" and (
            s["version"] != "1.20.1" or s["forge_version"] != "47.4.23"
        ):
            raise ValueError("This release supports Forge 47.4.23 on Minecraft 1.20.1")
        if s["java_version"] not in {"java17", "java21", "java25"}:
            raise ValueError("Java must be java17, java21, or java25")
        if not isinstance(s["image"], str) or not re.fullmatch(
            r"itzg/minecraft-server:(?:[0-9]+\.[0-9]+\.[0-9]+-)?java(?:17|21|25)(?:@sha256:[a-f0-9]{64})?",
            s["image"],
        ):
            raise ValueError(
                "Use a supported itzg/minecraft-server Java image tag or digest"
            )
        if s["java_version"] not in s["image"]:
            raise ValueError("Image tag and java_version disagree")
        if memory_bytes(s["container_memory"]) < memory_bytes(s["memory"]) + 1024**3:
            raise ValueError(
                "Container memory must leave at least 1 GiB beyond the Java heap"
            )
        for key, low, high in [
            ("port", 1024, 65535),
            ("max_players", 1, 100),
            ("view_distance", 2, 32),
            ("simulation_distance", 2, 32),
            ("startup_timeout", 30, 3600),
            ("stop_timeout", 30, 600),
        ]:
            if type(s[key]) is not int or not low <= s[key] <= high:
                raise ValueError(f"{key} must be an integer between {low} and {high}")
        if type(s["cpus"]) not in (int, float) or not 0.5 <= s["cpus"] <= 64:
            raise ValueError("cpus must be between 0.5 and 64")
        for key in ("eula", "allow_lan"):
            if type(s[key]) is not bool:
                raise ValueError(f"{key} must be a boolean")
        address = ipaddress.ip_address(s["bind_address"])
        if address.version != 4:
            raise ValueError("Use an IPv4 host bind address")
        if not address.is_loopback and not s["allow_lan"]:
            raise ValueError("Non-loopback networking requires allow_lan: true")
        if not isinstance(s["allowlist"], list) or any(
            not isinstance(x, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,16}", x)
            for x in s["allowlist"]
        ):
            raise ValueError("allowlist must contain Minecraft usernames")
        if not isinstance(s["operators"], list) or any(
            not isinstance(x, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,16}", x)
            for x in s["operators"]
        ):
            raise ValueError("operators must contain Minecraft usernames")
        if not {x.lower() for x in s["operators"]}.issubset(
            {x.lower() for x in s["allowlist"]}
        ):
            raise ValueError("Every configured operator must also be allowlisted")
        if not isinstance(self.get("profile"), str) or not re.fullmatch(
            r"[a-z][a-z0-9-]{0,39}", self.get("profile")
        ):
            raise ValueError(
                "Profile must be a short lowercase name with optional digits/hyphens"
            )
        for key in (
            "backup.max_backups",
            "backup.max_restore_bytes",
            "auto_shutdown.timeout",
        ):
            if type(self.get(key)) is not int or self.get(key) <= 0:
                raise ValueError(f"{key} must be a positive integer")
        for key in (
            "monitoring.enabled",
            "monitoring.prometheus",
            "monitoring.cloudwatch",
            "auto_shutdown.enabled",
            "debug",
        ):
            if type(self.get(key)) is not bool:
                raise ValueError(f"{key} must be a boolean")
        if any(
            self.get(k)
            for k in (
                "monitoring.enabled",
                "monitoring.prometheus",
                "monitoring.cloudwatch",
                "auto_shutdown.enabled",
            )
        ):
            raise ValueError(
                "Background monitoring and auto-shutdown are disabled; use explicit stop"
            )
        base = self.get("paths.base_dir")
        if base is not None and (
            not isinstance(base, (str, Path)) or not str(base).strip()
        ):
            raise ValueError("base_dir must be a nonempty path")
        if base is not None and any(c in str(base) for c in ("$", "\n", "\r")):
            raise ValueError(
                "base_dir must not contain Compose interpolation or newlines"
            )
        return self

    @property
    def base_dir(self) -> Path:
        value = self.get("paths.base_dir")
        return (
            Path(value).expanduser()
            if value
            else Path.home() / "MinecraftServers" / self.get("profile")
        ).resolve()
