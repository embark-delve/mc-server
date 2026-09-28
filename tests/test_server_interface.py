import json
from subprocess import CompletedProcess
from unittest.mock import Mock

import pytest

from src.implementations.aws_server import AWSServer
from src.implementations.docker_server import DockerServer
from src.utils.config import Config


@pytest.fixture
def server(tmp_path):
    c = Config()
    c.set("paths.base_dir", str(tmp_path / "profile"))
    c.set("server.allowlist", ["TestPlayer"])
    result = DockerServer(config=c)
    result.initialize(accept_eula=True)
    return result


def state(running=True, health="healthy", code=0):
    return {
        "Id": "container-id",
        "State": {
            "Running": running,
            "Health": {"Status": health},
            "Status": "running" if running else "exited",
            "ExitCode": code,
        },
    }


def test_construct_no_side_effects(tmp_path):
    first = DockerServer(base_dir=tmp_path / "one")
    second = DockerServer(base_dir=tmp_path / "two")
    assert not first.base_dir.exists()
    assert first.project != second.project


def test_init_requires_empty_directory(tmp_path):
    root = tmp_path / "profile"
    root.mkdir()
    (root / "valuable").write_text("keep")
    instance = DockerServer(base_dir=root)
    with pytest.raises(ValueError, match="empty"):
        instance.initialize(True)
    assert (root / "valuable").read_text() == "keep"


def test_compose_security_and_paths(server):
    data = server.compose_config()
    service = data["services"]["minecraft"]
    assert service["ports"][0]["host_ip"] == "127.0.0.1"
    assert service["ports"][0]["target"] == 25565
    assert len(service["ports"]) == 1
    assert service["environment"]["FORGE_VERSION"] == "47.4.23"
    assert service["environment"]["ONLINE_MODE"] == "true"
    assert "RCON_PASSWORD" not in service["environment"]
    assert service["environment"]["MEMORY"] == "4G"
    assert service["mem_limit"] == "6G"
    assert service["volumes"][0]["source"] == str(server.data_dir)
    assert service["restart"] == "no"
    assert (server.base_dir / "rcon.secret").stat().st_mode & 0o777 == 0o600
    assert (server.base_dir / "rcon.secret").read_text().strip() not in json.dumps(data)


def test_start_waits_for_healthy(server, monkeypatch):
    poll = Mock(
        side_effect=[state(health="starting"), state(health="starting"), state()]
    )
    monkeypatch.setattr(server, "_container", poll)
    monkeypatch.setattr("src.implementations.docker_server.time.sleep", lambda _: None)
    assert server.start()
    assert poll.call_count == 3


def test_graceful_stop_verifies_exit(server, monkeypatch):
    poll = Mock(side_effect=[state(), state(False)])
    run = Mock()
    monkeypatch.setattr(server, "_container", poll)
    monkeypatch.setattr(server, "_run", run)
    assert server.stop()
    assert run.call_args.args[0] == [
        "docker",
        "exec",
        "container-id",
        "rcon-cli",
        "stop",
    ]


def test_stop_timeout_no_force_kill(server, monkeypatch):
    run = Mock()
    monkeypatch.setattr(server, "_container", lambda: state())
    monkeypatch.setattr(server, "_run", run)
    monkeypatch.setattr(
        "src.implementations.docker_server.time.monotonic", Mock(side_effect=[0, 121])
    )
    with pytest.raises(RuntimeError, match="not force-killed"):
        server.stop()
    assert run.call_count == 1


def test_docker_failure_not_stopped(server, monkeypatch):
    monkeypatch.setattr(
        server, "_run", Mock(side_effect=RuntimeError("Docker unavailable"))
    )
    with pytest.raises(RuntimeError, match="unavailable"):
        server.is_running()


@pytest.mark.parametrize(
    "operation", ["backup", "restore", "install_local_mod", "uninstall_mod"]
)
def test_running_server_refuses_file_changes(server, monkeypatch, operation):
    monkeypatch.setattr(server, "_container", lambda: state())
    args = {
        "backup": [],
        "restore": [server.base_dir / "save.zip"],
        "install_local_mod": [server.base_dir / "mod.jar", "0" * 64],
        "uninstall_mod": ["mod.jar"],
    }
    with pytest.raises(RuntimeError, match="Stop the server"):
        getattr(server, operation)(*args[operation])


