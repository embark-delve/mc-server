#!/usr/bin/env python3

"""
Mod manager utility for Minecraft servers
Handles downloading, installing, and managing server mods
"""

import datetime
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mod_manager")

# Default sources for mods
DEFAULT_SOURCES = {
    "modrinth": "https://api.modrinth.com/v2",
    "curseforge": "https://api.curseforge.com/v1",
    "bukkit": "https://dev.bukkit.org/projects",
    "spigot": "https://api.spigotmc.org/legacy/update.php",
}

# Supported server types with compatible mod formats
SERVER_COMPATIBILITY = {
    "vanilla": [],  # Vanilla doesn't support mods
    "spigot": ["bukkit", "spigot"],
    "paper": ["bukkit", "spigot"],
    "fabric": ["fabric", "modrinth"],
    "forge": ["forge", "curseforge"],
}


class ModManager:
    """
    Utility for downloading and managing Minecraft server mods
    """

    def __init__(
        self,
        server_type: str,
        minecraft_version: str,
        mods_dir: Path,
        api_keys: Optional[Dict[str, str]] = None,
        mod_sources: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the mod manager

        Args:
            server_type: Type of Minecraft server (vanilla, spigot, paper, fabric, forge)
            minecraft_version: Minecraft version (e.g. 1.20.4)
            mods_dir: Directory to store mods
            api_keys: Optional API keys for mod repositories
            mod_sources: Optional custom mod repository URLs
        """
        self.server_type = server_type.lower()
        self.minecraft_version = minecraft_version
        self.mods_dir = mods_dir
        self.api_keys = api_keys or {}
        self.mod_sources = {**DEFAULT_SOURCES, **(mod_sources or {})}

        # Ensure mods directory exists
        os.makedirs(self.mods_dir, exist_ok=True)

        # Installed mods cache
        self.installed_mods_file = self.mods_dir / "installed_mods.json"
        self.installed_mods = self._load_installed_mods()

        # Check compatibility
        if self.server_type not in SERVER_COMPATIBILITY:
            logger.warning(
                f"Unknown server type: {self.server_type}. "
                f"Mod installation may not work correctly."
            )

    def _load_installed_mods(self) -> Dict[str, Dict[str, Any]]:
        """
        Load information about installed mods from cache

        Returns:
            Dict of installed mods with metadata
        """
        if not os.path.exists(self.installed_mods_file):
            return {}

        try:
            with open(self.installed_mods_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load installed mods cache: {e}")
            return {}

    def _save_installed_mods(self) -> None:
        """Save information about installed mods to cache"""
        try:
            with open(self.installed_mods_file, "w") as f:
                json.dump(self.installed_mods, f, indent=2)
        except OSError as e:
            logger.warning(f"Failed to save installed mods cache: {e}")

    def list_installed_mods(self) -> List[Dict[str, Any]]:
        """
        Get list of installed mods with metadata

        Returns:
            List of dictionaries with mod information
        """
        return [
            {
                "id": mod_id,
                "name": info.get("name", mod_id),
                "version": info.get("version", "unknown"),
                "source": info.get("source", "unknown"),
                "mc_version": info.get("mc_version", "unknown"),
                "installed_at": info.get("installed_at", "unknown"),
            }
            for mod_id, info in self.installed_mods.items()
        ]

    def is_compatible(self, source: str) -> bool:
        """
        Check if a mod source is compatible with the current server type

        Args:
            source: Mod source (modrinth, curseforge, bukkit, etc.)

        Returns:
            bool: True if compatible, False otherwise
        """
        compatible_sources = SERVER_COMPATIBILITY.get(self.server_type, [])
        return source in compatible_sources

    def install_mod(
        self,
        mod_identifier: str,
        source: str = "modrinth",
        version: Optional[str] = None,
    ) -> bool:
        """
        Install a mod from the specified source

        Args:
            mod_identifier: ID or slug of the mod
            source: Source repository (modrinth, curseforge, bukkit, spigot)
            version: Specific version to install, or None for latest compatible

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        # Check compatibility
        if not self.is_compatible(source):
            logger.error(
                f"Mod source '{source}' is not compatible with server type '{self.server_type}'"
            )
            return False

        # Get mod info and download URL
        try:
            mod_info, download_url = self._get_mod_download_info(
                mod_identifier, source, version
            )

            if not download_url:
                logger.error(f"Could not find download URL for mod {mod_identifier}")
                return False

            # Download and install the mod
            return self._download_and_install_mod(
                mod_identifier, mod_info, download_url, source
            )

        except Exception as e:
            logger.error(f"Error installing mod {mod_identifier}: {e}")
            return False

    def uninstall_mod(self, mod_identifier: str) -> bool:
        """
        Uninstall a mod by ID

        Args:
            mod_identifier: ID of the mod to uninstall

        Returns:
            bool: True if uninstallation succeeded, False otherwise
        """
        if mod_identifier not in self.installed_mods:
            logger.warning(f"Mod {mod_identifier} is not installed")
            return False

        # Get filename from installed mods cache
        mod_info = self.installed_mods[mod_identifier]
        filename = mod_info.get("filename")

        if not filename:
            logger.warning(f"Filename not found for mod {mod_identifier}")
            return False

        # Remove the file
        mod_path = self.mods_dir / filename
        try:
            if os.path.exists(mod_path):
                os.remove(mod_path)

            # Remove from installed mods cache
            del self.installed_mods[mod_identifier]
            self._save_installed_mods()

            logger.info(f"Successfully uninstalled mod {mod_identifier}")
            return True

        except OSError as e:
            logger.error(f"Error uninstalling mod {mod_identifier}: {e}")
            return False

    def update_mod(self, mod_identifier: str) -> bool:
        """
        Update a mod to the latest version compatible with the server

        Args:
            mod_identifier: ID of the mod to update

        Returns:
            bool: True if update succeeded, False otherwise
        """
        if mod_identifier not in self.installed_mods:
            logger.warning(f"Mod {mod_identifier} is not installed")
            return False

        # Get information about the installed mod
        mod_info = self.installed_mods[mod_identifier]
        source = mod_info.get("source")

        if not source:
            logger.warning(f"Source information missing for mod {mod_identifier}")
            return False

        # Uninstall the old version
        if not self.uninstall_mod(mod_identifier):
            logger.warning(f"Failed to uninstall old version of mod {mod_identifier}")
            return False

        # Install the new version
        return self.install_mod(mod_identifier, source)

    def _get_mod_download_info(
        self, mod_identifier: str, source: str, version: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Get mod information and download URL

        Args:
            mod_identifier: ID or slug of the mod
            source: Source repository
            version: Specific version to find

        Returns:
            Tuple containing mod info dict and download URL

        Raises:
            ValueError: If mod cannot be found or is incompatible
        """
        if source == "modrinth":
            return self._get_modrinth_download_info(mod_identifier, version)
        elif source == "curseforge":
            return self._get_curseforge_download_info(mod_identifier, version)
        elif source in ["bukkit", "spigot"]:
            return self._get_bukkit_spigot_download_info(
                mod_identifier, source, version
            )
        else:
            raise ValueError(f"Unsupported mod source: {source}")

    def _get_modrinth_download_info(
        self, mod_identifier: str, version: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        """Get mod info from Modrinth"""
        # Implementation details would go here
        # This would make API calls to Modrinth
        # For example purposes, we're returning dummy data
        mod_info = {
            "name": "Example Mod",
            "version": "1.0.0",
            "mc_version": self.minecraft_version,
            "author": "Example Author",
            "description": "An example mod",
        }
        download_url = "https://example.com/mods/example-mod.jar"
        return mod_info, download_url

    def _get_curseforge_download_info(
        self, mod_identifier: str, version: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        """Get mod info from CurseForge"""
        # Implementation details would go here
        # This would make API calls to CurseForge
        mod_info = {
            "name": "Example Mod",
            "version": "1.0.0",
            "mc_version": self.minecraft_version,
            "author": "Example Author",
            "description": "An example mod",
        }
        download_url = "https://example.com/mods/example-mod.jar"
        return mod_info, download_url

    def _get_bukkit_spigot_download_info(
        self, mod_identifier: str, source: str, version: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        """Get mod info from Bukkit/Spigot"""
        # Implementation details would go here
        mod_info = {
            "name": "Example Plugin",
            "version": "1.0.0",
            "mc_version": self.minecraft_version,
            "author": "Example Author",
            "description": "An example plugin",
        }
        download_url = "https://example.com/plugins/example-plugin.jar"
        return mod_info, download_url

    def _download_and_install_mod(
        self,
        mod_identifier: str,
        mod_info: Dict[str, Any],
        download_url: str,
        source: str,
    ) -> bool:
        """
        Download and install a mod

        Args:
            mod_identifier: ID of the mod
            mod_info: Information about the mod
            download_url: URL to download the mod
            source: Source of the mod

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        # Create a temporary file for downloading
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Download the file
            logger.info(f"Downloading mod from {download_url}")

            # For demo purposes, we're not actually downloading
            # In a real implementation, this would use requests:
            # response = requests.get(download_url, stream=True)
            # with open(temp_path, 'wb') as f:
            #     for chunk in response.iter_content(chunk_size=8192):
            #         f.write(chunk)

            # Get mod filename from info or extract from URL
            mod_filename = mod_info.get("filename")
            if not mod_filename:
                mod_filename = os.path.basename(download_url)
                if not mod_filename.endswith(".jar"):
                    mod_filename += ".jar"

            # Move to mods directory
            mod_path = self.mods_dir / mod_filename
            shutil.move(temp_path, mod_path)

            # Add to installed mods cache
            self.installed_mods[mod_identifier] = {
                "name": mod_info.get("name", mod_identifier),
                "version": mod_info.get("version", "unknown"),
                "mc_version": mod_info.get("mc_version", self.minecraft_version),
                "source": source,
                "filename": mod_filename,
                "installed_at": datetime.datetime.now().isoformat(),
                "info": mod_info,
            }

            self._save_installed_mods()
            logger.info(f"Successfully installed mod {mod_identifier}")
            return True

        except Exception as e:
            logger.error(f"Error downloading and installing mod: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return False

    def check_for_updates(self) -> Dict[str, Dict[str, Any]]:
        """
        Check for updates to installed mods

        Returns:
            Dict mapping mod IDs to update information
        """
        updates = {}

        for mod_id, info in self.installed_mods.items():
            source = info.get("source")
            current_version = info.get("version")

            if not source or not current_version:
                continue

            try:
                # Get latest compatible version info
                latest_info, _ = self._get_mod_download_info(mod_id, source)
                latest_version = latest_info.get("version")

                if latest_version and latest_version != current_version:
                    updates[mod_id] = {
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "name": info.get("name", mod_id),
                    }

            except Exception as e:
                logger.warning(f"Error checking for updates to mod {mod_id}: {e}")

        return updates
