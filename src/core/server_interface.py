#!/usr/bin/env python3

"""
Abstract server interface for Minecraft servers
Defines the core operations that any Minecraft server implementation must support
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Union, Any


class MinecraftServer(ABC):
    """Abstract base class for all Minecraft server implementations"""

    @abstractmethod
    def start(self) -> bool:
        """
        Start the Minecraft server

        Returns:
            bool: True if server started successfully, False otherwise
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the Minecraft server

        Returns:
            bool: True if server stopped successfully, False otherwise
        """
        pass

    @abstractmethod
    def restart(self) -> bool:
        """
        Restart the Minecraft server

        Returns:
            bool: True if server restarted successfully, False otherwise
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """
        Check if the server is currently running

        Returns:
            bool: True if server is running, False otherwise
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the server

        Returns:
            Dict[str, Any]: Dictionary containing status information
        """
        pass

    @abstractmethod
    def execute_command(self, command: str) -> str:
        """
        Execute a command on the server console

        Args:
            command: The command to execute

        Returns:
            str: Output from the command execution

        Raises:
            RuntimeError: If the server is not running
        """
        pass

    @abstractmethod
    def backup(self) -> Optional[Path]:
        """
        Create a backup of the server

        Returns:
            Optional[Path]: Path to the backup file if successful, None otherwise
        """
        pass

    @abstractmethod
    def restore(self, backup_path: Optional[Path] = None) -> bool:
        """
        Restore the server from a backup

        Args:
            backup_path: Path to the backup file to restore from.
                         If None, the latest backup will be used.

        Returns:
            bool: True if restored successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_logs(self, lines: int = 50) -> List[str]:
        """
        Get the most recent server logs

        Args:
            lines: Number of lines to retrieve

        Returns:
            List[str]: List of log lines
        """
        pass

    @abstractmethod
    def install_mod(self, mod_id: str, source: str = "modrinth") -> bool:
        """
        Install a mod to the server

        Args:
            mod_id: ID or slug of the mod
            source: Source repository for the mod

        Returns:
            bool: True if installation was successful
        """
        pass

    @abstractmethod
    def uninstall_mod(self, mod_id: str) -> bool:
        """
        Uninstall a mod from the server

        Args:
            mod_id: ID of the mod to uninstall

        Returns:
            bool: True if uninstallation was successful
        """
        pass

    @abstractmethod
    def list_mods(self) -> List[Dict[str, str]]:
        """
        List installed mods

        Returns:
            List[Dict[str, str]]: List of dictionaries containing mod information
        """
        pass

    @abstractmethod
    def configure_auto_shutdown(self, enabled: bool, timeout_minutes: int = 120) -> None:
        """
        Configure auto-shutdown behavior

        Args:
            enabled: Whether auto-shutdown should be enabled
            timeout_minutes: Inactivity minutes before shutdown
        """
        pass

    @abstractmethod
    def update_server_configuration(
        self,
        memory: Optional[str] = None,
        minecraft_version: Optional[str] = None,
        server_type: Optional[str] = None,
        java_flags: Optional[str] = None
    ) -> None:
        """
        Update server configuration

        Args:
            memory: Memory allocation (e.g., "2G")
            minecraft_version: Minecraft version to use
            server_type: Type of server (paper, spigot, etc.)
            java_flags: Java JVM flags
        """
        pass