def test_console_argv_no_shell(server, monkeypatch):
    run = Mock(return_value=CompletedProcess([], 0, "ok", ""))
    monkeypatch.setattr(server, "_container", lambda: state())
    monkeypatch.setattr(server, "_run", run)
    text = "say hi; echo not-a-shell"
    assert server.execute_command(text) == "ok"
    assert run.call_args.args[0][-1] == text


def test_foreign_container_rejected(server, monkeypatch):
    run = Mock(
        side_effect=[
            CompletedProcess([], 0, "abc", ""),
            CompletedProcess([], 0, json.dumps([{"Config": {"Labels": {}}}]), ""),
        ]
    )
    monkeypatch.setattr(server, "_run", run)
    with pytest.raises(RuntimeError, match="ownership"):
        server.is_running()


def test_lock_and_symlink_guard(server, tmp_path):
    with server._locked(), pytest.raises(RuntimeError, match="Another operation"):
        with server._locked():
            pass
    server.runtime_file.symlink_to(tmp_path / "elsewhere")
    with pytest.raises(ValueError, match="symlink"):
        with server._locked():
            pass


def test_cloud_is_disabled():
    with pytest.raises(NotImplementedError):
        AWSServer()


def test_image_pin_persists_and_detects_runtime_change(server, monkeypatch):
    image = "itzg/minecraft-server@sha256:" + "a" * 64
    run = Mock(
        side_effect=[
            CompletedProcess([], 0, "", ""),
            CompletedProcess([], 0, json.dumps([{"RepoDigests": [image]}]), ""),
        ]
    )
    monkeypatch.setattr(server, "_run", run)
    server._pin_image()
    assert server.compose_config()["services"]["minecraft"]["image"] == image
    server._pin_image()
    assert run.call_count == 2
    server.config.set("server.java_version", "java21")
    with pytest.raises(ValueError, match="Runtime differs"):
        server._runtime()


def test_stopped_profile_backup_and_fresh_restore(server, monkeypatch, tmp_path):
    from src.utils.file_manager import atomic_json

    monkeypatch.setattr(server, "_container", lambda: None)
    runtime = server._runtime()
    runtime["image"] = "itzg/minecraft-server@sha256:" + "a" * 64
    atomic_json(server.runtime_file, runtime)
    (server.data_dir / "world.dat").write_bytes(b"world")
    archive = server.backup()
    config = Config()
    config.set("paths.base_dir", str(tmp_path / "restore-target"))
    config.set("profile", "restored")
    config.set("server.allowlist", ["TestPlayer"])
    other = DockerServer(config=config)
    other.initialize(True)
    monkeypatch.setattr(other, "_container", lambda: None)
    assert other.restore(archive)
    assert (other.data_dir / "world.dat").read_bytes() == b"world"
    assert other._runtime() == runtime
    assert (server.data_dir / "world.dat").read_bytes() == b"world"


def test_full_start_generates_profile_compose(server, monkeypatch):
    from src.utils.file_manager import atomic_json

    runtime = server._runtime()
    runtime["image"] = "itzg/minecraft-server@sha256:" + "a" * 64
    atomic_json(server.runtime_file, runtime)
    monkeypatch.setattr(server, "_container", Mock(side_effect=[None, state()]))
    compose = Mock()
    monkeypatch.setattr(server, "_compose", compose)
    assert server.start()
    assert compose.call_args_list[0].args == ("config", "--quiet")
    assert compose.call_args_list[1].args == ("up", "-d")


def test_start_deadline_failure(server, monkeypatch):
    monkeypatch.setattr(server, "_container", lambda: state(health="starting"))
    monkeypatch.setattr(
        "src.implementations.docker_server.time.monotonic", Mock(side_effect=[0, 601])
    )
    with pytest.raises(RuntimeError, match="healthy"):
        server.start()


