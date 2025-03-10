# API Reference

This document provides detailed information about the core interfaces and classes in the Minecraft Server Manager.

## Core Interfaces

### MinecraftServer

The `MinecraftServer` abstract base class defines the interface that all server implementations must implement.

```python
class MinecraftServer(ABC):
    """Abstract base class for all Minecraft server implementations"""

    @abstractmethod
    def start(self) -> bool:
        """
        Start the Minecraft server

        Returns:
            bool: True if server started successfully, False otherwise
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the Minecraft server

        Returns:
            bool: True if server stopped successfully, False otherwise
        """
        pass

    @abstractmethod
    def restart(self) -> bool:
        """
        Restart the Minecraft server

        Returns:
            bool: True if server restarted successfully, False otherwise
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """
        Check if the server is currently running

        Returns:
            bool: True if server is running, False otherwise
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Union[str, int, bool]]:
        """
        Get the current status of the server

        Returns:
            Dict: A dictionary containing status information
        """
        pass

    @abstractmethod
    def execute_command(self, command: str) -> str:
        """
        Execute a command on the server console

        Args:
            command: The command to execute

        Returns:
            str: Output from the command execution

        Raises:
            RuntimeError: If the server is not running
        """
        pass

    @abstractmethod
    def backup(self) -> Optional[Path]:
        """
        Create a backup of the server

        Returns:
            Optional[Path]: Path to the backup file if successful, None otherwise
        """
        pass

    @abstractmethod
    def restore(self, backup_path: Optional[Path] = None) -> bool:
        """
        Restore the server from a backup

        Args:
            backup_path: Path to the backup file to restore from.
                         If None, the latest backup will be used.

        Returns:
            bool: True if restored successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_logs(self, lines: int = 50) -> List[str]:
        """
        Get the most recent server logs

        Args:
            lines: Number of lines to retrieve

        Returns:
            List[str]: List of log lines
        """
        pass
```

## Factory and Manager Classes

### ServerFactory

The `ServerFactory` class is responsible for creating server instances based on the requested type. It uses a registry pattern to allow dynamic registration of server implementations.

```python
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
```

### MinecraftManager

The `MinecraftManager` class provides a unified interface for managing different server implementations.

```python
class MinecraftManager:
    """Main application class for Minecraft Server Manager"""

    def __init__(self, server_type: str = "docker", base_dir: Optional[Path] = None, **kwargs):
        """
        Initialize the Minecraft Server Manager

        Args:
            server_type: Type of server to manage (docker, aws, etc.)
            base_dir: Base directory for server files
            **kwargs: Additional arguments to pass to the server implementation
        """
        self.base_dir = base_dir or Path(os.path.dirname(os.path.abspath(__file__))).parent
        self._register_server_types()
        self.server_type = server_type
        self.server = self._create_server(server_type, **kwargs)

    def _register_server_types(self) -> None:
        """Register available server implementations"""
        ServerFactory.register("docker", DockerServer)
        ServerFactory.register("aws", AWSServer)

    # (Additional methods omitted for brevity)
```

## Server Implementations

### DockerServer

The `DockerServer` class implements the `MinecraftServer` interface for Docker-based deployments.

```python
class DockerServer(MinecraftServer):
    """Docker-based Minecraft server implementation"""

    def __init__(self,
                 base_dir: Optional[Path] = None,
                 container_name: str = "minecraft-server",
                 data_dir_name: str = "data",
                 backup_dir_name: str = "backups",
                 plugins_dir_name: str = "plugins",
                 config_dir_name: str = "config"):
        """
        Initialize a Docker-based Minecraft server

        Args:
            base_dir: Base directory for server files
            container_name: Name of the Docker container
            data_dir_name: Name of the data directory
            backup_dir_name: Name of the backups directory
            plugins_dir_name: Name of the plugins directory
            config_dir_name: Name of the config directory
        """
        # Implementation details omitted
```

### AWSServer

The `AWSServer` class implements the `MinecraftServer` interface for AWS EC2-based deployments.

