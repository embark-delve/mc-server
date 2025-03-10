#!/usr/bin/env python3

"""
Minecraft Server Manager main entry point
"""

import os
import logging
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

from src.core.server_interface import MinecraftServer
from src.implementations.docker_server import DockerServer
from src.implementations.aws_server import AWSServer
from src.utils.console import Console

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("server_manager")


class MinecraftServerManager:
    """Main Minecraft server manager class"""

    def __init__(
        self,
        server_type: str = "docker",
        base_dir: Optional[Path] = None,
        minecraft_version: str = "latest",
        server_flavor: str = "paper",
        auto_shutdown_enabled: bool = True,
        auto_shutdown_timeout: int = 120,  # 2 hours in minutes
        monitoring_enabled: bool = True,
        enable_prometheus: bool = True,
        enable_cloudwatch: bool = False,
        **kwargs
    ):
        """
        Initialize the Minecraft server manager

        Args:
            server_type: Type of server (docker, aws)
            base_dir: Base directory for the server
            minecraft_version: Version of Minecraft to use
            server_flavor: Server flavor (paper, spigot, vanilla, etc.)
            auto_shutdown_enabled: Whether to enable auto-shutdown
            auto_shutdown_timeout: Minutes of inactivity before shutdown
            monitoring_enabled: Whether to enable monitoring
            enable_prometheus: Whether to enable Prometheus metrics
            enable_cloudwatch: Whether to enable CloudWatch metrics
            **kwargs: Additional arguments to pass to the server implementation
        """
        # Set base directory if not provided
        if base_dir is None:
            base_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
        self.base_dir = base_dir

        # Initialize the server based on type
        server_type = server_type.lower()
        if server_type == "docker":
            self.server = DockerServer(
                base_dir=base_dir,
                minecraft_version=minecraft_version,
                server_type=server_flavor,
                auto_shutdown_enabled=auto_shutdown_enabled,
                auto_shutdown_timeout=auto_shutdown_timeout,
                monitoring_enabled=monitoring_enabled,
                enable_prometheus=enable_prometheus,
                enable_cloudwatch=enable_cloudwatch,
                **kwargs
            )
        elif server_type == "aws":
            self.server = AWSServer(
                base_dir=base_dir,
                minecraft_version=minecraft_version,
                server_type=server_flavor,
                auto_shutdown_enabled=auto_shutdown_enabled,
                auto_shutdown_timeout=auto_shutdown_timeout,
                monitoring_enabled=monitoring_enabled,
                enable_prometheus=enable_prometheus,
                enable_cloudwatch=True,  # Always enable CloudWatch for AWS
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported server type: {server_type}")

        logger.info(f"Initialized {server_type} server manager")

    def start(self) -> bool:
        """Start the Minecraft server"""
        return self.server.start()

    def stop(self) -> bool:
        """Stop the Minecraft server"""
        return self.server.stop()

    def restart(self) -> bool:
        """Restart the Minecraft server"""
        return self.server.restart()

    def status(self) -> Dict[str, Any]:
        """Get the current status of the server"""
        status = self.server.get_status()
        Console.print_header("Minecraft Server Status")
        Console.print_info(
            f"Server Type: {status.get('server_type', 'Unknown')}")
        Console.print_info(
            f"Minecraft Type: {status.get('minecraft_type', 'Unknown')}")
        Console.print_info(
            f"Running: {'Yes' if status.get('running', False) else 'No'}")

        if status.get('running', False):
            Console.print_info(f"Version: {status.get('version', 'Unknown')}")
            Console.print_info(f"Uptime: {status.get('uptime', 'Unknown')}")
            Console.print_info(f"Players: {status.get('player_count', 0)}")

            if status.get('players'):
                Console.print_info("Online players:")
                for player in status.get('players', []):
                    Console.print_info(f"  - {player}")

            # Display connection information with rich formatting
            Console.print_header("Connection Information")

            # For Docker servers (local)
            if status.get('server_type') == 'Docker':
                Console.print_success(
                    "Local Connection: [bold cyan]localhost[/bold cyan] or [bold cyan]127.0.0.1[/bold cyan]")
                # Try to get the local machine's IP for LAN connections
                import socket
                try:
                    hostname = socket.gethostname()
                    local_ip = socket.gethostbyname(hostname)
                    Console.print_success(
                        f"LAN Connection: [bold cyan]{local_ip}[/bold cyan]")
                except Exception:
                    Console.print_warning("Could not determine LAN IP address")

            # For AWS servers (remote)
            elif status.get('server_type') == 'AWS EC2':
                if 'public_ip' in status and status['public_ip'] != 'Unknown':
                    Console.print_success(
                        f"Public Connection: [bold cyan]{status['public_ip']}[/bold cyan]")
                if 'private_ip' in status and status['private_ip'] != 'Unknown':
                    Console.print_success(
                        f"Private Connection: [bold cyan]{status['private_ip']}[/bold cyan]")

            # For any server type
            Console.print_info(
                "Default Minecraft Port: [bold cyan]25565[/bold cyan]")
            Console.print_info(
                "Connection String: [bold cyan]<ip_address>:25565[/bold cyan]")

            # Display monitoring metrics if available
            metrics = [
                ('system_cpu_percent', 'System CPU Usage', '%'),
                ('system_memory_percent', 'System Memory Usage', '%'),
                ('container_cpu_percent', 'Container CPU Usage', '%'),
                ('container_memory_percent', 'Container Memory Usage', '%')
            ]

            Console.print_header("Resource Usage")
            for key, label, unit in metrics:
                if key in status:
                    Console.print_info(f"{label}: {status[key]}{unit}")

        return status

    def backup(self) -> Optional[Path]:
        """Create a backup of the server"""
        return self.server.backup()

    def restore(self, backup_path: Optional[Path] = None) -> bool:
        """Restore the server from a backup"""
        return self.server.restore(backup_path)

    def execute_command(self, command: str) -> str:
        """Execute a command on the server console"""
        return self.server.execute_command(command)

    def get_logs(self, lines: int = 50) -> List[str]:
        """Get the server logs"""
        logs = self.server.get_logs(lines)
        Console.print_header(f"Last {len(logs)} Log Lines")
        for line in logs:
            Console.print_info(line)
        return logs

    # Mod Management
    def install_mod(self, mod_id: str, source: str = "modrinth") -> bool:
        """Install a mod to the server"""
        return self.server.install_mod(mod_id, source)

    def uninstall_mod(self, mod_id: str) -> bool:
        """Uninstall a mod from the server"""
        return self.server.uninstall_mod(mod_id)

    def list_mods(self) -> List[Dict[str, str]]:
        """List installed mods"""
        mods = self.server.list_mods()

        if not mods:
            Console.print_info("No mods installed")
            return []

        Console.print_header("Installed Mods")
        for mod in mods:
            Console.print_info(f"- {mod['name']} (v{mod['version']})")
            Console.print_info(f"  ID: {mod['id']}")
            Console.print_info(f"  Source: {mod['source']}")

        return mods

    # Auto-shutdown Configuration
    def configure_auto_shutdown(
        self,
        enabled: bool = True,
        timeout_minutes: int = 120
    ) -> None:
        """
        Configure the auto-shutdown feature

        Args:
            enabled: Whether to enable auto-shutdown
            timeout_minutes: Minutes of inactivity before shutdown
        """
        self.server.configure_auto_shutdown(enabled, timeout_minutes)

        if enabled:
            Console.print_success(
                f"Auto-shutdown enabled. Server will shut down after "
                f"{timeout_minutes} minutes of inactivity"
            )
        else:
            Console.print_info("Auto-shutdown disabled")

    def get_auto_shutdown_status(self) -> dict:
        """
        Get the current status of the auto-shutdown feature

        Returns:
            dict: Auto-shutdown status information
        """
        status = self.server.auto_shutdown.get_status()

        Console.print_header("Auto-Shutdown Status")
        Console.print_info(f"Enabled: {status['enabled']}")
        Console.print_info(f"Active: {status['monitoring_active']}")
        Console.print_info(
            f"Inactive for: {status['inactive_minutes']} minutes")
        Console.print_info(
            f"Threshold: {status['shutdown_threshold_minutes']} minutes")
        Console.print_info(
            f"Shutdown in: {status['minutes_until_shutdown']} minutes")

        return status

    # Server Configuration
    def update_server_configuration(
        self,
        memory: Optional[str] = None,
        minecraft_version: Optional[str] = None,
        server_flavor: Optional[str] = None,
        java_flags: Optional[str] = None
    ) -> None:
        """
        Update server configuration

        Args:
            memory: Memory allocation (e.g., "2G")
            minecraft_version: Minecraft version to use
            server_flavor: Server flavor (paper, spigot, etc.)
            java_flags: Java JVM flags
        """
        self.server.update_server_configuration(
            memory=memory,
            minecraft_version=minecraft_version,
            server_type=server_flavor,
            java_flags=java_flags
        )