def live_security(
    server, monkeypatch, *, properties=None, allowed=None, ops=None, ports=None
):
    info = state()
    info["NetworkSettings"] = {
        "Ports": ports
        if ports is not None
        else {
            "25565/tcp": [{"HostIp": "127.0.0.1", "HostPort": "25565"}],
            "25575/tcp": None,
        }
    }
    monkeypatch.setattr(server, "_container", lambda: info)
    props = "online-mode=true\nwhite-list=true\nenforce-whitelist=true\nenforce-secure-profile=true\nrcon.password=do-not-return"
    files = {
        "server.properties": properties if properties is not None else props,
        "whitelist.json": json.dumps(
            allowed
            if allowed is not None
            else [{"name": "TestPlayer", "uuid": "test-uuid"}]
        ),
        "ops.json": json.dumps(ops if ops is not None else []),
    }
    monkeypatch.setattr(
        server,
        "_run",
        lambda argv: CompletedProcess(argv, 0, files[argv[-1].split("/")[-1]], ""),
    )


def test_live_security_matches_approved_access(server, monkeypatch):
    live_security(server, monkeypatch)
    result = server.verify_security()
    assert result["verified"] is True
    assert "do-not-return" not in json.dumps(result)


@pytest.mark.parametrize(
    "override",
    [
        {"properties": "online-mode=false\nwhite-list=true"},
        {"properties": "online-mode=true\nwhite-list=false"},
        {"allowed": []},
        {"allowed": [{"name": "Stranger", "uuid": "other"}]},
        {"ops": [{"name": "Stranger", "uuid": "other"}]},
        {"ports": {"25565/tcp": [{"HostIp": "0.0.0.0", "HostPort": "25565"}]}},
        {
            "ports": {
                "25565/tcp": [{"HostIp": "127.0.0.1", "HostPort": "25565"}],
                "25575/tcp": [{"HostIp": "0.0.0.0", "HostPort": "25575"}],
            }
        },
    ],
)
def test_live_security_rejects_authentication_drift(server, monkeypatch, override):
    live_security(server, monkeypatch, **override)
    with pytest.raises(RuntimeError):
        server.verify_security()


def test_revoking_player_is_persistent_and_kicks_running_player(server, monkeypatch):
    server.accounts.change_player("ChildPlayer", "add")
    calls = []
    monkeypatch.setattr(server, "_container", lambda: state())
    monkeypatch.setattr(server, "_run", lambda args: calls.append(args[-1]))
    monkeypatch.setattr(server, "verify_security", lambda: {"verified": True})
    server.change_player("ChildPlayer", "ban")
    assert "deop childplayer" in calls
    assert "whitelist remove childplayer" in calls
    assert "kick childplayer Invitation revoked" in calls
    assert "ban childplayer Access revoked by server owner" in calls
    assert "ChildPlayer" not in server.accounts.allowlist([])


def test_offline_revocation_strips_operator_before_start(server):
    server.accounts.change_player("Stranger", "remove")
    path = server.data_dir / "ops.json"
    path.write_text(
        json.dumps(
            [
                {"name": "Stranger", "uuid": "bad"},
                {"name": "TestPlayer", "uuid": "good"},
            ]
        )
    )
    server._prepare_access()
    assert json.loads(path.read_text()) == [{"name": "TestPlayer", "uuid": "good"}]


def test_failed_game_revocation_is_not_reported_as_success(server, monkeypatch):
    server.accounts.change_player("ChildPlayer", "add")
    monkeypatch.setattr(server, "_container", lambda: state())
    monkeypatch.setattr(server, "_run", Mock(side_effect=RuntimeError("Docker failed")))
    with pytest.raises(RuntimeError):
        server.change_player("ChildPlayer", "ban")
    assert server.accounts.allowlist([]) == []


def test_configured_admins_are_filtered_when_banned(server):
    server.config.set("server.operators", ["TestPlayer"])
    assert (
        server.compose_config()["services"]["minecraft"]["environment"]["OPS"]
        == "TestPlayer"
    )
    server.accounts.change_player("TestPlayer", "ban")
    assert server.compose_config()["services"]["minecraft"]["environment"]["OPS"] == ""


def test_running_game_cannot_toggle_mods(server, monkeypatch):
    monkeypatch.setattr(server, "_container", lambda: state())
    with pytest.raises(RuntimeError, match="Stop the server"):
        server.set_mod_enabled("test.jar", False)