```python
class AWSServer(MinecraftServer):
    """AWS EC2-based Minecraft server implementation"""

    def __init__(self,
                 base_dir: Optional[Path] = None,
                 instance_id: Optional[str] = None,
                 ssh_key_path: Optional[Path] = None,
                 ssh_user: str = "ec2-user",
                 region: str = "us-east-1",
                 data_dir_path: str = "/home/ec2-user/minecraft/data",
                 backup_dir_name: str = "backups"):
        """
        Initialize an AWS EC2-based Minecraft server

        Args:
            base_dir: Base directory for local files
            instance_id: EC2 instance ID
            ssh_key_path: Path to SSH key for EC2 instance
            ssh_user: SSH username for EC2 instance
            region: AWS region
            data_dir_path: Path to data directory on EC2 instance
            backup_dir_name: Name of the local backup directory
        """
        # Implementation details omitted
```

## Utility Classes

### Console

The `Console` class provides utilities for formatting terminal output.

```python
class Console:
    """Console output utilities with ANSI color formatting"""

    # ANSI Color codes
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

    @staticmethod
    def print_colored(message: str, color: str) -> None:
        """Print a message with the specified color"""
        print(f"{color}{message}{Console.NC}")

    # Additional methods omitted
```

### CommandExecutor

The `CommandExecutor` class provides utilities for executing shell commands.

```python
class CommandExecutor:
    """Utility class for executing shell commands"""

    @staticmethod
    def run(
        cmd: Union[List[str], str],
        cwd: Optional[Path] = None,
        capture_output: bool = False,
        check: bool = True,
        shell: bool = False,
        verbose: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run a shell command and handle errors

        Args:
            cmd: The command to run (list or string)
            cwd: Working directory to run the command in
            capture_output: Whether to capture command output
            check: Whether to check for command success
            shell: Whether to run the command in a shell
            verbose: Whether to print command details

        Returns:
            CompletedProcess: Result of the command execution

        Raises:
            subprocess.CalledProcessError: If the command fails and check is True
        """
        # Implementation details omitted
```

### FileManager

The `FileManager` class provides utilities for handling file operations.

```python
class FileManager:
    """Utility class for managing files and directories"""

    @staticmethod
    def ensure_directories(dirs: List[Path]) -> None:
        """Ensure that all specified directories exist"""
        # Implementation details omitted

    @staticmethod
    def get_file_size(file_path: Path) -> str:
        """Get human-readable file size"""
        # Implementation details omitted

    @staticmethod
    def create_backup(
        source_dir: Path,
        backup_dir: Path,
        backup_name: Optional[str] = None
    ) -> Tuple[Path, str]:
        """Create a backup of a directory"""
        # Implementation details omitted

    # Additional methods omitted
```

## Extending with New Server Types

To create a new server implementation, you need to:

1. Create a new class that inherits from `MinecraftServer`
2. Implement all the required abstract methods
3. Register the implementation with the `ServerFactory`

Here's an example:

```python
from src.core.server_interface import MinecraftServer

class KubernetesServer(MinecraftServer):
    """Kubernetes-based Minecraft server implementation"""

    def __init__(self,
                 base_dir: Optional[Path] = None,
                 namespace: str = "minecraft",
                 # other parameters...
                ):
        # Initialize your implementation

    def start(self) -> bool:
        # Implement start logic

    def stop(self) -> bool:
        # Implement stop logic

    # Implement all other required methods...

# Then register it with the ServerFactory
ServerFactory.register("kubernetes", KubernetesServer)
```

You can then use your implementation:

```python
server = ServerFactory.create("kubernetes", namespace="my-minecraft")
server.start()
```

## Command-Line Interface

The main module provides a command-line interface for managing servers:

```python
def main():
    """Main function for the command-line interface"""
    parser = argparse.ArgumentParser(description="Minecraft Server Manager")

    # Server type argument
    parser.add_argument("--type", "-t",
                        choices=["docker", "aws"],
                        default="docker",
                        help="Server type to manage")

    # Base directory argument
    parser.add_argument("--base-dir", "-d",
                        help="Base directory for server files")

    # AWS specific arguments
    parser.add_argument("--instance-id",
                        help="AWS EC2 instance ID (for AWS server type)")
    parser.add_argument("--region",
                        help="AWS region (for AWS server type)")
    parser.add_argument("--ssh-key",
                        help="Path to SSH key (for AWS server type)")

    # Command argument
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command subparsers (start, stop, etc.)
    # ...

    # Parse arguments and create manager
    args = parser.parse_args()
    manager = MinecraftManager(server_type=args.type, **server_kwargs)

    # Execute the command
    # ...
```

You can extend the command-line interface to support new server types and commands by adding new arguments and subparsers.
