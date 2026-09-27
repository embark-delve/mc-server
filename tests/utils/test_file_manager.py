import json
import os
import stat
import zipfile

import pytest

from src.utils.file_manager import FileManager


@pytest.fixture
def world(tmp_path):
    profile = tmp_path / "profile"
    data = profile / "data"
    (data / "mods").mkdir(parents=True)
    (data / "region").mkdir()
    (data / "region" / "test.mca").write_bytes(b"original region")
    (data / "mods" / "example.jar").write_bytes(b"example")
    return profile, data


def test_roundtrip_preserves_previous_and_unrelated(world):
    profile, data = world
    archive, _ = FileManager.create_backup(data, profile / "backups")
    (data / "region" / "test.mca").write_bytes(b"new world")
    (profile / "unrelated").mkdir()
    (profile / "unrelated" / "keep").write_text("keep")
    assert FileManager.extract_backup(archive, profile, data)
    assert (data / "region" / "test.mca").read_bytes() == b"original region"
    assert (
        profile / "data.rollback" / "region" / "test.mca"
    ).read_bytes() == b"new world"
    assert (profile / "unrelated" / "keep").read_text() == "keep"
    with pytest.raises(ValueError, match="rollback"):
        FileManager.extract_backup(archive, profile, data)


@pytest.mark.parametrize(
    "member",
    [
        "../escape",
        "/absolute",
        "data/../../escape",
        "other/file",
        "data/../escape",
        "data\\escape",
    ],
)
def test_archive_path_attacks_leave_world_unchanged(world, member):
    profile, data = world
    archive = profile / "bad.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(member, "bad")
    with pytest.raises(ValueError):
        FileManager.extract_backup(archive, profile, data)
    assert (data / "region" / "test.mca").read_bytes() == b"original region"


def test_archive_symlink_rejected(world):
    profile, data = world
    archive = profile / "bad.zip"
    info = zipfile.ZipInfo("data/link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(info, "/tmp")
    with pytest.raises(ValueError):
        FileManager.extract_backup(archive, profile, data)
    assert data.exists()


def test_manifest_hash_mismatch(world):
    profile, data = world
    archive = profile / "bad.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("data/fake", "bad")
        z.writestr(
            "manifest.json",
            json.dumps(
                {"schema": 1, "files": {"data/fake": {"size": 3, "sha256": "0" * 64}}}
            ),
        )
    with pytest.raises(ValueError, match="checksum"):
        FileManager.extract_backup(archive, profile, data)
    assert (data / "region" / "test.mca").exists()


def test_restore_rollback_on_rename_failure(world, monkeypatch):
    profile, data = world
    archive, _ = FileManager.create_backup(data, profile / "backups")
    (data / "region" / "test.mca").write_text("latest")
    real = os.replace

    def replace(source, target):
        if ".restore-" in str(source):
            raise OSError("simulated disk failure")
        real(source, target)

    monkeypatch.setattr(os, "replace", replace)
    with pytest.raises(OSError):
        FileManager.extract_backup(archive, profile, data)
    assert (data / "region" / "test.mca").read_text() == "latest"


def test_limits_and_runtime(world):
    profile, data = world
    archive, _ = FileManager.create_backup(
        data, profile / "backups", metadata={"runtime": {"java": "17"}}
    )
    with pytest.raises(ValueError, match="limits"):
        FileManager.extract_backup(archive, profile, data, max_bytes=1)
    with pytest.raises(ValueError, match="runtime"):
        FileManager.extract_backup(
            archive, profile, data, expected_runtime={"java": "25"}
        )
    assert data.exists()


def test_symlink_source_and_backup_collisions(world, tmp_path):
    profile, data = world
    (data / "link").symlink_to(tmp_path)
    with pytest.raises(ValueError, match="links"):
        FileManager.create_backup(data, profile / "backups")
    (data / "link").unlink()
    FileManager.create_backup(data, profile / "backups", "one.zip")
    with pytest.raises(FileExistsError):
        FileManager.create_backup(data, profile / "backups", "one.zip")


def test_retention_guard(world):
    profile, data = world
    for _ in range(3):
        FileManager.create_backup(data, profile / "backups")
    assert FileManager.cleanup_old_backups(profile / "backups", 2) == 1
    with pytest.raises(ValueError):
        FileManager.cleanup_old_backups(profile / "backups", 0)


def test_corrupt_archive_and_disk_full_preserve_world(world, monkeypatch):
    import shutil

    profile, data = world
    bad = profile / "corrupt.zip"
    bad.write_bytes(b"not a zip")
    with pytest.raises(zipfile.BadZipFile):
        FileManager.extract_backup(bad, profile, data)
    monkeypatch.setattr(
        shutil, "disk_usage", lambda _: type("Usage", (), {"free": 0})()
    )
    with pytest.raises(OSError, match="disk"):
        FileManager.create_backup(data, profile / "backups")
    assert (data / "region" / "test.mca").read_bytes() == b"original region"
