#!/usr/bin/env python3

"""
Server factory for creating appropriate server implementations
"""

from typing import Optional, Type
from pathlib import Path

from src.core.server_interface import MinecraftServer


class ServerFactory:
    """Factory for creating server implementations"""

    # Dictionary of registered server implementations
    _implementations = {}

    @classmethod
    def register(cls, server_type: str, implementation: Type[MinecraftServer]) -> None:
        """
        Register a server implementation

        Args:
            server_type: String identifier for the server type
            implementation: Class implementing the MinecraftServer interface
        """
        cls._implementations[server_type.lower()] = implementation

    @classmethod
    def create(cls, server_type: str, base_dir: Optional[Path] = None, **kwargs) -> MinecraftServer:
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
        server_type = server_type.lower()

        if server_type not in cls._implementations:
            raise ValueError(f"Unknown server type: {server_type}. "
                             f"Available types: {', '.join(cls._implementations.keys())}")

        # Create a new instance of the requested implementation
        return cls._implementations[server_type](base_dir=base_dir, **kwargs)

    @classmethod
    def available_types(cls) -> list:
        """
        Get a list of available server types

        Returns:
            list: List of registered server types
        """
        return list(cls._implementations.keys())
