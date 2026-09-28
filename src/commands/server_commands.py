"""Compatibility command handlers; failures propagate to callers."""

from pathlib import Path

from src.commands import register
from src.minecraft_server_manager import MinecraftServerManager


@register("start")
def handle_start(manager: MinecraftServerManager, args: list[str]) -> None:
    if not manager.start():
        raise RuntimeError("Start failed")


@register("stop")
def handle_stop(manager: MinecraftServerManager, args: list[str]) -> None:
    if not manager.stop():
        raise RuntimeError("Stop failed")


@register("restart")
def handle_restart(manager: MinecraftServerManager, args: list[str]) -> None:
    if not manager.restart():
        raise RuntimeError("Restart failed")


@register("status")
def handle_status(manager: MinecraftServerManager, args: list[str]) -> None:
    print(manager.status())


@register("backup")
def handle_backup(manager: MinecraftServerManager, args: list[str]) -> None:
    print(manager.backup())


@register("restore")
def handle_restore(manager: MinecraftServerManager, args: list[str]) -> None:
    if not args:
        raise ValueError("An explicit backup is required")
    manager.restore(Path(args[0]))


@register("console")
def handle_console(manager: MinecraftServerManager, args: list[str]) -> None:
    if not args:
        raise ValueError("Supply one console command")
    print(manager.execute_command(" ".join(args)))
