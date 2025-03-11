#!/usr/bin/env python3

"""
Minecraft Server Manager
A Python tool for managing Minecraft servers with different deployment options

This is the main entry point for the application, providing a simple
command-line interface to the MinecraftServerManager.
"""

import src.commands.server_commands
from src.utils.console import Console
from src.utils.config import Config
from src.minecraft_server_manager import MinecraftServerManager
from src.commands import get_available_commands, get_handler
import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure that the src directory is in the Python path
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(script_dir))

# Import after setting up the path

# Import command handlers to register them


def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Set up the command-line argument parser

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Manage Minecraft servers with different deployment options"
    )

    # Server type
    parser.add_argument(
        "--type",
        choices=["docker", "aws"],
        help="Server deployment type (default: docker)",
    )

    # Server version
    parser.add_argument(
        "--version", help="Minecraft version to use (default: latest)"
    )

    # Server flavor
    parser.add_argument(
        "--flavor",
        help="Server flavor (paper, spigot, vanilla, etc.) (default: paper)",
    )

    # Memory allocation
    parser.add_argument(
        "--memory", help="Memory allocation for the server (default: 2G)"
    )

    # Auto-shutdown options
    parser.add_argument(
        "--disable-auto-shutdown",
        action="store_true",
        help="Disable auto-shutdown for inactive servers",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Auto-shutdown timeout in minutes (default: 120)",
    )

    # Debug mode
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")

    # Config file
    parser.add_argument(
        "--config",
        help="Path to configuration file (default: config.yml)",
        default="config.yml",
    )

    # Command
    parser.add_argument(
        "command",
        choices=get_available_commands(),
        help="Server management command",
    )

    # Additional command arguments
    parser.add_argument("args", nargs="*",
                        help="Additional arguments for the command")

    return parser


def main():
    """Main entry point for the Minecraft Server Manager CLI"""
    # Parse command-line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Load configuration with proper precedence
    config = Config()
    config.from_file(args.config)  # Load from config file (lowest precedence)
    config.from_env()              # Load from environment variables (medium precedence)
    # Load from command-line arguments (highest precedence)
    config.from_args(vars(args))

    # Configure logging
    log_level = logging.DEBUG if config.get("debug") else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Print header
    Console.print_header("Minecraft Server Manager")

    if config.get("debug"):
        Console.print_info("Debug mode enabled - verbose logging activated")

    # Initialize the server manager with the configuration
    manager = MinecraftServerManager(
        server_type=config.get("server.type"),
        minecraft_version=config.get("server.version"),
        server_flavor=config.get("server.flavor"),
        auto_shutdown_enabled=config.get("auto_shutdown.enabled"),
        auto_shutdown_timeout=config.get("auto_shutdown.timeout"),
    )

    # Get the command handler
    command_handler = get_handler(args.command)
    if not command_handler:
        Console.print_error(f"Unknown command: {args.command}")
        sys.exit(1)

    # Execute the command
    try:
        command_handler(manager, args.args)
    except Exception as e:
        Console.print_error(f"Error: {e!s}")
        if config.get("debug"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
