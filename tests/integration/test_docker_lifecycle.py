"""Opt-in disposable-world acceptance test; never uses the configured real profile."""

import os
import shutil
import socket
from pathlib import Path

import pytest

from src.implementations.docker_server import DockerServer
from src.utils.config import Config

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("MC_INTEGRATION_EULA") != "accepted"
        or not os.environ.get("MC_TEST_USERNAME")
        or not shutil.which("docker"),
        reason="Requires Docker, MC_TEST_USERNAME, and explicit MC_INTEGRATION_EULA=accepted",
    ),
]


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def profile(root: Path, name: str):
    c = Config()
    c.set("profile", name)
    c.set("paths.base_dir", str(root / name))
    c.set("server.port", free_port())
    c.set("server.allowlist", [os.environ["MC_TEST_USERNAME"]])
    server = DockerServer(config=c)
    server.initialize(accept_eula=True)
    return server


def test_forge_start_save_backup_restore(tmp_path):
    server = profile(tmp_path, "integration-source")
    restored = profile(tmp_path, "integration-restored")
    try:
        assert server.start()
        assert server.get_status()["health"] == "healthy"
        assert server.verify_security()["verified"] is True
        assert "players" in server.execute_command("list").lower()
        server.execute_command("scoreboard objectives add restorecheck dummy")
        written = server.execute_command(
            "scoreboard players set checkpoint restorecheck 42"
        )
        assert "42" in written, written
        server.execute_command("save-all flush")
        assert server.stop()
        backup = server.backup()
        assert restored.restore(backup)
        assert restored.start()
        assert restored.verify_security()["verified"] is True
        response = restored.execute_command(
            "scoreboard players get checkpoint restorecheck"
        )
        assert "42" in response, response
        assert restored.stop()
    finally:
        # Explicitly scoped disposable containers only. Never targets a real profile.
        for candidate in (server, restored):
            candidate._compose("down", "--timeout", "120", timeout=150)
