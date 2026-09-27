import json

import pytest

from src.utils.accounts import Accounts


@pytest.fixture
def accounts(tmp_path):
    store = Accounts(tmp_path / "world")
    store.set_admin("owner", "a unique test password")
    return store


def test_one_admin_private_password_and_session_rotation(accounts):
    assert "a unique test password" not in accounts.path.read_text()
    assert accounts.path.stat().st_mode & 0o777 == 0o600
    session = accounts.authenticate("Owner", "a unique test password")
    assert session["role"] == "admin"
    assert accounts.authenticate("owner", "incorrect") is None
    assert accounts.authenticate("missing", "incorrect") is None
    accounts.set_admin("newowner", "another unique test password")
    assert accounts.valid_session("owner", session["revision"]) is None
    assert accounts.authenticate("owner", "a unique test password") is None
    assert accounts.authenticate("newowner", "another unique test password")


def test_player_access_does_not_create_website_accounts(accounts):
    accounts.change_player("AlexPlayer", "add")
    assert accounts.allowlist([]) == ["alexplayer"]
    assert accounts.read()["admin"]["username"] == "owner"
    assert "users" not in accounts.read()
    accounts.change_player("AlexPlayer", "ban")
    assert accounts.allowlist(["AlexPlayer"]) == []
    accounts.change_player("AlexPlayer", "unban")
    assert accounts.allowlist([]) == ["alexplayer"]
    accounts.change_player("AlexPlayer", "remove")
    assert accounts.allowlist(["AlexPlayer"]) == []
    accounts.change_player("AlexPlayer", "add")
    assert accounts.allowlist([]) == ["alexplayer"]
    assert "hash" not in json.dumps(accounts.players([]))


def test_configured_revocation_is_durable(accounts):
    accounts.change_player("OwnerPlayer", "remove")
    fresh = Accounts(accounts.path.parent / "world")
    assert fresh.allowlist(["OwnerPlayer"]) == []


@pytest.mark.parametrize(
    "name,password", [("ab", "a unique test password"), ("valid", "short")]
)
def test_bad_admin_credentials(accounts, name, password):
    with pytest.raises(ValueError):
        accounts.set_admin(name, password)


def test_player_validation_and_symlink(accounts, tmp_path):
    with pytest.raises(ValueError):
        accounts.change_player("bad;op", "add")
    accounts.path.unlink()
    target = tmp_path / "valuable"
    target.write_text("keep")
    accounts.path.symlink_to(target)
    with pytest.raises(ValueError):
        accounts.read()
