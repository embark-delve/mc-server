"""
Base implementation for Minecraft servers with common functionality
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.server_interface import MinecraftServer
from src.utils.auto_shutdown import AutoShutdown
from src.utils.console import Console
from src.utils.file_manager import FileManager
from src.utils.mod_manager import ModManager
from src.utils.monitoring import ServerMonitor

# Configure logging
logger = logging.getLogger(__name__)


class BaseMinecraftServer(MinecraftServer):
    """Base implementation for Minecraft servers with common functionality"""

    def __init__(
        self,
        server_type: str,
        base_dir: Optional[Path] = None,
        data_dir_name: str = "data",
        backup_dir_name: str = "backups",
        plugins_dir_name: str = "plugins",
        config_dir_name: str = "config",
        minecraft_version: str = "latest",
        auto_shutdown_enabled: bool = True,
        auto_shutdown_timeout: int = 120,  # 2 hours in minutes
        monitoring_enabled: bool = True,
        enable_prometheus: bool = True,
        enable_cloudwatch: bool = False,
    ):
        """Initialize base Minecraft server implementation

        Args:
            server_type: Type of server (paper, spigot, etc.)
            base_dir: Base directory for server files
            data_dir_name: Name of the data directory
            backup_dir_name: Name of the backup directory
            plugins_dir_name: Name of the plugins directory
            config_dir_name: Name of the config directory
            minecraft_version: Minecraft version to use
            auto_shutdown_enabled: Whether auto-shutdown should be enabled
            auto_shutdown_timeout: Inactivity minutes before shutdown
            monitoring_enabled: Whether monitoring should be enabled
            enable_prometheus: Whether Prometheus metrics should be enabled
            enable_cloudwatch: Whether CloudWatch metrics should be enabled
        """
        # Set the base directory
        self.base_dir = (
            base_dir or Path(os.path.dirname(
                os.path.abspath(__file__))) / "../.."
        )
        self.base_dir = self.base_dir.resolve()  # Convert to absolute path

        # Set directory paths
        self.data_dir = self.base_dir / data_dir_name
        self.backup_dir = self.base_dir / backup_dir_name
        self.plugins_dir = self.base_dir / plugins_dir_name
        self.config_dir = self.base_dir / config_dir_name

        # Server configuration
        self.server_type = server_type
        self.minecraft_version = minecraft_version
        self.memory = "2G"  # Default memory allocation
        self.java_flags = (
            "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200"
        )

        # Auto-shutdown configuration
        self.auto_shutdown_enabled = auto_shutdown_enabled
        self.auto_shutdown = AutoShutdown(
            shutdown_callback=self.stop,
            inactivity_threshold=auto_shutdown_timeout,
            enabled=auto_shutdown_enabled,
        )

        # Monitoring configuration
        self.monitoring_enabled = monitoring_enabled
        self.enable_prometheus = enable_prometheus
        self.enable_cloudwatch = enable_cloudwatch
        self.monitor = None

        if self.monitoring_enabled:
            self.monitor = ServerMonitor(
                server_type=self.server_type,
                server_name=f"minecraft-{self.server_type}",
                metrics_dir=self.base_dir / "metrics",
                enable_prometheus=self.enable_prometheus,
                enable_cloudwatch=self.enable_cloudwatch,
            )

        # Mod manager
        self.mod_manager = ModManager(
            server_type=self.server_type,
            minecraft_version=self.minecraft_version,
            mods_dir=self.plugins_dir,
        )

        # Ensure required directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist"""
        FileManager.ensure_directories(
            [
                self.data_dir,
                self.backup_dir,
                self.plugins_dir,
                self.config_dir,
                self.base_dir / "logs",
                self.base_dir / "metrics",
            ]
        )

    def restart(self) -> bool:
        """Restart the Minecraft server"""
        Console.print_header("Restarting Minecraft Server")

        if not self.is_running():
            Console.print_warning("Server is not running, starting it...")
            return self.start()

        Console.print_info("Stopping server...")
        if not self.stop():
            Console.print_error("Failed to stop server")
            return False

        Console.print_info("Starting server...")
        return self.start()

    def configure_auto_shutdown(
        self, enabled: bool, timeout_minutes: int = 120
    ) -> None:
        """Configure auto-shutdown behavior"""
        Console.print_header("Configuring Auto-Shutdown")

        # Update auto-shutdown settings
        self.auto_shutdown_enabled = enabled
        self.auto_shutdown.inactivity_threshold = timeout_minutes
        self.auto_shutdown.enabled = enabled

        if enabled:
            Console.print_info(
                f"Auto-shutdown enabled with {timeout_minutes} minutes inactivity timeout"
            )
            # Start monitoring if server is running
            if self.is_running():
                self.auto_shutdown.start_monitoring()
        else:
            Console.print_info("Auto-shutdown disabled")
            # Stop monitoring if it was running
            self.auto_shutdown.stop_monitoring()

    def update_server_configuration(
        self,
        memory: Optional[str] = None,
        minecraft_version: Optional[str] = None,
        server_type: Optional[str] = None,
        java_flags: Optional[str] = None,
    ) -> None:
        """Update server configuration"""
        Console.print_header("Updating Server Configuration")

        # Update configuration values if provided
        if memory:
            self.memory = memory
            Console.print_info(f"Memory allocation set to {memory}")

        if minecraft_version:
            self.minecraft_version = minecraft_version
            Console.print_info(f"Minecraft version set to {minecraft_version}")

        if server_type:
            self.server_type = server_type
            Console.print_info(f"Server type set to {server_type}")

        if java_flags:
            self.java_flags = java_flags
            Console.print_info(f"Java flags set to {java_flags}")

        Console.print_success("Server configuration updated")
        Console.print_info("Restart the server for changes to take effect")

    def install_mod(self, mod_id: str, source: str = "modrinth") -> bool:
        """Install a mod to the server"""
        Console.print_header(f"Installing Mod: {mod_id}")

        if not self.mod_manager.is_compatible(source):
            Console.print_error(
                f"Server type '{self.server_type}' is not compatible with {source} mods"
            )
            return False

        success = self.mod_manager.install_mod(mod_id, source)

        if success:
            Console.print_success(f"Successfully installed mod {mod_id}")
            Console.print_info("Restart the server for the mod to take effect")
        else:
            Console.print_error(f"Failed to install mod {mod_id}")

        return success

    def uninstall_mod(self, mod_id: str) -> bool:
        """Uninstall a mod from the server"""
        Console.print_header(f"Uninstalling Mod: {mod_id}")

        success = self.mod_manager.uninstall_mod(mod_id)

        if success:
            Console.print_success(f"Successfully uninstalled mod {mod_id}")
            Console.print_info("Restart the server for changes to take effect")
        else:
            Console.print_error(f"Failed to uninstall mod {mod_id}")

        return success

    def list_mods(self) -> List[Dict[str, str]]:
        """List installed mods"""
        Console.print_header("Installed Mods")

        mods = self.mod_manager.list_installed_mods()

        if not mods:
            Console.print_info("No mods installed")
            return []

        # Display mods in a table
        Console.print_table(
            ["Name", "Version", "Source"],
            [[mod["name"], mod["version"], mod.get(
                "source", "Unknown")] for mod in mods]
        )

        return self.mod_manager.list_installed_mods()

    # Abstract methods that must be implemented by subclasses
    def _get_player_list(self) -> List[str]:
        """Get list of currently active players"""
        raise NotImplementedError("Subclasses must implement _get_player_list")
