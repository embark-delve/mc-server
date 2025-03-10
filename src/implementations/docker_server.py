#!/usr/bin/env python3

"""
Docker-based Minecraft Server implementation
"""

import os
import time
import shutil
import logging
from typing import Dict, List, Optional, Union, Set
from pathlib import Path

from src.core.server_interface import MinecraftServer
from src.utils.console import Console
from src.utils.command_executor import CommandExecutor
from src.utils.file_manager import FileManager
from src.utils.auto_shutdown import AutoShutdown
from src.utils.mod_manager import ModManager
from src.utils.monitoring import ServerMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("docker_server")


class DockerServer(MinecraftServer):
    """Docker-based Minecraft server implementation"""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        container_name: str = "minecraft-server",
        data_dir_name: str = "data",
        backup_dir_name: str = "backups",
        plugins_dir_name: str = "plugins",
        config_dir_name: str = "config",
        minecraft_version: str = "latest",
        server_type: str = "paper",
        auto_shutdown_enabled: bool = True,
        auto_shutdown_timeout: int = 120,  # 2 hours in minutes
        monitoring_enabled: bool = True,
        enable_prometheus: bool = True,
        enable_cloudwatch: bool = False
    ):
        """
        Initialize a Docker-based Minecraft server

        Args:
            base_dir: Base directory for server files (defaults to script directory)
            container_name: Name of the Docker container
            data_dir_name: Name of the data directory
            backup_dir_name: Name of the backups directory
            plugins_dir_name: Name of the plugins directory
            config_dir_name: Name of the config directory
            minecraft_version: Minecraft version to use
            server_type: Type of server (paper, spigot, vanilla, etc.)
            auto_shutdown_enabled: Whether to enable auto-shutdown
            auto_shutdown_timeout: Minutes of inactivity before shutdown
            monitoring_enabled: Whether to enable monitoring
            enable_prometheus: Whether to enable Prometheus metrics
            enable_cloudwatch: Whether to enable CloudWatch metrics
        """
        # Set the base directory
        self.base_dir = base_dir or Path(
            os.path.dirname(os.path.abspath(__file__))) / "../.."
        self.base_dir = self.base_dir.resolve()  # Convert to absolute path

        # Set container name
        self.container_name = container_name

        # Configure directories
        self.data_dir = self.base_dir / data_dir_name
        self.backup_dir = self.base_dir / backup_dir_name
        self.plugins_dir = self.base_dir / plugins_dir_name
        self.config_dir = self.base_dir / config_dir_name
        self.logs_dir = self.base_dir / "logs"

        # Server configuration
        self.minecraft_version = minecraft_version
        self.server_type = server_type.lower()
        self.memory = "2G"  # Default memory allocation
        self.java_flags = "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200"

        # Docker compose command
        self.docker_compose_cmd = ["docker", "compose"]

        # Ensure directories exist
        self._ensure_directories()

        # Initialize auto-shutdown
        self.auto_shutdown_enabled = auto_shutdown_enabled
        self.auto_shutdown = AutoShutdown(
            shutdown_callback=self.stop,
            inactivity_threshold=auto_shutdown_timeout,
            check_interval=5,  # Check every 5 minutes
            enabled=auto_shutdown_enabled
        )

        # Initialize mod manager
        self.mod_manager = ModManager(
            server_type=self.server_type,
            minecraft_version=self.minecraft_version,
            mods_dir=self.plugins_dir
        )

        # Initialize monitoring
        self.monitoring_enabled = monitoring_enabled
        if monitoring_enabled:
            self.monitor = ServerMonitor(
                server_type="docker",
                server_name=self.container_name,
                enable_prometheus=enable_prometheus,
                enable_cloudwatch=enable_cloudwatch,
                metrics_dir=self.base_dir / "metrics"
            )
        else:
            self.monitor = None

        # Current player list
        self.active_players: Set[str] = set()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        FileManager.ensure_directories([
            self.data_dir,
            self.backup_dir,
            self.plugins_dir,
            self.config_dir,
            self.logs_dir,
            self.base_dir / "metrics"
        ])

    def is_running(self) -> bool:
        """Check if the Minecraft server is running"""
        result = CommandExecutor.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            verbose=False
        )
        return self.container_name in result.stdout

    def _get_player_list(self) -> List[str]:
        """Get a list of currently active players"""
        try:
            if not self.is_running():
                return []

            # Get player list using RCON
            result = self.execute_command("list")

            # Parse player list from output
            # Example output: "There are 3 of 20 players online: player1, player2, player3"
            if "players online:" in result:
                players_part = result.split("players online:")[1].strip()
                if players_part:
                    return [p.strip() for p in players_part.split(",")]

            return []
        except Exception as e:
            logger.warning(f"Failed to get player list: {e}")
            return []

    def start(self) -> bool:
        """Start the Minecraft server"""
        Console.print_header("Starting Minecraft Server")

        if self.is_running():
            Console.print_warning("Server is already running!")
            return True

        Console.print_success("Starting Minecraft server...")

        # Create or update docker-compose.yml
        self._create_docker_compose_file()

        # Start the container
        CommandExecutor.run(self.docker_compose_cmd +
                            ["up", "-d"], cwd=self.base_dir)

        # Check server startup
        Console.print_info("Checking server startup...")

        # Wait for the server to initialize (checks 10 times with 5-second intervals)
        for i in range(1, 11):
            try:
                result = CommandExecutor.run(
                    ["docker", "logs", self.container_name],
                    capture_output=True,
                    verbose=False,
                    check=False
                )

                if "Done" in result.stdout:
                    Console.print_success("Server started successfully!")
                    Console.print_colored(
                        "Connect to server at: localhost:25565", Console.PURPLE)

                    # Start auto-shutdown monitoring
                    if self.auto_shutdown_enabled:
                        self.auto_shutdown.start_monitoring()
                        Console.print_info(
                            f"Auto-shutdown enabled. Server will shut down after "
                            f"{self.auto_shutdown.inactivity_threshold} minutes of inactivity."
                        )

                    # Start monitoring
                    if self.monitoring_enabled and self.monitor:
                        self.monitor.start()
                        Console.print_info("Server monitoring started.")

                    return True
            except Exception:
                pass

            Console.print_warning(
                f"Waiting for server to initialize... ({i}/10)")
            time.sleep(5)

        Console.print_warning(
            "Server is starting but taking longer than expected.")
        Console.print_warning("Check logs with: server.get_logs()")
        return False

    def stop(self) -> bool:
        """Stop the Minecraft server"""
        Console.print_header("Stopping Minecraft Server")

        if not self.is_running():
            Console.print_warning("Server is not running!")
            return True

        # Stop auto-shutdown monitoring
        if self.auto_shutdown_enabled:
            self.auto_shutdown.stop_monitoring()

        # Stop monitoring
        if self.monitoring_enabled and self.monitor:
            self.monitor.stop()

        Console.print_success("Stopping Minecraft server...")

        # Send stop command to server console first for clean shutdown
        try:
            self.execute_command("stop")
            # Wait for server to stop gracefully
            time.sleep(5)
        except Exception as e:
            Console.print_warning(
                f"Could not send stop command, forcing shutdown... Error: {e}")

        # Force stop if still running
        CommandExecutor.run(self.docker_compose_cmd +
                            ["down"], cwd=self.base_dir)
        Console.print_success("Server stopped successfully!")
        return True

    def restart(self) -> bool:
        """Restart the Minecraft server"""
        Console.print_header("Restarting Minecraft Server")
        Console.print_success("Restarting Minecraft server...")

        stop_success = self.stop()
        time.sleep(2)  # Wait a bit before starting again
        start_success = self.start()

        return stop_success and start_success

    def get_status(self) -> Dict[str, Union[str, int, bool]]:
        """Get the current status of the server"""
        is_running = self.is_running()

        status = {
            "running": is_running,
            "server_type": "Docker",
            "minecraft_type": self.server_type,
            "minecraft_version": self.minecraft_version,
            "container_name": self.container_name,
            "data_directory": str(self.data_dir),
            "plugins_directory": str(self.plugins_dir),
            "config_directory": str(self.config_dir)
        }

        # If the server is running, get additional information
        if is_running:
            try:
                # Get container info
                _ = CommandExecutor.run(
                    ["docker", "inspect", self.container_name,
                        "--format", "{{json .}}"],
                    capture_output=True,
                    verbose=False
                )

                # Get server version from logs
                logs = CommandExecutor.run(
                    ["docker", "logs", self.container_name, "--tail", "100"],
                    capture_output=True,
                    verbose=False
                )

                # Extract useful information
                # Would require more parsing to get actual uptime
                status["uptime"] = "Running"

                # Try to extract Minecraft version from logs
                import re
                version_match = re.search(
                    r"Starting minecraft server version ([\d\.]+)", logs.stdout)
                if version_match:
                    status["version"] = version_match.group(1)
                else:
                    status["version"] = "Unknown"

                # Get player count and list
                try:
                    player_list = self._get_player_list()
                    status["player_count"] = len(player_list)
                    status["players"] = player_list
                    self.active_players = set(player_list)

                    # Update auto-shutdown with player list if enabled
                    if self.auto_shutdown_enabled:
                        self.auto_shutdown.update_player_list(player_list)
                except Exception as e:
                    logger.warning(f"Failed to get player information: {e}")
                    status["player_count"] = 0
                    status["players"] = []

                # Get metrics if monitoring is enabled
                if self.monitoring_enabled and self.monitor:
                    metrics = self.monitor.get_metrics()
                    for key, value in metrics.items():
                        # Add a subset of interesting metrics to status
                        if key in ["system_cpu_percent", "system_memory_percent",
                                   "container_cpu_percent", "container_memory_percent"]:
                            status[key] = value

            except Exception as e:
                Console.print_error(f"Error getting server details: {e}")

        return status

    def execute_command(self, command: str) -> str:
        """Execute a command on the server console"""
        if not self.is_running():
            Console.print_error("Server is not running")
            raise RuntimeError("Server must be running to execute commands")

        Console.print_info(f"Executing command: {command}")
        result = CommandExecutor.run(
            ["docker", "exec", self.container_name, "rcon-cli", command],
            capture_output=True
        )

        # Record activity for auto-shutdown
        if self.auto_shutdown_enabled:
            self.auto_shutdown.record_activity()

        return result.stdout

    def backup(self) -> Optional[Path]:
        """Create a backup of the server"""
        Console.print_header("Backing Up Minecraft Server")

        # Check if server is running and warn
        if self.is_running():
            Console.print_warning(
                "Creating backup while server is running. This might cause data corruption.")
            Console.print_warning(
                "It's recommended to stop the server before backing up.")

            # Notify server of backup
            try:
                self.execute_command(
                    "say SERVER BACKUP STARTING - Possible lag incoming")
            except Exception:
                pass

        try:
            # Create the backup
            backup_path, backup_size = FileManager.create_backup(
                self.data_dir,
                self.backup_dir
            )

            Console.print_success(
                f"Backup created successfully: {backup_path.name}")
            Console.print_success(f"Backup size: {backup_size}")

            # Clean up old backups (keep 5 latest)
            removed_count = FileManager.cleanup_old_backups(self.backup_dir, 5)
            if removed_count > 0:
                Console.print_warning(f"Removed {removed_count} old backup(s)")

            # Notify server if running
            if self.is_running():
                try:
                    self.execute_command("say SERVER BACKUP COMPLETED")
                except Exception:
                    pass

            return backup_path
        except Exception as e:
            Console.print_error(f"Backup failed: {e}")
            return None

    def restore(self, backup_path: Optional[Path] = None) -> bool:
        """Restore the server from a backup"""
        Console.print_header("Restoring Minecraft Server")

        # If no backup path provided, use the latest
        if not backup_path:
            backups = FileManager.list_backups(self.backup_dir)
            if not backups:
                Console.print_error("No backups found")
                return False

            backup_path = backups[0]  # Latest backup

        # Check if the backup exists
        if not os.path.exists(backup_path):
            Console.print_error(f"Backup not found: {backup_path}")
            return False

        # Confirm the server is not running
        if self.is_running():
            Console.print_warning(
                "Server must be stopped before restoring a backup")
            Console.print_warning("Stopping server...")
            self.stop()

        # Create a temporary directory for extraction
        temp_dir = self.base_dir / "temp_restore"

        # Extract and restore
        Console.print_info(f"Restoring from backup: {backup_path}")
        success = FileManager.extract_backup(
            backup_path,
            temp_dir,
            self.data_dir
        )

        # Clean up temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        if success:
            Console.print_success("Server restored successfully")
        else:
            Console.print_error("Failed to restore server")

        return success

    def get_logs(self, lines: int = 50) -> List[str]:
        """Get the most recent server logs"""
        if not self.is_running():
            Console.print_warning(
                "Server is not running, logs may be incomplete")

        result = CommandExecutor.run(
            ["docker", "logs", "--tail", str(lines), self.container_name],
            capture_output=True,
            verbose=False,
            check=False  # Don't fail if server isn't running
        )

        return result.stdout.splitlines()

    def install_mod(self, mod_id: str, source: str = "modrinth") -> bool:
        """
        Install a mod to the server

        Args:
            mod_id: ID or slug of the mod
            source: Source repository for the mod

        Returns:
            bool: True if installation was successful
        """
        Console.print_header("Installing Mod")

        # Check server type compatibility
        if not self.mod_manager.is_compatible(source):
            Console.print_error(
                f"Server type '{self.server_type}' is not compatible with {source} mods")
            return False

        Console.print_info(f"Installing mod {mod_id} from {source}...")
        success = self.mod_manager.install_mod(mod_id, source)

        if success:
            Console.print_success(f"Successfully installed mod {mod_id}")
            Console.print_info("Restart the server to apply changes")
        else:
            Console.print_error(f"Failed to install mod {mod_id}")

        return success

    def uninstall_mod(self, mod_id: str) -> bool:
        """
        Uninstall a mod from the server

        Args:
            mod_id: ID of the mod to uninstall

        Returns:
            bool: True if uninstallation was successful
        """
        Console.print_header("Uninstalling Mod")
        Console.print_info(f"Uninstalling mod {mod_id}...")

        success = self.mod_manager.uninstall_mod(mod_id)

        if success:
            Console.print_success(f"Successfully uninstalled mod {mod_id}")
            Console.print_info("Restart the server to apply changes")
        else:
            Console.print_error(f"Failed to uninstall mod {mod_id}")

        return success

    def list_mods(self) -> List[Dict[str, str]]:
        """
        List installed mods

        Returns:
            List of dictionaries containing mod information
        """
        return self.mod_manager.list_installed_mods()

    def configure_auto_shutdown(self, enabled: bool, timeout_minutes: int = 120) -> None:
        """
        Configure auto-shutdown behavior

        Args:
            enabled: Whether auto-shutdown should be enabled
            timeout_minutes: Inactivity minutes before shutdown
        """
        # Update configuration
        self.auto_shutdown_enabled = enabled
        self.auto_shutdown.inactivity_threshold = timeout_minutes
        self.auto_shutdown.enabled = enabled

        # Update monitoring state
        if enabled and self.is_running():
            self.auto_shutdown.start_monitoring()
            Console.print_info(
                f"Auto-shutdown enabled. Server will shut down after "
                f"{timeout_minutes} minutes of inactivity."
            )
        else:
            self.auto_shutdown.stop_monitoring()
            Console.print_info("Auto-shutdown disabled.")

    def _create_docker_compose_file(self) -> None:
        """Create or update docker-compose.yml with current settings"""
        compose_file = self.base_dir / "docker-compose.yml"

        # Basic docker-compose template
        compose_content = f"""version: '3'

services:
  minecraft:
    image: itzg/minecraft-server:java17
    container_name: {self.container_name}
    ports:
      - "25565:25565"
    environment:
      # EULA Agreement
      EULA: "TRUE"
      
      # Server type and version
      TYPE: "{self.server_type.upper()}"
      VERSION: "{self.minecraft_version}"
      
      # Performance settings
      MEMORY: "{self.memory}"
      JVM_XX_OPTS: "{self.java_flags}"
      USE_AIKAR_FLAGS: "true"
      
      # Game settings
      DIFFICULTY: "normal"
      MODE: "survival"
      MOTD: "Minecraft Server"
      
      # Security settings
      ENABLE_RCON: "true"
      RCON_PASSWORD: "minecraft"
      RCON_PORT: 25575
      ENFORCE_SECURE_PROFILE: "false"
      
      # Auto-shutdown
      ENABLE_AUTOPAUSE: "{str(self.auto_shutdown_enabled).lower()}"
      AUTOPAUSE_TIMEOUT_EST: "{self.auto_shutdown.inactivity_threshold * 60}"
      
    volumes:
      - ./data:/data
      - ./plugins:/plugins
      - ./config:/config
      - ./logs:/logs
    restart: unless-stopped
"""

        # Write the file
        with open(compose_file, 'w') as f:
            f.write(compose_content)

        Console.print_info(f"Created Docker Compose file: {compose_file}")

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
        configuration_changed = False

        if memory and memory != self.memory:
            self.memory = memory
            configuration_changed = True

        if minecraft_version and minecraft_version != self.minecraft_version:
            self.minecraft_version = minecraft_version
            configuration_changed = True

        if server_type and server_type.lower() != self.server_type:
            self.server_type = server_type.lower()
            configuration_changed = True

        if java_flags and java_flags != self.java_flags:
            self.java_flags = java_flags
            configuration_changed = True

        if configuration_changed:
            Console.print_info("Server configuration updated")
            self._create_docker_compose_file()
            Console.print_warning("Restart the server to apply changes")
        else:
            Console.print_info("No configuration changes made")
