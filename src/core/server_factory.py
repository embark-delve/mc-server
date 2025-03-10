#!/usr/bin/env python3

"""
Server factory for creating appropriate server implementations
"""

import logging
from pathlib import Path
from typing import Optional, Type, ClassVar, Dict

from src.core.server_interface import MinecraftServer

# Configure logging
logger = logging.getLogger(__name__)


class ServerFactory:
    """Factory for creating Minecraft server instances"""

    # Dictionary of registered server implementations
    _implementations: ClassVar[Dict[str, Type[MinecraftServer]]] = {}

    @classmethod
    def register(cls, server_type: str, implementation: Type[MinecraftServer]) -> None:
        """
        Register a server implementation

        Args:
            server_type: String identifier for the server type
            implementation: Class implementing the MinecraftServer interface
        """
        cls._implementations[server_type] = implementation
        logger.info(f"Registered server implementation: {server_type}")

    @classmethod
    def create(
        cls, server_type: str, base_dir: Optional[Path] = None, **kwargs
    ) -> MinecraftServer:
        """
        Create a server instance of the specified type

        Args:
            server_type: Type of server to create (e.g., 'docker', 'aws', 'kubernetes')
            base_dir: Base directory for server files
            **kwargs: Additional arguments to pass to the server constructor

        Returns:
            MinecraftServer: An instance of the requested server type

        Raises:
            ValueError: If the requested server type is not registered
        """
        if server_type not in cls._implementations:
            raise ValueError(
                f"Unknown server type: {server_type}. "
                f"Available types: {list(cls._implementations.keys())}"
            )

        implementation = cls._implementations[server_type]
        return implementation(base_dir=base_dir, **kwargs)

    @classmethod
    def available_types(cls) -> list:
        """
        Get a list of available server types

        Returns:
            list: List of registered server types
        """
        return list(cls._implementations.keys())
