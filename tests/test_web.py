"""One admin, no player website accounts, safe setup and fixed game controls."""

import threading
import time
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

from src.minecraft_server_manager import MinecraftServerManager
from src.utils.config import Config
from src.web.app import create_app

ADMIN = "a" * 43
ORIGIN = "http://127.0.0.1:8765"


def headers(token=ADMIN):
    return {
        "Authorization": f"Bearer {token}",
        "Origin": ORIGIN,
        "X-Confirm-Profile": "forge",
    }


@pytest.fixture
def web(tmp_path):
    config = Config()
    config.set("paths.base_dir", str(tmp_path / "world"))
    manager = MinecraftServerManager(config=config)
    manager.accounts.set_admin("owner", "a long admin password")
    app = create_app(manager, admin_token=ADMIN)
    with TestClient(app, base_url=ORIGIN) as client:
        yield client, manager


def test_auth_host_origin_and_surface(web):
    client, _ = web
    assert client.get("/api/status").status_code == 401
    assert client.get("/api/players").status_code == 403
    assert client.get("/", headers={"Host": "evil.example"}).status_code == 400
    assert (
        client.post(
            "/api/actions/start",
            headers={**headers(), "Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert client.post("/api/actions/start").status_code == 401
    assert client.post("/api/actions/console", headers=headers()).status_code == 404
    assert (
        client.post(
            "/api/actions/stop", headers={**headers(), "X-Confirm-Profile": "other"}
        ).status_code
        == 400
    )
    assert client.get("/api/users", headers=headers()).status_code == 404
    page = client.get("/")
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    assert page.headers["cache-control"] == "no-store"
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/other.txt").status_code == 404


def test_password_session_logout_and_rotation(web):
    client, manager = web
    payload = {"username": "owner", "password": "a long admin password"}
    assert client.post("/api/login", json=payload).status_code == 400
    login = client.post("/api/login", json=payload, headers={"Origin": ORIGIN})
    token = login.json()["token"]
    assert client.get("/api/players", headers=headers(token)).status_code == 200
    assert client.post("/api/logout", headers=headers(token)).status_code == 200
    assert client.get("/api/players", headers=headers(token)).status_code == 403
    token = client.post("/api/login", json=payload, headers={"Origin": ORIGIN}).json()[
        "token"
    ]
    manager.accounts.set_admin("newowner", "a different admin password")
    assert client.get("/api/players", headers=headers(token)).status_code == 403


def test_player_add_ban_unban_remove_without_accounts(web):
    client, manager = web
    for action in ["add", "ban", "unban", "remove"]:
        assert (
            client.post(
                "/api/players",
                json={"action": action, "minecraft": "FriendPlayer"},
                headers=headers(),
            ).status_code
            == 200
        )
    assert manager.accounts.allowlist(["FriendPlayer"]) == []
    assert "users" not in manager.accounts.read()
    result = client.get("/api/players", headers=headers())
    assert "hash" not in result.text and "password" not in result.text


def test_setup_requires_authentication_and_explicit_eula(web):
    client, manager = web
    payload = {"minecraft": "TestPlayer", "accept_eula": "true"}
    assert client.post("/api/setup", json=payload).status_code == 403
    assert (
        client.post(
            "/api/setup", json={**payload, "accept_eula": "false"}, headers=headers()
        ).status_code
        == 400
    )
    assert not manager.marker.exists()
    assert client.post("/api/setup", json=payload, headers=headers()).status_code == 200
    assert manager.marker.exists()
    assert client.post("/api/setup", json=payload, headers=headers()).status_code == 400
    assert (
        manager.compose_config()["services"]["minecraft"]["environment"]["ONLINE_MODE"]
        == "true"
    )


def test_single_operation_and_failure_redaction(web, monkeypatch):
    client, manager = web
    gate = threading.Event()
    monkeypatch.setattr(manager, "start", lambda: gate.wait(3))
    try:
        assert client.post("/api/actions/start", headers=headers()).status_code == 202
        assert client.post("/api/actions/start", headers=headers()).status_code == 409
    finally:
        gate.set()
    for _ in range(100):
        if (
            client.get("/api/status", headers=headers()).json()["operation"]["state"]
            != "working"
        ):
            break
        time.sleep(0.01)
    monkeypatch.setattr(
        manager, "backup", Mock(side_effect=RuntimeError("secret password"))
    )
    assert client.post("/api/actions/backup", headers=headers()).status_code == 202
    for _ in range(100):
        response = client.get("/api/status", headers=headers())
        if response.json()["operation"]["state"] != "working":
            break
        time.sleep(0.01)
    assert response.json()["operation"]["state"] == "failed"
    assert "secret password" not in response.text


def test_bounded_login_and_strong_bootstrap(web):
    client, _ = web
    assert (
        client.post(
            "/api/login", content="x" * 8193, headers={"Origin": ORIGIN}
        ).status_code
        == 400
    )
    for _ in range(8):
        assert (
            client.post(
                "/api/login",
                json={"username": "missing", "password": "wrong"},
                headers={"Origin": ORIGIN},
            ).status_code
            == 401
        )
    assert (
        client.post("/api/login", json={}, headers={"Origin": ORIGIN}).status_code
        == 429
    )
    with pytest.raises(ValueError):
        create_app(Mock(), admin_token="short")


def test_mod_controls_require_admin_and_stopped_backend(web, monkeypatch):
    client, manager = web
    body = {"filename": "test.jar", "enabled": "false"}
    assert client.post("/api/mods", json=body).status_code == 403
    toggle = Mock(return_value=True)
    monkeypatch.setattr(manager, "set_mod_enabled", toggle)
    assert client.post("/api/mods", json=body, headers=headers()).status_code == 200
    toggle.assert_called_once_with("test.jar", False)
    toggle.side_effect = RuntimeError("Stop the server")
    assert client.post("/api/mods", json=body, headers=headers()).status_code == 409
