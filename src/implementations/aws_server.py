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

from src.core.base_server import BaseMinecraftServer
from src.utils.auto_shutdown import AutoShutdown
from src.utils.command_executor import CommandExecutor
from src.utils.console import Console
from src.utils.file_manager import FileManager
from src.utils.mod_manager import ModManager
from src.utils.monitoring import ServerMonitor

# Configure logging
logger = logging.getLogger(__name__)


class AWSServer(BaseMinecraftServer):
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
        # Call parent constructor
        super().__init__(
            server_type=server_type,
            base_dir=base_dir,
            data_dir_name=data_dir_name,
            backup_dir_name=backup_dir_name,
            plugins_dir_name=plugins_dir_name,
            config_dir_name=config_dir_name,
            minecraft_version=minecraft_version,
            auto_shutdown_enabled=auto_shutdown_enabled,
            auto_shutdown_timeout=auto_shutdown_timeout,
            monitoring_enabled=monitoring_enabled,
            enable_prometheus=enable_prometheus,
            enable_cloudwatch=enable_cloudwatch,
        )

        # AWS-specific configuration
        self.instance_id = instance_id
        self.region = region
        self.ssh_key_path = ssh_key_path
        self.ssh_user = ssh_user

        # Initialize AWS clients
        self.ec2 = boto3.client("ec2", region_name=self.region)
        self.ssm = boto3.client("ssm", region_name=self.region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=self.region)

        # Initialize auto-shutdown
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

    def is_running(self) -> bool:
        """Check if the server is currently running"""
        if not self.instance_id:
            return False

        try:
            # Check if EC2 instance is running
            response = self.ec2.describe_instance_status(
                InstanceIds=[self.instance_id], IncludeAllInstances=True
            )

            if not response["InstanceStatuses"]:
                return False

            instance_state = response["InstanceStatuses"][0]["InstanceState"]["Name"]
            if instance_state != "running":
                return False

            # Check if Minecraft service is running
            command_response = self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": ["systemctl is-active minecraft.service"]
                },
            )

            command_id = command_response["Command"]["CommandId"]
            time.sleep(1)  # Wait for command to complete

            output = self.ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=self.instance_id,
            )

            return output["Status"] == "Success" and output["StandardOutputContent"].strip() == "active"

        except Exception as e:
            logger.error(f"Error checking if server is running: {e}")
            return False

    def _get_player_list(self) -> List[str]:
        """Get list of currently active players"""
        if not self.is_running():
            return []

        try:
            # Execute RCON command to get player list
            output = self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [
                    "cd /opt/minecraft && rcon-cli list"]},
            )

            command_id = output["Command"]["CommandId"]
            time.sleep(1)  # Wait for command to complete

            output = self.ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=self.instance_id,
            )

            # Parse player list from output
            # Example output: "There are 3 of 20 players online: player1, player2, player3"
            result = output.get("StandardOutputContent", "")
            if "players online:" in result:
                players_part = result.split("players online:")[1].strip()
                if players_part and players_part != ".":
                    player_list = [p.strip() for p in players_part.split(",")]

                    # Update auto-shutdown with player list
                    if self.auto_shutdown_enabled:
                        self.auto_shutdown.update_player_list(player_list)

                    return player_list
            return []
        except Exception as e:
            logger.error(f"Error getting player list: {e}")
            return []

    def start(self) -> bool:
        """Start the Minecraft server on AWS EC2"""
        Console.print_header("Starting Minecraft Server on AWS")
        Console.print_info("Starting Minecraft server...")

        if not self.instance_id:
            Console.print_info("Creating new EC2 instance...")
            # This would be a complex operation to create and configure a new EC2 instance
            # For simplicity, we're assuming the instance already exists
            raise ValueError(
                "Instance ID is required. Please provide an existing EC2 instance ID."
            )

        # Check if already running
        if self.is_running():
            Console.print_success("Server is already running")
            return True

        try:
            # First, ensure the EC2 instance is running
            instance_response = self.ec2.describe_instances(
                InstanceIds=[self.instance_id]
            )
            instance_state = instance_response["Reservations"][0]["Instances"][0]["State"]["Name"]

            if instance_state != "running":
                Console.print_info("Starting EC2 instance...")
                self.ec2.start_instances(InstanceIds=[self.instance_id])

                # Wait for instance to be running
                waiter = self.ec2.get_waiter("instance_running")
                waiter.wait(InstanceIds=[self.instance_id])

                # Wait a bit more for services to start
                time.sleep(30)
                Console.print_success("EC2 instance started")

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

            # Wait for server to start
            max_attempts = 12
            for attempt in range(1, max_attempts + 1):
                Console.print_info(
                    f"Waiting for server to initialize... ({attempt}/{max_attempts})"
                )
                time.sleep(10)  # Wait between checks

                if self.is_running():
                    Console.print_success("Server started successfully!")

                    # Start auto-shutdown if enabled
                    if self.auto_shutdown_enabled:
                        self.auto_shutdown.start_monitoring()

                    return True

            Console.print_error(
                "Server failed to start within the expected time")
            return False

        except Exception as e:
            Console.print_error(f"Error starting server: {e}")
            return False

    def stop(self) -> bool:
        """Stop the Minecraft server on AWS EC2"""
        Console.print_header("Stopping Minecraft Server on AWS")
        Console.print_info("Stopping Minecraft server...")

        if not self.is_running():
            Console.print_info("Server is already stopped")
            return True

        # Stop auto-shutdown monitoring
        if self.auto_shutdown_enabled:
            self.auto_shutdown.stop_monitoring()

        # Stop monitoring
        if self.monitoring_enabled and self.monitor:
            self.monitor.stop()

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

            # Verify server has stopped
            max_attempts = 6
            for attempt in range(1, max_attempts + 1):
                Console.print_info(
                    f"Verifying server has stopped... ({attempt}/{max_attempts})"
                )
                time.sleep(5)

                if not self.is_running():
                    Console.print_success("Server stopped successfully!")
                    return True

            Console.print_warning("Server may not have stopped properly")
            return False

        except Exception as e:
            Console.print_error(f"Error stopping server: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the AWS EC2 server"""
        is_running = self.is_running()

        status = {
            "running": is_running,
            "server_type": "AWS EC2",
            "minecraft_type": self.server_type,
            "minecraft_version": self.minecraft_version,
            "instance_id": self.instance_id or "Not set",
            "region": self.region,
            "data_directory": str(self.data_dir),
            "plugins_directory": str(self.plugins_dir),
            "config_directory": str(self.config_dir),
        }

        # If the server is running, get additional information
        if is_running:
            # Get player list
            players = self._get_player_list()
            status["player_count"] = len(players)
            status["players"] = players

            # Get auto-shutdown status
            auto_shutdown_status = self.auto_shutdown.get_status()
            status.update(auto_shutdown_status)

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
                launch_time = instance.get("LaunchTime", "Unknown")
                status["launch_time"] = str(launch_time)

                # Get server version
                version_cmd = self.ssm.send_command(
                    InstanceIds=[self.instance_id],
                    DocumentName="AWS-RunShellScript",
                    Parameters={
                        "commands": [
                            "cd /opt/minecraft",
                            "grep 'Starting minecraft server version' logs/latest.log | tail -1",
                        ]
                    },
                )

                command_id = version_cmd["Command"]["CommandId"]
                time.sleep(1)  # Wait for command to complete

                version_output = self.ssm.get_command_invocation(
                    CommandId=command_id,
                    InstanceId=self.instance_id,
                )

                version_text = version_output.get("StandardOutputContent", "")
                if "version" in version_text:
                    status["full_version"] = version_text.split("version")[
                        1].strip()

            except Exception as e:
                logger.error(f"Error getting detailed status: {e}")
                status["error"] = str(e)

        return status

    def execute_command(self, command: str) -> str:
        """Execute a command on the server console"""
        if not self.is_running():
            raise RuntimeError("Server is not running")

        try:
            output = self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [
                    f"cd /opt/minecraft && rcon-cli {command}"]},
            )

            command_id = output["Command"]["CommandId"]
            time.sleep(1)  # Wait for command to complete

            result = self.ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=self.instance_id,
            )

            if result["Status"] != "Success":
                raise RuntimeError(
                    f"Command execution failed: {result.get('StandardErrorContent', '')}")

            return result.get("StandardOutputContent", "").strip()

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            raise RuntimeError(f"Command execution failed: {e}")

    def backup(self) -> Optional[Path]:
        """Create a backup of the AWS EC2 server"""
        Console.print_header("Backing Up Minecraft Server on AWS")

        if not self.is_running():
            Console.print_warning(
                "Server is not running, backup may be incomplete")

        try:
            # Notify server of backup
            with contextlib.suppress(Exception):
                self.execute_command(
                    "say SERVER BACKUP STARTING - Possible lag incoming"
                )

            # Create a backup directory on the EC2 instance
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            remote_backup_path = f"/tmp/minecraft-backup-{timestamp}.zip"

            # Create backup on the EC2 instance
            backup_cmd = self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        "cd /opt/minecraft",
                        f"sudo zip -r {remote_backup_path} data",
                    ]
                },
            )

            command_id = backup_cmd["Command"]["CommandId"]

            # Wait for backup to complete
            Console.print_info("Creating backup on EC2 instance...")
            max_attempts = 30
            for attempt in range(1, max_attempts + 1):
                time.sleep(10)  # Check every 10 seconds

                result = self.ssm.get_command_invocation(
                    CommandId=command_id,
                    InstanceId=self.instance_id,
                )

                if result["Status"] in ["Success", "Failed", "Cancelled"]:
                    break

                Console.print_info(
                    f"Backup in progress... ({attempt}/{max_attempts})")

            if result["Status"] != "Success":
                Console.print_error(
                    f"Backup failed: {result.get('StandardErrorContent', '')}")
                return None

            # Download the backup from EC2 to local machine
            local_backup_path = self.backup_dir / \
                f"minecraft-backup-{timestamp}.zip"

            Console.print_info("Downloading backup from EC2 instance...")
            download_result = CommandExecutor.run(
                [
                    "scp",
                    "-i", self.ssh_key_path,
                    f"{self.ssh_user}@{self._get_instance_ip()}:{remote_backup_path}",
                    str(local_backup_path),
                ],
                capture_output=True,
            )

            if download_result.returncode != 0:
                Console.print_error(
                    f"Failed to download backup: {download_result.stderr}")
                return None

            # Clean up remote backup
            cleanup_cmd = self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        f"sudo rm {remote_backup_path}",
                    ]
                },
            )

            # Get backup size
            backup_size = FileManager.format_size(
                os.path.getsize(local_backup_path))

            Console.print_success(
                f"Backup created successfully: {local_backup_path.name}")
            Console.print_success(f"Backup size: {backup_size}")

            # Notify server if running
            with contextlib.suppress(Exception):
                self.execute_command("say SERVER BACKUP COMPLETED")

            return local_backup_path

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
            log_cmd = self.ssm.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        f"tail -n {lines} /opt/minecraft/logs/latest.log",
                    ]
                },
            )

            command_id = log_cmd["Command"]["CommandId"]
            time.sleep(1)  # Wait for command to complete

            result = self.ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=self.instance_id,
            )

            if result["Status"] != "Success":
                Console.print_error(
                    f"Failed to get logs: {result.get('StandardErrorContent', '')}")
                return []

            return result.get("StandardOutputContent", "").splitlines()

        except Exception as e:
            Console.print_error(f"Error getting logs: {e}")
            return []

    def install_mod(self, mod_id: str, source: str = "modrinth") -> bool:
        """Install a mod on the AWS EC2 server"""
        Console.print_header(f"Installing Mod: {mod_id}")

        if not self.mod_manager.is_compatible(source):
            Console.print_error(
                f"Server type '{self.server_type}' is not compatible with {source} mods"
            )
            return False

        # First download the mod locally
        if not self.mod_manager.install_mod(mod_id, source):
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
                f"{self.ssh_user}@{self._get_instance_ip()}:/tmp/"
            ],
            capture_output=True
        )

        if scp_result.returncode != 0:
            Console.print_error(
                f"Failed to upload mod: {scp_result.stderr}")
            return False

        # Move the mod to the server's plugins directory
        move_cmd = self.ssm.send_command(
            InstanceIds=[self.instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    f"sudo mv /tmp/{mod_file_path.name} /opt/minecraft/plugins/",
                    "sudo chown minecraft:minecraft /opt/minecraft/plugins/*",
                ]
            },
        )

        command_id = move_cmd["Command"]["CommandId"]
        time.sleep(1)  # Wait for command to complete

        result = self.ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=self.instance_id,
        )

        if result["Status"] != "Success":
            Console.print_error(
                f"Failed to install mod: {result.get('StandardErrorContent', '')}")
            return False

        Console.print_success(f"Successfully installed mod {mod_id}")
        Console.print_info("Restart the server for the mod to take effect")
        return True

    def uninstall_mod(self, mod_id: str) -> bool:
        """Uninstall a mod from the server"""
        Console.print_header(f"Uninstalling Mod: {mod_id}")

        if not self.is_running():
            Console.print_warning(
                "Server is not running, cannot uninstall mod")
            return False

        # First uninstall locally to update the mod registry
        success = self.mod_manager.uninstall_mod(mod_id)
        if not success:
            Console.print_error(
                f"Failed to uninstall mod {mod_id} locally")
            return False

        # Remove the mod from the server
        remove_cmd = self.ssm.send_command(
            InstanceIds=[self.instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    f"sudo rm -f /opt/minecraft/plugins/{mod_id}*.jar",
                ]
            },
        )

        command_id = remove_cmd["Command"]["CommandId"]
        time.sleep(1)  # Wait for command to complete

        result = self.ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=self.instance_id,
        )

        if result["Status"] != "Success":
            Console.print_error(
                f"Failed to uninstall mod: {result.get('StandardErrorContent', '')}")
            return False

        Console.print_success(f"Successfully uninstalled mod {mod_id}")
        Console.print_info("Restart the server for changes to take effect")
        return True

    def _get_instance_ip(self) -> str:
        """Get the public IP address of the EC2 instance"""
        try:
            response = self.ec2.describe_instances(
                InstanceIds=[self.instance_id])
            instance = response["Reservations"][0]["Instances"][0]
            return instance.get("PublicIpAddress", "Unknown")
        except Exception as e:
            logger.error(f"Error getting instance IP: {e}")
            return "Unknown"
