"""
Command registry for Minecraft Server Manager
"""

from typing import Any, Callable, Dict, List, Optional

# Type for command handler functions
CommandHandler = Callable[..., None]

# Registry of available commands
_registry: Dict[str, CommandHandler] = {}


def register(command_name: str) -> Callable[[CommandHandler], CommandHandler]:
    """
    Decorator to register a command handler

    Args:
        command_name: Name of the command

    Returns:
        Decorator function
    """
    def decorator(handler: CommandHandler) -> CommandHandler:
        _registry[command_name] = handler
        return handler
    return decorator


def get_handler(command_name: str) -> Optional[CommandHandler]:
    """
    Get a command handler by name

    Args:
        command_name: Name of the command

    Returns:
        Command handler function or None if not found
    """
    return _registry.get(command_name)


def get_available_commands() -> List[str]:
    """
    Get a list of available commands

    Returns:
        List of registered command names
    """
    return list(_registry.keys())
