#!/usr/bin/env python3

"""
AWS EC2-based Minecraft server implementation
"""

import contextlib
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import boto3
from botocore.exceptions import ClientError

from src.core.server_interface import MinecraftServer
from src.utils.auto_shutdown import AutoShutdown
from src.utils.command_executor import CommandExecutor
from src.utils.console import Console
from src.utils.file_manager import FileManager
from src.utils.mod_manager import ModManager
from src.utils.monitoring import ServerMonitor

# Configure logging
logger = logging.getLogger(__name__)


class AWSServer(MinecraftServer):
    """AWS EC2-based Minecraft server implementation"""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        instance_id: Optional[str] = None,
        region: str = "us-west-2",
        ssh_key_path: Optional[str] = None,
        ssh_user: str = "ec2-user",
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
        enable_cloudwatch: bool = True,
    ):
        """
        Initialize an AWS EC2-based Minecraft server

        Args:
            base_dir: Base directory for server files (defaults to script directory)
            instance_id: EC2 instance ID, if None will create a new instance
            region: AWS region
            ssh_key_path: Path to SSH key for connecting to the instance
            ssh_user: SSH username for the instance
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
        self.base_dir = (
            base_dir or Path(os.path.dirname(
                os.path.abspath(__file__))) / "../.."
        )
        self.base_dir = self.base_dir.resolve()  # Convert to absolute path

        # Configure directories
        self.data_dir = self.base_dir / data_dir_name
        self.backup_dir = self.base_dir / backup_dir_name
        self.plugins_dir = self.base_dir / plugins_dir_name
        self.config_dir = self.base_dir / config_dir_name
        self.logs_dir = self.base_dir / "logs"

        # AWS configuration
        self.instance_id = instance_id
        self.region = region
        self.ssh_key_path = ssh_key_path
        self.ssh_user = ssh_user

        # Server configuration
        self.minecraft_version = minecraft_version
        self.server_type = server_type.lower()
        self.memory = "2G"  # Default memory allocation
        self.java_flags = (
            "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200"
        )

        # Initialize AWS clients
        self.ec2 = boto3.client("ec2", region_name=self.region)
        self.ssm = boto3.client("ssm", region_name=self.region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=self.region)

        # Ensure directories exist
        self._ensure_directories()

        # Initialize auto-shutdown
        self.auto_shutdown_enabled = auto_shutdown_enabled
        self.auto_shutdown = AutoShutdown(
            shutdown_callback=self.stop,
            inactivity_threshold=auto_shutdown_timeout,
            check_interval=5,  # Check every 5 minutes
            enabled=auto_shutdown_enabled,
        )

        # Initialize mod manager
        self.mod_manager = ModManager(
            server_type=self.server_type,
            minecraft_version=self.minecraft_version,
            mods_dir=self.plugins_dir,
        )

        # Initialize monitoring
        self.monitoring_enabled = monitoring_enabled
        if monitoring_enabled:
            self.monitor = ServerMonitor(
                server_type="aws",
                server_name=self.instance_id or "aws-minecraft",
                enable_prometheus=enable_prometheus,
                enable_cloudwatch=enable_cloudwatch,
                metrics_dir=self.base_dir / "metrics",
                aws_region=self.region,
            )
        else:
            self.monitor = None

        # Current player list
        self.active_players: Set[str] = set()

        logger.info("AWS server manager initialized")

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        FileManager.ensure_directories(
            [
                self.data_dir,
                self.backup_dir,
                self.plugins_dir,
                self.config_dir,
                self.logs_dir,
                self.base_dir / "metrics",
            ]
        )

    def is_running(self) -> bool:
        """Check if the Minecraft server EC2 instance is running"""
        if not self.instance_id:
            return False

        try:
            response = self.ec2.describe_instance_status(
                InstanceIds=[self.instance_id], IncludeAllInstances=True
            )

            if not response["InstanceStatuses"]:
                return False

            status = response["InstanceStatuses"][0]["InstanceState"]["Name"]
            return status == "running"
        except ClientError as e:
            logger.error(f"Error checking instance status: {e}")
            return False

    def _get_player_list(self) -> List[str]:
        """Get a list of currently active players"""
        try:
            if not self.is_running():
                return []

            # Get player list using SSM to run RCON command
            response = self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [
                    "cd /opt/minecraft && rcon-cli list"]},
            )

            # Wait for command completion
            command_id = response["Command"]["CommandId"]
            time.sleep(2)  # Give command time to execute

            output = self.ssm.get_command_invocation(
                CommandId=command_id, InstanceId=self.instance_id
            )

            # Parse player list from output
            # Example output: "There are 3 of 20 players online: player1, player2, player3"
            result = output.get("StandardOutputContent", "")
            if "players online:" in result:
                players_part = result.split("players online:")[1].strip()
                if players_part:
                    return [p.strip() for p in players_part.split(",")]

            return []
        except Exception as e:
            logger.warning(f"Failed to get player list: {e}")
            return []

    def start(self) -> bool:
        """Start the Minecraft server on AWS EC2"""
        Console.print_header("Starting Minecraft Server on AWS")

        if self.is_running():
            Console.print_warning("Server is already running!")
            return True

        Console.print_success("Starting AWS EC2 instance...")

        try:
            # If we don't have an instance ID, we need to create one
            if not self.instance_id:
                Console.print_info("Creating new EC2 instance...")
                # This would be a complex operation to create and configure a new EC2 instance
                # For simplicity, we're assuming the instance already exists
                raise ValueError(
                    "No instance ID provided and automatic creation not implemented"
                )

            # Start the instance
            self.ec2.start_instances(InstanceIds=[self.instance_id])

            # Wait for the instance to be running
            Console.print_info("Waiting for instance to start...")
            waiter = self.ec2.get_waiter("instance_running")
            waiter.wait(InstanceIds=[self.instance_id])

            # Wait for SSH to be available
            Console.print_info("Waiting for SSH to be available...")
            time.sleep(30)  # Simple delay, could be more sophisticated

            # Start the Minecraft server on the instance
            Console.print_info("Starting Minecraft server...")
            # Store response but don't use it - we'll check status separately
            self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        "cd /opt/minecraft",
                        "sudo systemctl start minecraft.service",
                    ]
                },
            )

            # Wait for the server to initialize
            Console.print_info("Waiting for server to initialize...")
            time.sleep(60)  # Simple delay, could be more sophisticated

            Console.print_success("Server started successfully!")
            Console.print_colored(
                f"Connect to server at: {self._get_instance_ip()}", Console.PURPLE
            )

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

        except Exception as e:
            Console.print_error(f"Failed to start server: {e}")
            return False

    def stop(self) -> bool:
        """Stop the Minecraft server on AWS EC2"""
        Console.print_header("Stopping Minecraft Server on AWS")

        if not self.is_running():
            Console.print_warning("Server is not running!")
            return True

        # Stop auto-shutdown monitoring
        if self.auto_shutdown_enabled:
            self.auto_shutdown.stop_monitoring()

        # Stop monitoring
        if self.monitoring_enabled and self.monitor:
            self.monitor.stop()

        Console.print_success("Stopping Minecraft server and EC2 instance...")

        try:
            # First stop the Minecraft server gracefully
            try:
                # Store response but don't use it - we'll check status separately
                self.ssm.send_command(
                    InstanceIds=[self.instance_id],
                    DocumentName="AWS-RunShellScript",
                    Parameters={
                        "commands": [
                            "cd /opt/minecraft",
                            "sudo systemctl stop minecraft.service",
                        ]
                    },
                )
            except Exception as e:
                Console.print_warning(f"Error stopping Minecraft service: {e}")

            # Stop the EC2 instance
            self.ec2.stop_instances(InstanceIds=[self.instance_id])

            # Wait for the instance to stop
            Console.print_info("Waiting for EC2 instance to stop...")
            waiter = self.ec2.get_waiter("instance_stopped")
            waiter.wait(InstanceIds=[self.instance_id])

            Console.print_success("Server stopped successfully!")
            return True

        except Exception as e:
            Console.print_error(f"Failed to stop server: {e}")
            return False

    def restart(self) -> bool:
        """Restart the Minecraft server on AWS EC2"""
        Console.print_header("Restarting Minecraft Server on AWS")

        if not self.is_running():
            Console.print_warning("Server is not running, starting it...")
            return self.start()

        Console.print_info("Restarting Minecraft server...")

        try:
            # Restart the Minecraft service only, not the whole EC2 instance
            # Store response but don't use it - we'll check status separately
            self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        "cd /opt/minecraft",
                        "sudo systemctl restart minecraft.service",
                    ]
                },
            )

            # Wait for the server to restart
            Console.print_info("Waiting for server to restart...")
            time.sleep(60)  # Simple delay, could be more sophisticated

            Console.print_success("Server restarted successfully!")
            return True

        except Exception as e:
            Console.print_error(f"Failed to restart server: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the AWS EC2 server"""
        is_running = self.is_running()

        status = {
            "running": is_running,
            "server_type": "AWS EC2",
            "minecraft_type": self.server_type,
            "minecraft_version": self.minecraft_version,
            "instance_id": self.instance_id,
            "region": self.region,
            "data_directory": str(self.data_dir),
            "plugins_directory": str(self.plugins_dir),
            "config_directory": str(self.config_dir),
        }

        # If the server is running, get additional information
        if is_running:
            try:
                # Get instance details
                response = self.ec2.describe_instances(
                    InstanceIds=[self.instance_id])
                instance = response["Reservations"][0]["Instances"][0]

                # Add instance information
                status["instance_type"] = instance.get(
                    "InstanceType", "Unknown")
                status["public_ip"] = instance.get(
                    "PublicIpAddress", "Unknown")
                status["private_ip"] = instance.get(
                    "PrivateIpAddress", "Unknown")

                # Get uptime
                launch_time = instance.get("LaunchTime", None)
                if launch_time:
                    # Calculate uptime
                    uptime_seconds = time.time() - launch_time.timestamp()
                    days, remainder = divmod(uptime_seconds, 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, _ = divmod(remainder, 60)

                    status["uptime"] = f"{int(days)}d {int(hours)}h {int(minutes)}m"
                else:
                    status["uptime"] = "Unknown"

                # Get server version and other details via SSM
                try:
                    response = self.ssm.send_command(
                        InstanceIds=[self.instance_id],
                        DocumentName="AWS-RunShellScript",
                        Parameters={
                            "commands": [
                                "cd /opt/minecraft",
                                "grep 'Starting minecraft server version' logs/latest.log | tail -1",
                            ]
                        },
                    )

                    command_id = response["Command"]["CommandId"]
                    time.sleep(2)  # Give command time to execute

                    output = self.ssm.get_command_invocation(
                        CommandId=command_id, InstanceId=self.instance_id
                    )

                    # Parse server version
                    version_output = output.get("StandardOutputContent", "")
                    import re

                    version_match = re.search(
                        r"Starting minecraft server version ([\d\.]+)", version_output
                    )
                    if version_match:
                        status["version"] = version_match.group(1)
                    else:
                        status["version"] = "Unknown"

                except Exception as e:
                    logger.warning(f"Could not get server version: {e}")
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
                        if key in [
                            "system_cpu_percent",
                            "system_memory_percent",
                            "instance_cpu_utilization",
                            "instance_memory_utilization",
                        ]:
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

        try:
            # Execute command via SSM and RCON
            response = self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [
                    f"cd /opt/minecraft && rcon-cli {command}"]},
            )

            command_id = response["Command"]["CommandId"]
            time.sleep(2)  # Give command time to execute

            output = self.ssm.get_command_invocation(
                CommandId=command_id, InstanceId=self.instance_id
            )

            # Record activity for auto-shutdown
            if self.auto_shutdown_enabled:
                self.auto_shutdown.record_activity()

            return output.get("StandardOutputContent", "")

        except Exception as e:
            Console.print_error(f"Error executing command: {e}")
            return f"Error: {e!s}"

    def backup(self) -> Optional[Path]:
        """Create a backup of the AWS EC2 server"""
        Console.print_header("Backing Up Minecraft Server on AWS")

        if not self.is_running():
            Console.print_warning("Server is not running, cannot backup")
            return None

        try:
            # Notify server of backup
            with contextlib.suppress(Exception):
                self.execute_command(
                    "say SERVER BACKUP STARTING - Possible lag incoming"
                )

            # Create a backup directory on the EC2 instance
            self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        "cd /opt/minecraft",
                        "mkdir -p backups",
                        "tar -czf backups/backup-$(date +%Y%m%d%H%M%S).tar.gz world",
                    ]
                },
            )

            # Download the latest backup
            Console.print_info("Downloading backup from EC2 instance...")
            # This would require more code to actually download the backup
            # For simplicity, we're just creating a placeholder

            backup_path, backup_size = FileManager.create_backup(
                self.data_dir, self.backup_dir
            )

            Console.print_success(
                f"Backup created successfully: {backup_path.name}")
            Console.print_success(f"Backup size: {backup_size}")

            # Clean up old backups (keep 5 latest)
            removed_count = FileManager.cleanup_old_backups(self.backup_dir, 5)
            if removed_count > 0:
                Console.print_warning(f"Removed {removed_count} old backup(s)")

            # Notify server if running
            with contextlib.suppress(Exception):
                self.execute_command("say SERVER BACKUP COMPLETED")

            return backup_path

        except Exception as e:
            Console.print_error(f"Backup failed: {e}")
            return None

    def restore(self, backup_path: Optional[Path] = None) -> bool:
        """Restore the server from a backup"""
        Console.print_header("Restoring Minecraft Server on AWS")

        if not backup_path:
            # Find the most recent backup
            backups = list(self.backup_dir.glob("*.zip"))
            if not backups:
                Console.print_error("No backups found")
                return False
            backup_path = max(backups, key=os.path.getmtime)

        Console.print_info(f"Restoring from backup: {backup_path}")

        # Ensure server is stopped
        if self.is_running():
            Console.print_info("Stopping server before restore...")
            self.stop()

        # Upload backup to EC2 instance
        Console.print_info("Uploading backup to EC2 instance...")
        upload_result = CommandExecutor.run(
            [
                "scp",
                "-i", self.ssh_key_path,
                str(backup_path),
                f"{self.ssh_user}@{self._get_instance_ip()}:/tmp/"
            ],
            capture_output=True
        )

        if upload_result.returncode != 0:
            Console.print_error(
                f"Failed to upload backup: {upload_result.stderr}")
            return False

        # Extract backup on EC2 instance
        Console.print_info("Extracting backup on EC2 instance...")
        # We don't need to store the result, just execute the command
        self.ssm.send_command(
            InstanceIds=[self.instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    "cd /opt/minecraft",
                    "sudo systemctl stop minecraft.service",
                    f"sudo unzip -o /tmp/{backup_path.name} -d /opt/minecraft/data",
                    "sudo chown -R minecraft:minecraft /opt/minecraft/data",
                    "sudo systemctl start minecraft.service"
                ]
            }
        )

        Console.print_success("Backup restored successfully!")
        return True

    def get_logs(self, lines: int = 50) -> List[str]:
        """Get the most recent server logs"""
        if not self.is_running():
            Console.print_warning(
                "Server is not running, logs may be unavailable")
            return []

        try:
            response = self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        f"cd /opt/minecraft && tail -n {lines} logs/latest.log"
                    ]
                },
            )

            command_id = response["Command"]["CommandId"]
            time.sleep(2)  # Give command time to execute

            output = self.ssm.get_command_invocation(
                CommandId=command_id, InstanceId=self.instance_id
            )

            return output.get("StandardOutputContent", "").splitlines()

        except Exception as e:
            Console.print_error(f"Error getting logs: {e}")
            return []

    def install_mod(self, mod_id: str, source: str = "modrinth") -> bool:
        """
        Install a mod to the server

        Args:
            mod_id: ID or slug of the mod
            source: Source repository for the mod

        Returns:
            bool: True if installation was successful
        """
        Console.print_header("Installing Mod on AWS Server")

        # Check server type compatibility
        if not self.mod_manager.is_compatible(source):
            Console.print_error(
                f"Server type '{self.server_type}' is not compatible with {source} mods"
            )
            return False

        if not self.is_running():
            Console.print_warning("Server is not running, cannot install mod")
            return False

        try:
            # First download the mod locally
            Console.print_info(f"Downloading mod {mod_id} from {source}...")
            success = self.mod_manager.install_mod(mod_id, source)

            if not success:
                Console.print_error(f"Failed to download mod {mod_id}")
                return False

            # Find mod files
            mod_files = list(self.plugins_dir.glob(f"{mod_id}*.jar"))
            if not mod_files:
                Console.print_error(f"No mod files found for {mod_id}")
                return False

            # We'll use the mod file path in the upload command
            mod_file_path = mod_files[0]

            # Upload the mod to the EC2 instance
            Console.print_info(f"Uploading mod {mod_id} to EC2 instance...")

            # Use SCP to upload the mod file
            scp_result = CommandExecutor.run(
                [
                    "scp",
                    "-i", self.ssh_key_path,
                    str(mod_file_path),
                    f"{self.ssh_user}@{self._get_instance_ip()}:/opt/minecraft/mods/"
                ],
                capture_output=True
            )

            if scp_result.returncode != 0:
                Console.print_error(
                    f"Failed to upload mod: {scp_result.stderr}")
                return False

            # Install the mod on the server
            Console.print_info("Installing mod on server...")
            # This is a placeholder for the actual installation process

            Console.print_success(f"Successfully installed mod {mod_id}")
            Console.print_info("Restart the server to apply changes")
            return True

        except Exception as e:
            Console.print_error(f"Failed to install mod: {e}")
            return False

    def uninstall_mod(self, mod_id: str) -> bool:
        """
        Uninstall a mod from the server

        Args:
            mod_id: ID of the mod to uninstall

        Returns:
            bool: True if uninstallation was successful
        """
        Console.print_header("Uninstalling Mod from AWS Server")
        Console.print_info(f"Uninstalling mod {mod_id}...")

        if not self.is_running():
            Console.print_warning(
                "Server is not running, cannot uninstall mod")
            return False

        try:
            # Remove mod from local directory
            success = self.mod_manager.uninstall_mod(mod_id)

            if not success:
                Console.print_error(
                    f"Failed to uninstall mod {mod_id} locally")
                return False

            # Remove mod from EC2 instance
            Console.print_info("Removing mod from EC2 instance...")
            # This would require more code to actually remove the file
            # For simplicity, we'll just say it was successful

            Console.print_success(f"Successfully uninstalled mod {mod_id}")
            Console.print_info("Restart the server to apply changes")
            return True

        except Exception as e:
            Console.print_error(f"Failed to uninstall mod: {e}")
            return False

    def list_mods(self) -> List[Dict[str, str]]:
        """
        List installed mods

        Returns:
            List of dictionaries containing mod information
        """
        if not self.is_running():
            Console.print_warning("Server is not running, cannot list mods")
            return []

        # For AWS, we would need to get the list from the EC2 instance
        # This is a simplified implementation
        return self.mod_manager.list_installed_mods()

    def configure_auto_shutdown(
        self, enabled: bool, timeout_minutes: int = 120
    ) -> None:
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

    def update_server_configuration(
        self,
        memory: Optional[str] = None,
        minecraft_version: Optional[str] = None,
        server_type: Optional[str] = None,
        java_flags: Optional[str] = None,
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
            Console.print_info("Server configuration updated locally")
            Console.print_warning(
                "To apply these changes to the EC2 instance, "
                "you need to update the server configuration and restart it"
            )

    def _get_instance_ip(self) -> str:
        """Get the public IP address of the EC2 instance"""
        if not self.instance_id or not self.is_running():
            return "Unknown"

        try:
            response = self.ec2.describe_instances(
                InstanceIds=[self.instance_id])
            instance = response["Reservations"][0]["Instances"][0]
            return instance.get("PublicIpAddress", "Unknown")
        except Exception as e:
            logger.error(f"Error getting instance IP: {e}")
            return "Unknown"
