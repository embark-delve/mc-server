from pathlib import Path

import pytest
import yaml

from src.utils.config import Config


def test_checked_in_config():
    config = Config().from_file("config.yml").validate()
    assert config.get("server.type") == "docker"
    assert config.get("server.version") == "1.20.1"
    assert config.get("server.forge_version") == "47.4.23"
    assert config.get("server.java_version") == "java25"
    assert config.get("auto_shutdown.enabled") is False


def test_precedence_and_omitted_flags(tmp_path, monkeypatch):
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({"server": {"memory": "2G"}, "debug": True}))
    monkeypatch.setenv("SERVER_MEMORY", "3G")
    config = (
        Config()
        .from_file(path)
        .from_env()
        .from_args({"memory": "4G", "debug": None, "disable_auto_shutdown": False})
    )
    assert config.get("server.memory") == "4G"
    assert config.get("debug") is True
    assert config.get("auto_shutdown.enabled") is False


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("server.type", "aws"),
        ("server.memory", "-2G"),
        ("server.memory", 2),
        ("server.port", True),
        ("server.port", 65536),
        ("server.version", "latest"),
        ("server.allowlist", ["bad;name"]),
        ("server.allow_lan", "false"),
        ("server.image", "evil/image:java25"),
        ("server.bind_address", "0.0.0.0"),
        ("profile", "../outside"),
        ("backup.max_backups", 0),
        ("monitoring.enabled", True),
        ("server.container_memory", "4G"),
        ("server.forge_version", "47.4.0"),
    ],
)
def test_invalid_settings(key, value):
    c = Config()
    c.set(key, value)
    with pytest.raises((ValueError, TypeError)):
        c.validate()


def test_path_relative_to_configuration(tmp_path):
    path = tmp_path / "config.yml"
    path.write_text("paths:\n  base_dir: profile\n")
    assert Config().from_file(path).base_dir == tmp_path / "profile"


@pytest.mark.parametrize(
    "content", ["[]", "typo: true", "server: 2", "server:\n  unknown: 4"]
)
def test_invalid_yaml_schema(tmp_path, content):
    path = tmp_path / "config.yml"
    path.write_text(content)
    with pytest.raises(ValueError):
        Config().from_file(path)


def test_copy_not_mutable():
    c = Config()
    result = c.get_all()
    result["server"]["type"] = "aws"
    assert c.get("server.type") == "docker"
    assert isinstance(c.base_dir, Path)
