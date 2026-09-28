"""Install explicitly selected, hash-verified local Forge JARs; no mock downloads."""

import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from src.utils.file_manager import atomic_json, digest


class ModManager:
    def __init__(
        self, server_type: str, minecraft_version: str, mods_dir: Path
    ) -> None:
        self.server_type = server_type
        self.minecraft_version = minecraft_version
        self.mods_dir = mods_dir
        self.disabled_dir = mods_dir.parent / "disabled-mods"
        self.installed_mods_file = mods_dir / "installed_mods.json"

    def is_compatible(self, source: str) -> bool:
        return source == "local" and self.server_type == "forge"

    def install_mod(
        self, mod_identifier: str, source: str = "modrinth", version: str | None = None
    ) -> bool:
        raise ValueError(
            "Automatic provider downloads are disabled. Use mods-install with an exact SHA-256 and reviewed Forge JAR"
        )

    def install_local(self, path: Path, sha256: str) -> bool:
        if self.server_type != "forge":
            raise ValueError("Local JAR installation currently supports Forge only")
        if not re.fullmatch(r"[a-f0-9]{64}", sha256):
            raise ValueError("An explicit SHA-256 is required")
        if (
            path.is_symlink()
            or not path.is_file()
            or path.suffix != ".jar"
            or path.stat().st_size > 256 * 1024**2
        ):
            raise ValueError("Choose a regular JAR of at most 256 MiB")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*\.jar", path.name):
            raise ValueError("Unsafe JAR filename")
        if digest(path) != sha256:
            raise ValueError("JAR SHA-256 mismatch")
        with zipfile.ZipFile(path) as jar:
            if "META-INF/mods.toml" not in jar.namelist():
                raise ValueError("JAR is not a Forge mod (META-INF/mods.toml missing)")
            info = jar.getinfo("META-INF/mods.toml")
            if info.file_size > 1024**2:
                raise ValueError("Oversized mod metadata")
            # Checking metadata proves format, not compatibility or trust.
            import tomllib

            metadata = tomllib.loads(jar.read(info).decode())
            if metadata.get("clientSideOnly") is True:
                raise ValueError("Client-only mod cannot be installed on this server")
            client_ids = {
                "embeddium",
                "oculus",
                "rubidium",
                "fullbright",
                "fullbrightnesstoggle",
            }
            ids = {entry.get("modId") for entry in metadata.get("mods", [])}
            if ids & client_ids:
                raise ValueError(
                    "Known client-only mod cannot be installed on this server"
                )
        if self.mods_dir.is_symlink():
            raise ValueError("Mods directory cannot be a symlink")
        self.mods_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if (self.disabled_dir / path.name).exists() or self.disabled_dir.is_symlink():
            raise ValueError(
                "A disabled copy already exists or its directory is unsafe"
            )
        target = self.mods_dir / path.name
        if target.exists() or target.is_symlink():
            raise FileExistsError("Remove or archive the old JAR after taking a backup")
        fd, temp = tempfile.mkstemp(prefix=".mod-", dir=self.mods_dir)
        os.close(fd)
        try:
            shutil.copyfile(path, temp)
            if digest(Path(temp)) != sha256:
                raise ValueError("JAR changed while copying")
            os.link(temp, target)
            records = self._load()
            records[path.name] = {
                "filename": path.name,
                "sha256": sha256,
                "minecraft": self.minecraft_version,
            }
            atomic_json(self.installed_mods_file, records)
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        finally:
            Path(temp).unlink(missing_ok=True)
        return True

    def _load(self) -> dict[str, Any]:
        if self.installed_mods_file.is_symlink():
            raise ValueError("Mod inventory cannot be a symlink")
        if not self.installed_mods_file.exists():
            return {}
        data = json.loads(self.installed_mods_file.read_text())
        if not isinstance(data, dict):
            raise ValueError("Invalid mod inventory")
        return data

    def list_installed_mods(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for directory, enabled in [(self.mods_dir, True), (self.disabled_dir, False)]:
            if directory.is_symlink():
                raise ValueError("Refusing mod directory symlink")
            result.extend(
                {"id": p.name, "name": p.name, "sha256": digest(p), "enabled": enabled}
                for p in sorted(directory.glob("*.jar"))
                if p.is_file() and not p.is_symlink()
            )
        return result

    def set_enabled(self, filename: str, enabled: bool) -> bool:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*\.jar", filename):
            raise ValueError("Specify an installed JAR basename")
        if self.mods_dir.is_symlink() or self.disabled_dir.is_symlink():
            raise ValueError("Refusing mod directory symlink")
        source_dir, target_dir = (
            (self.disabled_dir, self.mods_dir)
            if enabled
            else (self.mods_dir, self.disabled_dir)
        )
        source, target = source_dir / filename, target_dir / filename
        if source.is_symlink() or not source.is_file():
            raise ValueError("Mod is missing or already in the requested state")
        if target.exists() or target.is_symlink():
            raise ValueError("A conflicting copy exists; no files were replaced")
        target_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        # Same-filesystem rename under the caller's profile lock is atomic.
        source.rename(target)
        return True

    def uninstall_mod(self, mod_identifier: str) -> bool:
        if Path(mod_identifier).name != mod_identifier or not mod_identifier.endswith(
            ".jar"
        ):
            raise ValueError("Specify an installed JAR basename")
        target = self.mods_dir / mod_identifier
        if target.is_symlink() or self.mods_dir.is_symlink():
            raise ValueError("Refusing symlink")
        target.unlink()
        records = self._load()
        records.pop(mod_identifier, None)
        atomic_json(self.installed_mods_file, records)
        return True
