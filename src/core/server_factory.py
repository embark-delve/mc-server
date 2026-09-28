"""Factory for the supported local backend."""

from pathlib import Path
from typing import Any

from src.implementations.docker_server import DockerServer


class ServerFactory:
    @classmethod
    def available_types(cls) -> list[str]:
        return ["docker"]

    @classmethod
    def create(
        cls, server_type: str, base_dir: Path | None = None, **kwargs: Any
    ) -> DockerServer:
        if server_type != "docker":
            raise ValueError("Only Docker is supported")
        return DockerServer(base_dir=base_dir, **kwargs)
