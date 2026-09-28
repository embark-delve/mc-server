import zipfile

import pytest

from src.utils.file_manager import digest
from src.utils.mod_manager import ModManager


def jar(path, content='modLoader="javafml"\nloaderVersion="[47,)"\nlicense="MIT"\n'):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("META-INF/mods.toml", content)
    return path


def test_verified_install_and_uninstall(tmp_path):
    manager = ModManager("forge", "1.20.1", tmp_path / "mods")
    source = jar(tmp_path / "mod.jar")
    assert manager.install_local(source, digest(source))
    assert manager.list_installed_mods()[0]["sha256"] == digest(source)
    assert manager.uninstall_mod("mod.jar")
    assert manager.list_installed_mods() == []


def test_bad_hash_and_client_mod_rejected(tmp_path):
    manager = ModManager("forge", "1.20.1", tmp_path / "mods")
    source = jar(tmp_path / "mod.jar")
    with pytest.raises(ValueError, match="mismatch"):
        manager.install_local(source, "0" * 64)
    jar(source, "clientSideOnly=true\n")
    with pytest.raises(ValueError, match="Client-only"):
        manager.install_local(source, digest(source))


def test_no_fake_download_or_path_escape(tmp_path):
    manager = ModManager("forge", "1.20.1", tmp_path / "mods")
    with pytest.raises(ValueError, match="disabled"):
        manager.install_mod("foo")
    with pytest.raises(ValueError):
        manager.uninstall_mod("../outside.jar")
    assert not (tmp_path / "mods").exists()


def test_mod_enabled_by_default_and_reversible_toggle(tmp_path):
    manager = ModManager("forge", "1.20.1", tmp_path / "mods")
    source = jar(tmp_path / "test.jar")
    manager.install_local(source, digest(source))
    assert manager.list_installed_mods()[0]["enabled"] is True
    manager.set_enabled("test.jar", False)
    disabled = manager.list_installed_mods()[0]
    assert disabled["enabled"] is False
    assert disabled["sha256"] == digest(source)
    assert not (manager.mods_dir / "test.jar").exists()
    manager.set_enabled("test.jar", True)
    assert manager.list_installed_mods()[0]["enabled"] is True
    with pytest.raises(ValueError):
        manager.set_enabled("../test.jar", False)


def test_mod_toggle_rejects_conflict_and_directory_symlink(tmp_path):
    manager = ModManager("forge", "1.20.1", tmp_path / "mods")
    source = jar(tmp_path / "test.jar")
    manager.install_local(source, digest(source))
    manager.disabled_dir.mkdir()
    (manager.disabled_dir / "test.jar").write_bytes(b"keep")
    with pytest.raises(ValueError, match="conflicting"):
        manager.set_enabled("test.jar", False)
    assert (manager.disabled_dir / "test.jar").read_bytes() == b"keep"
