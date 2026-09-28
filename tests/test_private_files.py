"""Private files must stay blocked even when force-added to Git."""

import sys

import pytest

from scripts.check_private_files import main


@pytest.mark.parametrize(
    "name",
    [
        ".env",
        ".env.local",
        ".clubhouse-123.json",
        "nested/rcon.secret",
        "config.local.yml",
        "data/world/level.dat",
        "tls/server.key",
        ".specstory/history/chat.md",
    ],
)
def test_reject_private_files(monkeypatch, name):
    monkeypatch.setattr(sys, "argv", ["check", name])
    assert main() == 1


@pytest.mark.parametrize(
    "name", [".env.example", "config.yml", "src/web/app.py", "docs/admin-guide.md"]
)
def test_allow_source_and_templates(monkeypatch, name):
    monkeypatch.setattr(sys, "argv", ["check", name])
    assert main() == 0
