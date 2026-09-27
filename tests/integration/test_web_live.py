"""Real CLI + HTTP smoke test on a disposable profile; never starts Minecraft."""

import os
import socket
import subprocess
import sys
import time

import httpx
import pytest
import yaml

pytestmark = pytest.mark.skipif(
    os.environ.get("MC_WEB_INTEGRATION") != "1",
    reason="Set MC_WEB_INTEGRATION=1 to bind a disposable loopback HTTP server",
)


def test_live_cli_and_authenticated_web(tmp_path):
    config = tmp_path / "config.yml"
    config.write_text(yaml.safe_dump({"paths": {"base_dir": str(tmp_path / "world")}}))
    prefix = [sys.executable, "-m", "src.cli", "--config", str(config)]

    def cli(*args, password=None):
        return subprocess.run(  # noqa: S603 - fixed local CLI and test arguments
            prefix + list(args),
            input=password,
            text=True,
            capture_output=True,
            timeout=20,
            check=True,
        )

    cli("admin", "owner", "--password-stdin", password="temporary owner password\n")
    cli("players", "add", "FriendPlayer")
    assert "friendplayer" in cli("players", "list").stdout
    cli("players", "ban", "FriendPlayer")
    assert "banned" in cli("players", "list").stdout
    cli("players", "unban", "FriendPlayer")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen(  # noqa: S603 - fixed local CLI and test arguments
        prefix + ["web", "--ui-port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    origin = f"http://127.0.0.1:{port}"
    try:
        with httpx.Client(base_url=origin, timeout=5, trust_env=False) as client:
            for _ in range(100):
                try:
                    if client.get("/").status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                time.sleep(0.1)
            else:
                pytest.fail("Dashboard did not start")
            assert client.get("/api/status").status_code == 401
            assert client.get("/", headers={"Host": "evil.example"}).status_code == 400
            login = client.post(
                "/api/login",
                headers={"Origin": origin},
                json={"username": "owner", "password": "temporary owner password"},
            )
            assert login.status_code == 200
            adult = {
                "Authorization": f"Bearer {login.json()['token']}",
                "Origin": origin,
                "X-Confirm-Profile": "forge",
            }
            assert client.get("/api/players").status_code == 403
            assert (
                client.post(
                    "/api/players",
                    headers={**adult, "Origin": "https://evil.example"},
                    json={"action": "add", "minecraft": "OtherPlayer"},
                ).status_code
                == 400
            )
            for action in ["add", "ban", "unban", "remove"]:
                assert (
                    client.post(
                        "/api/players",
                        headers=adult,
                        json={"action": action, "minecraft": "FriendPlayer"},
                    ).status_code
                    == 200
                )
            assert "removed" in cli("players", "list").stdout
            assert client.get("/api/users", headers=adult).status_code == 404
            assert client.post("/api/logout", headers=adult).status_code == 200
            assert client.get("/api/status", headers=adult).status_code == 401
    finally:
        process.terminate()
        process.wait(timeout=15)
