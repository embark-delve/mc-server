#!/usr/bin/env python3

"""
Advanced Minecraft Server Management Example

This example demonstrates how to use the advanced features of the Minecraft Server Manager
including:
- Auto-shutdown for inactive servers
- Mod/plugin installation and management
- Server monitoring and metrics
- Server configuration updates
"""

import argparse
import os
from pathlib import Path

from src.minecraft_server_manager import MinecraftServerManager
from src.utils.console import Console


def main():
    """Main function to demonstrate advanced server management"""
    parser = argparse.ArgumentParser(
        description="Advanced Minecraft Server Manager Example"
    )

    # Basic server options
    parser.add_argument(
        "--server-type",
        choices=["docker", "aws"],
        default="docker",
        help="Server type (docker or aws)",
    )
    parser.add_argument(
        "--minecraft-version", default="latest", help="Minecraft version to use"
    )
    parser.add_argument(
        "--server-flavor",
        default="paper",
        help="Server flavor (paper, spigot, vanilla, etc.)",
    )

    # Auto-shutdown options
    parser.add_argument(
        "--disable-auto-shutdown", action="store_true", help="Disable auto-shutdown"
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="Auto-shutdown timeout in minutes"
    )

    # Monitoring options
    parser.add_argument(
        "--disable-monitoring", action="store_true", help="Disable server monitoring"
    )
    parser.add_argument(
        "--disable-prometheus", action="store_true", help="Disable Prometheus metrics"
    )

    # Action options
    parser.add_argument(
        "--action",
        choices=[
            "start",
            "stop",
            "restart",
            "status",
            "backup",
            "restore",
            "install-mod",
            "uninstall-mod",
            "list-mods",
            "configure",
            "auto-shutdown-status",
            "execute-command",
            "logs",
        ],
        default="status",
        help="Action to perform",
    )

    # Action-specific options
    parser.add_argument("--mod-id", help="Mod ID for install/uninstall")
    parser.add_argument(
        "--mod-source", default="modrinth", help="Source for mod installation"
    )
    parser.add_argument("--command", help="Command to execute on server")
    parser.add_argument("--memory", help="Memory allocation (e.g., '2G')")
    parser.add_argument("--java-flags", help="Java JVM flags")

    args = parser.parse_args()

    # Set up the server manager
    base_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent

    Console.print_header("Minecraft Server Manager - Advanced Features Demo")
    Console.print_info(f"Server Type: {args.server_type}")
    Console.print_info(f"Minecraft Version: {args.minecraft_version}")
    Console.print_info(f"Server Flavor: {args.server_flavor}")
    Console.print_info(
        f"Auto-Shutdown: {'Disabled' if args.disable_auto_shutdown else 'Enabled'}"
    )
    Console.print_info(
        f"Monitoring: {'Disabled' if args.disable_monitoring else 'Enabled'}"
    )

    try:
        # Initialize the server manager
        manager = MinecraftServerManager(
            server_type=args.server_type,
            base_dir=base_dir,
            minecraft_version=args.minecraft_version,
            server_flavor=args.server_flavor,
            auto_shutdown_enabled=not args.disable_auto_shutdown,
            auto_shutdown_timeout=args.timeout,
            monitoring_enabled=not args.disable_monitoring,
            enable_prometheus=not args.disable_prometheus,
        )

        # Perform the selected action
        if args.action == "start":
            Console.print_header("Starting Server")
            success = manager.start()
            if success:
                Console.print_success("Server started successfully")
            else:
                Console.print_error("Failed to start server")

        elif args.action == "stop":
            Console.print_header("Stopping Server")
            success = manager.stop()
            if success:
                Console.print_success("Server stopped successfully")
            else:
                Console.print_error("Failed to stop server")

        elif args.action == "restart":
            Console.print_header("Restarting Server")
            success = manager.restart()
            if success:
                Console.print_success("Server restarted successfully")
            else:
                Console.print_error("Failed to restart server")

        elif args.action == "status":
            # Status output is handled by the manager
            manager.status()

        elif args.action == "backup":
            backup_path = manager.backup()
            if backup_path:
                Console.print_success(f"Backup created at: {backup_path}")
            else:
                Console.print_error("Backup failed")

        elif args.action == "restore":
            success = manager.restore()
            if success:
                Console.print_success("Server restored successfully")
            else:
                Console.print_error("Restore failed")

        elif args.action == "install-mod":
            if not args.mod_id:
                Console.print_error("Mod ID is required for installation")
                return

            Console.print_info(
                f"Installing mod {args.mod_id} from {args.mod_source}..."
            )
            success = manager.install_mod(args.mod_id, args.mod_source)
            if success:
                Console.print_success(f"Mod {args.mod_id} installed successfully")
            else:
                Console.print_error(f"Failed to install mod {args.mod_id}")

        elif args.action == "uninstall-mod":
            if not args.mod_id:
                Console.print_error("Mod ID is required for uninstallation")
                return

            Console.print_info(f"Uninstalling mod {args.mod_id}...")
            success = manager.uninstall_mod(args.mod_id)
            if success:
                Console.print_success(f"Mod {args.mod_id} uninstalled successfully")
            else:
                Console.print_error(f"Failed to uninstall mod {args.mod_id}")

        elif args.action == "list-mods":
            manager.list_mods()

        elif args.action == "configure":
            # Update server configuration if any options provided
            if any(
                [
                    args.memory,
                    args.minecraft_version,
                    args.server_flavor,
                    args.java_flags,
                ]
            ):
                Console.print_header("Updating Server Configuration")
                manager.update_server_configuration(
                    memory=args.memory,
                    minecraft_version=args.minecraft_version,
                    server_flavor=args.server_flavor,
                    java_flags=args.java_flags,
                )
                Console.print_info(
                    "Configuration updated. Restart the server to apply changes."
                )
            else:
                Console.print_warning("No configuration options provided")

        elif args.action == "auto-shutdown-status":
            manager.get_auto_shutdown_status()

        elif args.action == "execute-command":
            if not args.command:
                Console.print_error("Command is required")
                return

            Console.print_header(f"Executing command: {args.command}")
            result = manager.execute_command(args.command)
            Console.print_info("Command output:")
            for line in result.splitlines():
                Console.print_info(f"  {line}")

        elif args.action == "logs":
            manager.get_logs()

    except Exception as e:
        Console.print_error(f"Error: {e}")


if __name__ == "__main__":
    main()
