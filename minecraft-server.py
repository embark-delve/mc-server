#!/usr/bin/env python3

"""
Minecraft Server Manager
A Python tool for managing Minecraft servers with different deployment options

This is the main entry point for the application, providing a simple
command-line interface to the MinecraftServerManager.
"""

from src.minecraft_server_manager import MinecraftServerManager
from src.utils.console import Console
import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

# Ensure that the src directory is in the Python path
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(script_dir))


def main():
    """Main entry point for the Minecraft Server Manager CLI"""

    parser = argparse.ArgumentParser(
        description="Manage Minecraft servers with different deployment options")

    # Server type
    parser.add_argument('--type', choices=['docker', 'aws'], default='docker',
                        help='Server deployment type (default: docker)')

    # Server version
    parser.add_argument('--version', default='latest',
                        help='Minecraft version to use (default: latest)')

    # Server flavor
    parser.add_argument('--flavor', default='paper',
                        help='Server flavor (paper, spigot, vanilla, etc.) (default: paper)')

    # Memory allocation
    parser.add_argument('--memory', default='2G',
                        help='Memory allocation for the server (default: 2G)')

    # Auto-shutdown options
    parser.add_argument('--disable-auto-shutdown', action='store_true',
                        help='Disable auto-shutdown for inactive servers')
    parser.add_argument('--timeout', type=int, default=120,
                        help='Auto-shutdown timeout in minutes (default: 120)')

    # Debug mode
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')

    # Command
    parser.add_argument('command', choices=['start', 'stop', 'restart', 'status', 'backup', 'restore', 'console'],
                        help='Server management command')

    # Additional command arguments
    parser.add_argument('args', nargs='*',
                        help='Additional arguments for the command')

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    Console.print_header("Minecraft Server Manager")

    if args.debug:
        Console.print_info("Debug mode enabled - verbose logging activated")

    # Initialize the server manager with the specified options
    manager = MinecraftServerManager(
        server_type=args.type,
        minecraft_version=args.version,
        server_flavor=args.flavor,
        auto_shutdown_enabled=not args.disable_auto_shutdown,
        auto_shutdown_timeout=args.timeout
    )

    # Process the command
    with Console.create_progress() as progress:
        task = progress.add_task(
            f"[cyan]Executing {args.command}...", total=100)

        try:
            if args.command == 'start':
                progress.update(task, advance=50)
                success = manager.start()
                progress.update(task, completed=100)

                if success:
                    Console.print_success("Server started successfully!")
                    Console.print_status(manager.status())
                else:
                    Console.print_error("Failed to start the server!")

            elif args.command == 'stop':
                progress.update(task, advance=50)
                success = manager.stop()
                progress.update(task, completed=100)

                if success:
                    Console.print_success("Server stopped successfully!")
                else:
                    Console.print_error("Failed to stop the server!")

            elif args.command == 'restart':
                progress.update(task, advance=50)
                success = manager.restart()
                progress.update(task, completed=100)

                if success:
                    Console.print_success("Server restarted successfully!")
                    Console.print_status(manager.status())
                else:
                    Console.print_error("Failed to restart the server!")

            elif args.command == 'status':
                progress.update(task, completed=100)
                Console.print_status(manager.status())

            elif args.command == 'backup':
                progress.update(task, advance=25)
                backup_path = manager.backup()
                progress.update(task, completed=100)

                if backup_path:
                    Console.print_success(
                        f"Backup created successfully at: {backup_path}")
                else:
                    Console.print_error("Failed to create backup!")

            elif args.command == 'restore':
                backup_path = args.args[0] if args.args else None
                progress.update(task, advance=25)
                success = manager.restore(backup_path)
                progress.update(task, completed=100)

                if success:
                    Console.print_success("Backup restored successfully!")
                else:
                    Console.print_error("Failed to restore backup!")

            elif args.command == 'console':
                progress.update(task, completed=100)

                if not args.args:
                    # Interactive console mode
                    Console.print_info(
                        "Interactive console mode. Type 'exit' to quit.")
                    while True:
                        try:
                            command = input("> ")
                            if command.lower() in ('exit', 'quit'):
                                break
                            result = manager.execute_command(command)
                            print(result)
                        except KeyboardInterrupt:
                            break
                else:
                    # Execute a single command
                    command = ' '.join(args.args)
                    result = manager.execute_command(command)
                    print(result)

        except Exception as e:
            Console.print_error(f"Error: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
