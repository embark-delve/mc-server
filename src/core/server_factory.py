#!/usr/bin/env python3

"""
Factory for creating Minecraft server instances
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Type

from src.core.base_server import BaseMinecraftServer
from src.core.server_interface import MinecraftServer
from src.implementations.aws_server import AWSServer
from src.implementations.docker_server import DockerServer
from src.utils.console import Console

# Configure logging
logger = logging.getLogger(__name__)


class ServerFactory:
    """Factory for creating Minecraft server instances"""

    # Registry of available server implementations
    _registry: Dict[str, Type[MinecraftServer]] = {}

    @classmethod
    def register(cls, server_type: str, implementation: Type[MinecraftServer]) -> None:
        """
        Register a server implementation

        Args:
            server_type: Type identifier for the server
            implementation: Class implementing MinecraftServer interface
        """
        cls._registry[server_type.lower()] = implementation
        logger.info(f"Registered server implementation: {server_type}")

    @classmethod
    def create(
        cls,
        server_type: str,
        base_dir: Optional[Path] = None,
        minecraft_version: str = "latest",
        minecraft_type: str = "paper",
        **kwargs,
    ) -> MinecraftServer:
        """
        Create a server instance of the specified type

        Args:
            server_type: Type of server to create (docker, aws, etc.)
            base_dir: Base directory for server files
            minecraft_version: Minecraft version to use
            minecraft_type: Type of Minecraft server (paper, spigot, etc.)
            **kwargs: Additional arguments for specific server types

        Returns:
            An instance of a MinecraftServer implementation
        """
        server_type = server_type.lower()

        # Set default base directory if not provided
        if not base_dir:
            base_dir = Path(os.path.dirname(
                os.path.abspath(__file__))) / "../.."
            base_dir = base_dir.resolve()  # Convert to absolute path

        # Check if server type is registered
        if server_type not in cls._registry:
            available_types = ", ".join(cls._registry.keys())
            Console.print_error(
                f"Unknown server type: {server_type}. Available types: {available_types}"
            )
            raise ValueError(f"Unknown server type: {server_type}")

        # Create server instance
        try:
            server_class = cls._registry[server_type]
            server = server_class(
                base_dir=base_dir,
                minecraft_version=minecraft_version,
                server_type=minecraft_type,
                **kwargs,
            )
            logger.info(
                f"Created {server_type} server with Minecraft {minecraft_type} {minecraft_version}"
            )
            return server
        except Exception as e:
            Console.print_error(f"Failed to create server: {e}")
            raise

    @classmethod
    def available_types(cls) -> List[str]:
        """
        Get a list of available server types

        Returns:
            List of registered server types
        """
        return list(cls._registry.keys())


# Register available server implementations
ServerFactory.register("docker", DockerServer)
ServerFactory.register("aws", AWSServer)
