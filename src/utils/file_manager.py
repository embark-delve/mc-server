"""Stopped-server snapshots and staged, validated restoration."""

import hashlib
import json
import os
import shutil
import stat
import tempfile
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def atomic_json(path: Path, content: Any) -> None:
    if path.is_symlink():
        raise ValueError(f"Refusing symlink: {path}")
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(content, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


class FileManager:
    @staticmethod
    def ensure_directories(dirs: list[Path]) -> None:
        for path in dirs:
            if path.is_symlink():
                raise ValueError(f"Refusing symlink directory: {path}")
            path.mkdir(parents=True, exist_ok=True, mode=0o700)

    @staticmethod
    def create_backup(
        source_dir: Path,
        backup_dir: Path,
        backup_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Path, str]:
        if source_dir.is_symlink() or not source_dir.is_dir():
            raise ValueError("Backup source must be an existing real directory")
        if backup_dir.resolve().is_relative_to(source_dir.resolve()):
            raise ValueError("Backups cannot be stored inside the data directory")
        FileManager.ensure_directories([backup_dir])
        name = (
            backup_name
            or f"minecraft-{datetime.now(UTC):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}.zip"
        )
        if Path(name).name != name or not name.endswith(".zip"):
            raise ValueError("Backup name must be a ZIP basename")
        target = backup_dir / name
        if target.exists() or target.is_symlink():
            raise FileExistsError(target)
        files = []
        for path in sorted(source_dir.rglob("*")):
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise ValueError(f"Backup refuses links or special files: {path}")
            if path.is_file():
                files.append(path)
        size = sum(path.stat().st_size for path in files)
        if shutil.disk_usage(backup_dir).free < size + 64 * 1024**2:
            raise OSError("Insufficient free disk for a safe backup")
        fd, temp = tempfile.mkstemp(prefix=".backup-", dir=backup_dir)
        os.close(fd)
        staging = Path(temp)
        try:
            manifest: dict[str, Any] = {
                "schema": 1,
                "created_at": datetime.now(UTC).isoformat(),
                "metadata": metadata or {},
                "files": {},
            }
            with zipfile.ZipFile(
                staging, "w", zipfile.ZIP_DEFLATED, allowZip64=True
            ) as archive:
                for path in files:
                    relative = "data/" + path.relative_to(source_dir).as_posix()
                    hasher = hashlib.sha256()
                    written = 0
                    with (
                        path.open("rb") as source,
                        archive.open(relative, "w", force_zip64=True) as output,
                    ):
                        while chunk := source.read(1024 * 1024):
                            hasher.update(chunk)
                            output.write(chunk)
                            written += len(chunk)
                    manifest["files"][relative] = {
                        "sha256": hasher.hexdigest(),
                        "size": written,
                    }
                archive.writestr("manifest.json", json.dumps(manifest))
            with zipfile.ZipFile(staging) as archive:
                if archive.testzip() is not None:
                    raise ValueError("Backup failed archive verification")
            with staging.open("rb") as stream:
                os.fsync(stream.fileno())
            # Exclusive publication never overwrites a previous good backup.
            os.link(staging, target)
        finally:
            staging.unlink(missing_ok=True)
        return target, FileManager.get_file_size(target)

    @staticmethod
    def list_backups(backup_dir: Path) -> list[Path]:
        return sorted(
            (p for p in backup_dir.glob("*.zip") if p.is_file() and not p.is_symlink()),
            key=lambda p: p.stat().st_mtime_ns,
            reverse=True,
        )

    @staticmethod
    def cleanup_old_backups(backup_dir: Path, keep_count: int) -> int:
        if type(keep_count) is not int or keep_count < 1:
            raise ValueError("Keep at least one backup")
        old = FileManager.list_backups(backup_dir)[keep_count:]
        for path in old:
            path.unlink()
        return len(old)

    @staticmethod
    def extract_backup(
        backup_path: Path,
        extract_dir: Path,
        target_dir: Path | None = None,
        max_bytes: int = 20 * 1024**3,
        expected_runtime: dict[str, Any] | None = None,
    ) -> bool:
        target = target_dir or extract_dir / "data"
        if (
            target.parent.resolve() != extract_dir.resolve()
            or target.name != "data"
            or target.is_symlink()
        ):
            raise ValueError("Restore target must be the profile's real data directory")
        rollback = extract_dir / "data.rollback"
        if rollback.exists() or rollback.is_symlink():
            raise ValueError(
                "A previous data.rollback exists; recover or move it before restoring"
            )
        if max_bytes <= 0:
            raise ValueError("Restore size limit must be positive")
        FileManager.ensure_directories([extract_dir])
        with tempfile.TemporaryDirectory(prefix=".restore-", dir=extract_dir) as temp:
            stage = Path(temp)
            (stage / "data").mkdir()
            with zipfile.ZipFile(backup_path) as archive:
                entries = archive.infolist()
                if (
                    len(entries) > 100_000
                    or sum(x.file_size for x in entries) > max_bytes
                ):
                    raise ValueError("Archive exceeds restore limits")
                if (
                    shutil.disk_usage(extract_dir).free
                    < sum(x.file_size for x in entries) + 64 * 1024**2
                ):
                    raise OSError("Insufficient disk for staged restore")
                names: set[str] = set()
                for entry in entries:
                    name = entry.filename
                    path = PurePosixPath(name)
                    mode = entry.external_attr >> 16
                    if (
                        name.casefold() in names
                        or "\\" in name
                        or path.is_absolute()
                        or any(
                            x in ("..", ".", "") for x in name.rstrip("/").split("/")
                        )
                        or (
                            name != "manifest.json"
                            and (not path.parts or path.parts[0] != "data")
                        )
                        or stat.S_ISLNK(mode)
                        or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR))
                        or entry.flag_bits & 1
                    ):
                        raise ValueError(f"Unsafe archive member: {name}")
                    names.add(name.casefold())
                if (
                    "manifest.json" not in names
                    or archive.getinfo("manifest.json").file_size > 8 * 1024**2
                ):
                    raise ValueError(
                        "A bounded versioned manifest is required; legacy archives need manual recovery"
                    )
                manifest = json.loads(archive.read("manifest.json"))
                if (
                    not isinstance(manifest, dict)
                    or manifest.get("schema") != 1
                    or not isinstance(manifest.get("files"), dict)
                    or not isinstance(manifest.get("metadata", {}), dict)
                ):
                    raise ValueError("Invalid backup manifest")
                if (
                    expected_runtime is not None
                    and manifest.get("metadata", {}).get("runtime") != expected_runtime
                ):
                    raise ValueError(
                        "Backup runtime does not match this profile; restore into a matching profile"
                    )
                actual = {
                    x.filename
                    for x in entries
                    if not x.is_dir() and x.filename != "manifest.json"
                }
                if actual != set(manifest["files"]):
                    raise ValueError("Archive files do not match manifest")
                for entry in entries:
                    if entry.filename == "manifest.json":
                        continue
                    dest = stage / entry.filename
                    if entry.is_dir():
                        dest.mkdir(parents=True, exist_ok=True)
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with archive.open(entry) as source, dest.open("xb") as output:
                            shutil.copyfileobj(source, output)
                        record = manifest["files"][entry.filename]
                        if (
                            not isinstance(record, dict)
                            or not isinstance(record.get("sha256"), str)
                            or type(record.get("size")) is not int
                        ):
                            raise ValueError("Invalid file record in backup manifest")
                        if (
                            dest.stat().st_size != record["size"]
                            or digest(dest) != record["sha256"]
                        ):
                            raise ValueError("Backup checksum mismatch")
            existed = target.exists()
            if existed:
                os.replace(target, rollback)
            try:
                os.replace(stage / "data", target)
            except BaseException:
                if existed:
                    os.replace(rollback, target)
                raise
            # Keep rollback until an operator has verified the restored world.
        return True

    @staticmethod
    def format_size(size_bytes: int) -> str:
        return f"{size_bytes / 1024**2:.2f} MiB"

    @staticmethod
    def get_file_size(file_path: Path) -> str:
        return FileManager.format_size(file_path.stat().st_size)
