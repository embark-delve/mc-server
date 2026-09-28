"""Public local-server facade; cloud integrations are intentionally unavailable."""

from pathlib import Path
from typing import Any

from src.implementations.docker_server import DockerServer


class MinecraftServerManager(DockerServer):
    def __init__(
        self,
        server_type: str = "docker",
        base_dir: Path | None = None,
        server_flavor: str = "forge",
        **kwargs: Any,
    ) -> None:
        if server_type != "docker":
            raise ValueError(
                "Only Docker is supported; the unsafe AWS backend is disabled"
            )
        super().__init__(base_dir=base_dir, server_type=server_flavor, **kwargs)

    def status(self) -> dict[str, Any]:
        return self.get_status()

    def get_auto_shutdown_status(self) -> dict[str, bool]:
        return {"enabled": False, "monitoring_active": False}
