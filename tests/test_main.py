import yaml

from src.cli import main


def config_file(tmp_path):
    path = tmp_path / "settings.yml"
    path.write_text(
        yaml.safe_dump(
            {
                "paths": {"base_dir": str(tmp_path / "profile")},
                "server": {"allowlist": ["TestPlayer"]},
            }
        )
    )
    return path


def test_cli_config_does_not_create_server(tmp_path, capsys):
    config = config_file(tmp_path)
    assert main(["--config", str(config), "config"]) == 0
    assert "47.4.23" in capsys.readouterr().out
    assert not (tmp_path / "profile").exists()


def test_cli_requires_eula(tmp_path):
    config = config_file(tmp_path)
    assert main(["--config", str(config), "init"]) == 1
    assert not (tmp_path / "profile").exists()


def test_cli_init_and_start_failure_exit(tmp_path, monkeypatch):
    config = config_file(tmp_path)
    assert main(["--config", str(config), "init", "--accept-eula"]) == 0
    monkeypatch.setattr(
        "src.minecraft_server_manager.MinecraftServerManager.start", lambda self: False
    )
    assert main(["--config", str(config), "start"]) == 1


def test_bad_config_and_restore_confirmation(tmp_path):
    assert main(["--config", str(tmp_path / "missing"), "status"]) == 1
    config = config_file(tmp_path)
    assert (
        main(
            [
                "--config",
                str(config),
                "restore",
                "save.zip",
                "--confirm-profile",
                "wrong",
            ]
        )
        == 1
    )
