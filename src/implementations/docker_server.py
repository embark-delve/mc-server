"""Profile-scoped Docker operations. No background service or network on construction."""

import contextlib
import fcntl
import hashlib
import json
import os
import re
import secrets
import tempfile
import time
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

from src.utils.accounts import Accounts
from src.utils.command_executor import CommandExecutor
from src.utils.config import Config
from src.utils.file_manager import FileManager, atomic_json
from src.utils.mod_manager import ModManager


class DockerServer:
    def __init__(
        self,
        base_dir: Path | None = None,
        minecraft_version: str = "1.20.1",
        server_type: str = "forge",
        memory: str = "4G",
        java_version: str = "java25",
        auto_shutdown_enabled: bool = False,
        auto_shutdown_timeout: int = 120,
        monitoring_enabled: bool = False,
        enable_prometheus: bool = False,
        enable_cloudwatch: bool = False,
        config: Config | None = None,
    ) -> None:
        self.config = config or Config()
        if config is None:
            for key, value in {
                "paths.base_dir": str(base_dir) if base_dir else None,
                "server.version": minecraft_version,
                "server.flavor": server_type,
                "server.memory": memory,
                "server.java_version": java_version,
                "server.image": f"itzg/minecraft-server:{java_version}",
                "auto_shutdown.enabled": auto_shutdown_enabled,
                "auto_shutdown.timeout": auto_shutdown_timeout,
                "monitoring.enabled": monitoring_enabled,
                "monitoring.prometheus": enable_prometheus,
                "monitoring.cloudwatch": enable_cloudwatch,
            }.items():
                self.config.set(key, value)
        self.config.validate()
        self.base_dir = self.config.base_dir
        self.accounts = Accounts(self.base_dir)
        self.data_dir = self.base_dir / "data"
        self.backup_dir = self.base_dir / "backups"
        self.plugins_dir = self.data_dir / "mods"
        self.config_dir = self.data_dir / "config"
        self.compose_file = self.base_dir / "compose.yaml"
        self.marker = self.base_dir / "profile.json"
        self.runtime_file = self.base_dir / "runtime.json"
        self.project = (
            "mc-"
            + self.config.get("profile")
            + "-"
            + hashlib.sha256(str(self.base_dir).encode()).hexdigest()[:10]
        )
        self.mod_manager = ModManager(
            self.config.get("server.flavor"),
            self.config.get("server.version"),
            self.plugins_dir,
        )

    def _run(self, args: list[str], timeout: float = 60, check: bool = True) -> Any:
        return CommandExecutor.run(
            args, capture_output=True, timeout=timeout, check=check
        )

    def _compose(self, *args: str, timeout: float = 60) -> Any:
        return self._run(
            [
                "docker",
                "compose",
                "--project-name",
                self.project,
                "--file",
                str(self.compose_file),
                *args,
            ],
            timeout=timeout,
        )

    @contextlib.contextmanager
    def _locked(self) -> Iterator[None]:
        if not self.base_dir.is_dir():
            raise ValueError("Profile is not initialized. Run init first")
        path = self.base_dir / ".operation.lock"
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError(
                    "Another operation is active for this profile"
                ) from exc
            for p in [
                self.data_dir,
                self.backup_dir,
                self.marker,
                self.runtime_file,
                self.compose_file,
            ]:
                if p.is_symlink():
                    raise ValueError(f"Refusing profile symlink: {p}")
            yield
        finally:
            os.close(fd)

    def initialize(self, accept_eula: bool = False) -> None:
        if not accept_eula:
            raise ValueError(
                "Read https://aka.ms/MinecraftEULA, then pass --accept-eula if you agree"
            )
        if self.base_dir in (Path("/"), Path.home(), Path.cwd()):
            raise ValueError("Choose a dedicated server profile directory")
        self.base_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self._locked():
            if self.marker.exists():
                self._verify_profile()
                return
            if any(p.name != ".operation.lock" for p in self.base_dir.iterdir()):
                raise ValueError(
                    "Initialization requires an empty dedicated directory; existing worlds need a separate migration"
                )
            if not self.accounts.allowlist(self.config.get("server.allowlist")):
                raise ValueError(
                    "Add your Minecraft username to server.allowlist before initializing"
                )
            FileManager.ensure_directories(
                [self.data_dir, self.plugins_dir, self.backup_dir]
            )
            secret = self.base_dir / "rcon.secret"
            fd = os.open(
                secret, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
            )
            with os.fdopen(fd, "w") as stream:
                stream.write(secrets.token_urlsafe(36) + "\n")
            atomic_json(
                self.marker,
                {"schema": 1, "project": self.project, "eula_accepted": True},
            )
            self._write_compose()

    def _verify_profile(self) -> None:
        if not self.marker.is_file() or self.marker.is_symlink():
            raise ValueError("Profile not initialized")
        marker = json.loads(self.marker.read_text())
        if marker != {"schema": 1, "project": self.project, "eula_accepted": True}:
            raise ValueError("Profile ownership/EULA marker mismatch")
        secret = self.base_dir / "rcon.secret"
        if not secret.is_file() or secret.is_symlink() or secret.stat().st_mode & 0o077:
            raise ValueError("RCON secret must be a private regular file (mode 600)")
        if len(secret.read_text().strip()) < 32:
            raise ValueError("RCON secret is too short")
        if not self.data_dir.is_dir() or self.data_dir.is_symlink():
            raise ValueError("Profile data directory is missing or unsafe")

    def compose_config(self) -> dict[str, Any]:
        s = self.config.get("server")
        # This is a mounted filename, not a password value.
        rcon_secret_path = str(Path("/run/secrets") / "rcon_password")
        image = s["image"]
        if self.runtime_file.exists():
            runtime = json.loads(self.runtime_file.read_text())
            image = runtime["image"]
        return {
            "services": {
                "minecraft": {
                    "image": image,
                    "ports": [
                        {
                            "target": 25565,
                            "published": str(s["port"]),
                            "host_ip": s["bind_address"],
                            "protocol": "tcp",
                        }
                    ],
                    "environment": {
                        "EULA": "TRUE",
                        "TYPE": s["flavor"].upper(),
                        "VERSION": s["version"],
                        "FORGE_VERSION": s["forge_version"],
                        "MEMORY": s["memory"],
                        "ENABLE_RCON": "true",
                        "RCON_PASSWORD_FILE": rcon_secret_path,
                        "ONLINE_MODE": "true",
                        "ENFORCE_SECURE_PROFILE": "true",
                        "ENABLE_WHITELIST": "true",
                        "ENFORCE_WHITELIST": "true",
                        "WHITELIST": ",".join(self.accounts.allowlist(s["allowlist"])),
                        "EXISTING_WHITELIST_FILE": "SYNCHRONIZE",
                        "OPS": ",".join(self._operators()),
                        "EXISTING_OPS_FILE": "SYNCHRONIZE",
                        "USER_API_PROVIDER": "mojang",
                        "MAX_PLAYERS": str(s["max_players"]),
                        "VIEW_DISTANCE": str(s["view_distance"]),
                        "SIMULATION_DISTANCE": str(s["simulation_distance"]),
                        "ENABLE_AUTOPAUSE": "false",
                        "ENABLE_AUTOSTOP": "false",
                        "UID": str(os.getuid()),
                        "GID": str(os.getgid()),
                    },
                    "volumes": [
                        {
                            "type": "bind",
                            "source": str(self.data_dir),
                            "target": "/data",
                        }
                    ],
                    "secrets": ["rcon_password"],
                    "restart": "no",
                    "mem_limit": s["container_memory"],
                    "cpus": s["cpus"],
                    "stop_grace_period": f"{s['stop_timeout']}s",
                    "logging": {
                        "driver": "json-file",
                        "options": {"max-size": "10m", "max-file": "3"},
                    },
                    "security_opt": ["no-new-privileges:true"],
                    "healthcheck": {
                        "test": ["CMD", "mc-health"],
                        "interval": "10s",
                        "timeout": "5s",
                        "retries": 6,
                        "start_period": "120s",
                    },
                }
            },
            "secrets": {"rcon_password": {"file": str(self.base_dir / "rcon.secret")}},
        }

    def _write_compose(self) -> None:
        if self.compose_file.is_symlink():
            raise ValueError("Compose file cannot be a symlink")
        fd, temp = tempfile.mkstemp(prefix=".compose-", dir=self.base_dir)
        try:
            with os.fdopen(fd, "w") as stream:
                yaml.safe_dump(self.compose_config(), stream, sort_keys=False)
            os.replace(temp, self.compose_file)
        finally:
            Path(temp).unlink(missing_ok=True)

    def _container(self) -> dict[str, Any] | None:
        result = self._run(
            [
                "docker",
                "ps",
                "-aq",
                "--filter",
                f"label=com.docker.compose.project={self.project}",
                "--filter",
                "label=com.docker.compose.service=minecraft",
            ]
        )
        ids = result.stdout.split()
        if len(ids) > 1:
            raise RuntimeError(
                "Multiple containers found for this profile; refusing ambiguous operation"
            )
        if not ids:
            return None
        info = json.loads(self._run(["docker", "inspect", ids[0]]).stdout)[0]
        labels = info.get("Config", {}).get("Labels", {})
        if (
            labels.get("com.docker.compose.project") != self.project
            or labels.get("com.docker.compose.service") != "minecraft"
        ):
            raise RuntimeError("Container ownership mismatch")
        return info

    def is_running(self) -> bool:
        info = self._container()
        return bool(info and info["State"]["Running"])

    def _runtime(self) -> dict[str, Any]:
        s = self.config.get("server")
        desired = {
            "minecraft": s["version"],
            "flavor": s["flavor"],
            "forge": s["forge_version"],
            "java": s["java_version"],
            "requested_image": s["image"],
        }
        if self.runtime_file.exists():
            saved = json.loads(self.runtime_file.read_text())
            if any(saved.get(k) != v for k, v in desired.items()):
                raise ValueError(
                    "Runtime differs from locked world; test upgrades in a new profile"
                )
            return saved
        return desired

    def _pin_image(self) -> None:
        runtime = self._runtime()
        if "image" not in runtime:
            image = runtime["requested_image"]
            self._run(
                ["docker", "pull", image],
                timeout=self.config.get("server.startup_timeout"),
            )
            found = json.loads(self._run(["docker", "image", "inspect", image]).stdout)[
                0
            ]
            digests = found.get("RepoDigests", [])
            candidates = [
                x for x in digests if x.startswith("itzg/minecraft-server@sha256:")
            ]
            if not candidates:
                raise RuntimeError("Could not lock the downloaded image digest")
            runtime["image"] = candidates[0]
            atomic_json(self.runtime_file, runtime)

    def start(self) -> bool:
        with self._locked():
            self._verify_profile()
            self._runtime()
            if not self.accounts.allowlist(self.config.get("server.allowlist")):
                raise ValueError("Set an allowlist before starting")
            info = self._container()
            if not (info and info["State"]["Running"]):
                self._prepare_access()
                self._pin_image()
                self._write_compose()
                self._compose("config", "--quiet")
                self._compose(
                    "up", "-d", timeout=self.config.get("server.startup_timeout")
                )
            deadline = time.monotonic() + self.config.get("server.startup_timeout")
            while time.monotonic() < deadline:
                info = self._container()
                if info:
                    state = info["State"]
                    if state.get("Health", {}).get("Status") == "healthy" and state.get(
                        "Running"
                    ):
                        self._sync_access(info)
                        return True
                    if state.get("Status") in ("exited", "dead"):
                        raise RuntimeError(
                            "Minecraft exited during startup; inspect logs"
                        )
                time.sleep(2)
            raise RuntimeError(
                "Minecraft did not become healthy before the deadline; inspect logs and stop if needed"
            )

    def _stop(self) -> bool:
        info = self._container()
        if info is None or not info["State"]["Running"]:
            return True
        timeout = self.config.get("server.stop_timeout")
        # RCON stops the game itself; unlike Docker stop this never force-kills after a deadline.
        self._run(["docker", "exec", info["Id"], "rcon-cli", "stop"])
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            info = self._container()
            if info is None:
                raise RuntimeError(
                    "Container disappeared during stop; save state cannot be verified"
                )
            if not info["State"]["Running"]:
                if (
                    info["State"].get("OOMKilled")
                    or info["State"].get("ExitCode", 0) != 0
                ):
                    raise RuntimeError(
                        "Server exited uncleanly; inspect logs before backup/restore"
                    )
                return True
            time.sleep(1)
        raise RuntimeError(
            "Graceful stop timed out; server was not force-killed. Backup/restore refused"
        )

    def stop(self) -> bool:
        with self._locked():
            self._verify_profile()
            return self._stop()

    def restart(self) -> bool:
        self.stop()
        return self.start()

    def execute_command(self, command: str) -> str:
        if not command.strip() or any(c in command for c in ("\n", "\r", "\x00")):
            raise ValueError("Send one nonempty console command")
        with self._locked():
            self._verify_profile()
            info = self._container()
            if not info or not info["State"]["Running"]:
                raise RuntimeError("Server is stopped")
            return str(
                self._run(["docker", "exec", info["Id"], "rcon-cli", command]).stdout
            ).strip()

    def get_status(self) -> dict[str, Any]:
        info = self._container()
        state = info["State"] if info else {}
        return {
            "profile": self.config.get("profile"),
            "state": state.get("Status", "absent"),
            "running": state.get("Running", False),
            "health": state.get("Health", {}).get("Status", "unknown"),
            "minecraft_version": self.config.get("server.version"),
            "forge_version": self.config.get("server.forge_version"),
            "java": self.config.get("server.java_version"),
            "data_directory": str(self.data_dir),
            "connection": f"{self.config.get('server.bind_address')}:{self.config.get('server.port')}",
        }

    def _operators(self) -> list[str]:
        allowed = {
            x.lower()
            for x in self.accounts.allowlist(self.config.get("server.allowlist"))
        }
        return [x for x in self.config.get("server.operators") if x.lower() in allowed]

    def _prepare_access(self) -> None:
        # Operators bypass the whitelist: revoke stale operators BEFORE starting Java.
        path = self.data_dir / "ops.json"
        if path.is_symlink():
            raise ValueError("Operator inventory cannot be a symlink")
        if path.exists():
            operators = json.loads(path.read_text())
            if not isinstance(operators, list) or any(
                not isinstance(x, dict) for x in operators
            ):
                raise ValueError("Invalid operator inventory")
            allowed = {
                name.lower()
                for name in self.accounts.allowlist(self.config.get("server.allowlist"))
            }
            atomic_json(
                path,
                [
                    entry
                    for entry in operators
                    if str(entry.get("name", "")).lower() in allowed
                ],
            )

    def _sync_access(self, info: dict[str, Any]) -> None:
        data = self.accounts.read()
        if not (
            data["allowed"] or data["removed"] or data["banned"] or self._operators()
        ):
            return

        def command(text: str) -> None:
            self._run(["docker", "exec", info["Id"], "rcon-cli", text])

        command("whitelist on")
        for name in sorted(set(data["removed"]) | set(data["banned"])):
            command(f"deop {name}")
            command(f"whitelist remove {name}")
            command(f"kick {name} Invitation revoked")
        for name in data["banned"]:
            command(f"ban {name} Access revoked by server owner")
        for name in self.accounts.allowlist(self.config.get("server.allowlist")):
            command(f"pardon {name}")
            command(f"whitelist add {name}")
        for name in self._operators():
            command(f"op {name}")
        self.verify_security()

    def change_player(self, minecraft: str, action: str) -> None:
        if not self.marker.exists():
            self.accounts.change_player(minecraft, action)
            return
        with self._locked():
            self._verify_profile()
            self.accounts.change_player(minecraft, action)
            info = self._container()
            if info and info["State"]["Running"]:
                if action == "unban":
                    self._run(
                        [
                            "docker",
                            "exec",
                            info["Id"],
                            "rcon-cli",
                            f"pardon {minecraft}",
                        ]
                    )
                self._sync_access(info)

    def verify_security(self) -> dict[str, Any]:
        """Inspect effective container settings, without returning RCON secrets."""
        info = self._container()
        if not info or not info["State"]["Running"]:
            raise RuntimeError("Start the server before checking live security")
        ports = info.get("NetworkSettings", {}).get("Ports", {})
        bindings = ports.get("25565/tcp") or []
        expected_ip = self.config.get("server.bind_address")
        if not bindings or any(
            binding.get("HostIp") != expected_ip
            or str(binding.get("HostPort")) != str(self.config.get("server.port"))
            for binding in bindings
        ):
            raise RuntimeError(
                "Game port binding differs from the approved configuration"
            )
        if any(bindings for port, bindings in ports.items() if port != "25565/tcp"):
            raise RuntimeError("An unexpected container port is published")

        def read(name: str) -> str:
            return str(
                self._run(["docker", "exec", info["Id"], "cat", f"/data/{name}"]).stdout
            )

        properties = {}
        for line in read("server.properties").splitlines():
            if "=" in line and not line.lstrip().startswith(("#", "!")):
                key, value = line.split("=", 1)
                properties[key.strip()] = value.strip()
        for key in (
            "online-mode",
            "white-list",
            "enforce-whitelist",
            "enforce-secure-profile",
        ):
            if properties.get(key) != "true":
                raise RuntimeError(f"Live security check failed: {key} must be true")
        expected = {
            name.lower()
            for name in self.accounts.allowlist(self.config.get("server.allowlist"))
        }
        allowed = json.loads(read("whitelist.json"))
        operators = json.loads(read("ops.json"))
        if not isinstance(allowed, list) or not isinstance(operators, list):
            raise RuntimeError("Invalid live access-control inventory")

        def names(entries: list[Any]) -> set[str]:
            if any(
                not isinstance(x, dict)
                or not isinstance(x.get("name"), str)
                or not isinstance(x.get("uuid"), str)
                or not x["uuid"]
                for x in entries
            ):
                raise RuntimeError("Invalid live player identity")
            return {entry["name"].lower() for entry in entries}

        if names(allowed) != expected:
            raise RuntimeError("Live allowlist differs from the approved player list")
        if not names(operators).issubset(expected):
            raise RuntimeError("An unapproved operator can bypass the allowlist")
        if not {x.lower() for x in self._operators()}.issubset(names(operators)):
            raise RuntimeError("A configured administrator is missing operator access")
        return {
            "verified": True,
            "online_mode": True,
            "allowlist_enforced": True,
            "approved_players": len(expected),
            "game_bind_address": expected_ip,
            "management_ports_published": False,
        }

    def get_logs(self, lines: int = 50) -> list[str]:
        if not 1 <= lines <= 10000:
            raise ValueError("Log line count must be between 1 and 10000")
        info = self._container()
        if info is None:
            return []
        result = self._run(["docker", "logs", "--tail", str(lines), info["Id"]])
        return (result.stdout + result.stderr).splitlines()

    def _require_stopped(self) -> None:
        info = self._container()
        if info and info["State"]["Running"]:
            raise RuntimeError(
                "Stop the server before modifying or backing up its files"
            )
        if info and (
            info["State"].get("OOMKilled") or info["State"].get("ExitCode", 0) != 0
        ):
            raise RuntimeError(
                "Last exit was unclean; recover/inspect the world before using managed backups"
            )

    def backup(self) -> Path:
        with self._locked():
            self._verify_profile()
            self._require_stopped()
            runtime = self._runtime()
            if "image" not in runtime:
                raise ValueError(
                    "Start this profile once to establish its runtime lock before a managed backup"
                )
            path, _ = FileManager.create_backup(
                self.data_dir,
                self.backup_dir,
                metadata={"runtime": runtime, "config": self.config.get_all()},
            )
            FileManager.cleanup_old_backups(
                self.backup_dir, self.config.get("backup.max_backups")
            )
            return path

    def restore(self, backup_path: Path | None = None) -> bool:
        with self._locked():
            self._verify_profile()
            self._require_stopped()
            if backup_path is None:
                raise ValueError(
                    "Specify an explicit backup path; restore never selects implicitly"
                )
            runtime = self._runtime()
            adopting_runtime = not self.runtime_file.exists()
            if adopting_runtime:
                # Only a fresh profile may adopt the exact image recorded in a backup.
                if any(p.is_file() or p.is_symlink() for p in self.data_dir.rglob("*")):
                    raise ValueError(
                        "Restore into an empty profile or one with an existing runtime lock"
                    )
                with zipfile.ZipFile(backup_path) as archive:
                    if archive.getinfo("manifest.json").file_size > 8 * 1024**2:
                        raise ValueError("Oversized manifest")
                    saved = (
                        json.loads(archive.read("manifest.json"))
                        .get("metadata", {})
                        .get("runtime", {})
                    )
                if not isinstance(saved, dict) or any(
                    saved.get(k) != v for k, v in runtime.items()
                ):
                    raise ValueError("Backup runtime does not match target settings")
                if not isinstance(saved.get("image"), str) or not re.fullmatch(
                    r"itzg/minecraft-server@sha256:[a-f0-9]{64}", saved["image"]
                ):
                    raise ValueError("Backup must record a pinned Minecraft image")
                runtime = saved
            result = FileManager.extract_backup(
                backup_path,
                self.base_dir,
                self.data_dir,
                max_bytes=self.config.get("backup.max_restore_bytes"),
                expected_runtime=runtime,
            )
            if adopting_runtime:
                atomic_json(self.runtime_file, runtime)
            return result

    def install_mod(self, mod_id: str, source: str = "modrinth") -> bool:
        return self.mod_manager.install_mod(mod_id, source)

    def install_local_mod(self, path: Path, sha256: str) -> bool:
        with self._locked():
            self._verify_profile()
            self._require_stopped()
            return self.mod_manager.install_local(path, sha256)

    def uninstall_mod(self, mod_id: str) -> bool:
        with self._locked():
            self._verify_profile()
            self._require_stopped()
            return self.mod_manager.uninstall_mod(mod_id)

    def set_mod_enabled(self, filename: str, enabled: bool) -> bool:
        with self._locked():
            self._verify_profile()
            self._require_stopped()
            return self.mod_manager.set_enabled(filename, enabled)

    def list_mods(self) -> list[dict[str, Any]]:
        return self.mod_manager.list_installed_mods()

    def configure_auto_shutdown(
        self, enabled: bool, timeout_minutes: int = 120
    ) -> None:
        if enabled:
            raise ValueError("Auto-shutdown is disabled; explicitly stop the server")

    def update_server_configuration(self, **kwargs: Any) -> None:
        raise ValueError(
            "Edit the profile YAML configuration, then restart. Runtime upgrades require a separate profile"
        )
