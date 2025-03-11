#!/usr/bin/env python3

"""
Command handlers for server operations
"""

import logging
from pathlib import Path
from typing import List, Optional

from src.commands import register
from src.minecraft_server_manager import MinecraftServerManager
from src.utils.console import Console

logger = logging.getLogger(__name__)


@register("start")
def handle_start(manager: MinecraftServerManager, args: List[str]) -> None:
    """
    Handle the 'start' command

    Args:
        manager: Server manager instance
        args: Additional command arguments
    """
    with Console.create_progress() as progress:
        task = progress.add_task("[cyan]Starting server...", total=100)
        progress.update(task, advance=50)

        success = manager.start()
        progress.update(task, completed=100)

        if success:
            Console.print_success("Server started successfully!")
            Console.print_status(manager.status())
        else:
            Console.print_error("Failed to start the server!")


@register("stop")
def handle_stop(manager: MinecraftServerManager, args: List[str]) -> None:
    """
    Handle the 'stop' command

    Args:
        manager: Server manager instance
        args: Additional command arguments
    """
    with Console.create_progress() as progress:
        task = progress.add_task("[cyan]Stopping server...", total=100)
        progress.update(task, advance=50)

        success = manager.stop()
        progress.update(task, completed=100)

        if success:
            Console.print_success("Server stopped successfully!")
        else:
            Console.print_error("Failed to stop the server!")


@register("restart")
def handle_restart(manager: MinecraftServerManager, args: List[str]) -> None:
    """
    Handle the 'restart' command

    Args:
        manager: Server manager instance
        args: Additional command arguments
    """
    with Console.create_progress() as progress:
        task = progress.add_task("[cyan]Restarting server...", total=100)
        progress.update(task, advance=50)

        success = manager.restart()
        progress.update(task, completed=100)

        if success:
            Console.print_success("Server restarted successfully!")
            Console.print_status(manager.status())
        else:
            Console.print_error("Failed to restart the server!")


@register("status")
def handle_status(manager: MinecraftServerManager, args: List[str]) -> None:
    """
    Handle the 'status' command

    Args:
        manager: Server manager instance
        args: Additional command arguments
    """
    with Console.create_progress() as progress:
        task = progress.add_task("[cyan]Getting server status...", total=100)
        progress.update(task, completed=100)

        Console.print_status(manager.status())


@register("backup")
def handle_backup(manager: MinecraftServerManager, args: List[str]) -> None:
    """
    Handle the 'backup' command

    Args:
        manager: Server manager instance
        args: Additional command arguments
    """
    with Console.create_progress() as progress:
        task = progress.add_task("[cyan]Creating backup...", total=100)
        progress.update(task, advance=25)

        backup_path = manager.backup()
        progress.update(task, completed=100)

        if backup_path:
            Console.print_success(
                f"Backup created successfully at: {backup_path}")
        else:
            Console.print_error("Failed to create backup!")


@register("restore")
def handle_restore(manager: MinecraftServerManager, args: List[str]) -> None:
    """
    Handle the 'restore' command

    Args:
        manager: Server manager instance
        args: Additional command arguments
    """
    backup_path = Path(args[0]) if args else None

    with Console.create_progress() as progress:
        task = progress.add_task("[cyan]Restoring backup...", total=100)
        progress.update(task, advance=25)

        success = manager.restore(backup_path)
        progress.update(task, completed=100)

        if success:
            Console.print_success("Backup restored successfully!")
        else:
            Console.print_error("Failed to restore backup!")


@register("console")
def handle_console(manager: MinecraftServerManager, args: List[str]) -> None:
    """
    Handle the 'console' command

    Args:
        manager: Server manager instance
        args: Additional command arguments
    """
    if not args:
        # Interactive console mode
        Console.print_info("Interactive console mode. Type 'exit' to quit.")
        while True:
            try:
                command = input("> ")
                if command.lower() in ("exit", "quit"):
                    break
                result = manager.execute_command(command)
                print(result)
            except KeyboardInterrupt:
                break
    else:
        # Execute a single command
        command = " ".join(args)
        result = manager.execute_command(command)
        print(result)
