"""Offline configuration inspection; start/manage via the installed CLI."""

from src.implementations.docker_server import DockerServer
from src.utils.config import Config


def main() -> None:
    config = Config().from_file("config.yml").validate()
    server = DockerServer(config=config)
    print(f"Profile: {config.get('profile')}")
    print(f"Data: {server.data_dir}")
    print("No server was started. Use minecraft-server --help for supported commands.")


if __name__ == "__main__":
    main()
