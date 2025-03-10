# Minecraft Server Manager

[![CI/CD](https://github.com/yourusername/minecraft-server/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/minecraft-server/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A Python-based utility for managing Minecraft servers across different deployment environments.

## Features

- **Multiple Deployment Options**: Run Minecraft servers on Docker or AWS
- **Server Management**: Start, stop, restart, and monitor your Minecraft server
- **Backup & Restore**: Create and manage server backups
- **Server Console**: Execute commands directly on the server
- **Resource Monitoring**: Track CPU, memory, and network usage
- **Auto-Shutdown**: Automatically shut down inactive servers to save resources
- **Mod Management**: Install, update, and manage server mods/plugins
- **Metrics Export**: Export metrics to Prometheus or AWS CloudWatch

## Installation

### Requirements

- Python 3.8+
- Docker (for local server deployment)
- AWS CLI (configured with appropriate permissions for AWS deployment)

### Setup

1. Clone the repository:

```
git clone https://github.com/yourusername/minecraft-server-manager.git
cd minecraft-server-manager
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. (Optional) Install development dependencies:

```
pip install -r requirements-dev.txt
```

## Usage

### Basic Usage

```python
from src.minecraft_server_manager import MinecraftServerManager

# Create a Docker-based server manager
manager = MinecraftServerManager(server_type="docker")

# Start the server
manager.start()

# Get server status
status = manager.status()

# Execute a command on the server
result = manager.execute_command("list")  # List online players

# Stop the server
manager.stop()
```

### Advanced Features

#### Auto-Shutdown

The auto-shutdown feature automatically stops the server when it's inactive for a specified period of time. This is useful for saving resources, especially on AWS deployments.

```python
# Configure auto-shutdown (enabled, timeout in minutes)
manager.configure_auto_shutdown(enabled=True, timeout_minutes=120)

# Get auto-shutdown status
status = manager.get_auto_shutdown_status()
```

#### Mod Management

Install and manage mods/plugins for your Minecraft server:

```python
# Install a mod from Modrinth
manager.install_mod("sodium", source="modrinth")

# Install a plugin from Bukkit/Spigot
manager.install_mod("worldedit", source="bukkit")

# List installed mods
mods = manager.list_mods()

# Uninstall a mod
manager.uninstall_mod("sodium")
```

#### Server Monitoring

Enable monitoring to track server performance metrics:

```python
# Create a server manager with monitoring enabled
manager = MinecraftServerManager(
    server_type="docker",
    monitoring_enabled=True,
    enable_prometheus=True,
    enable_cloudwatch=False  # Enable for AWS deployments
)

# Metrics are automatically collected when the server is running
# and can be viewed in the status() output
```

### CLI Example

The repository includes a CLI example script:

```
python examples/advanced_server_management.py --action start
python examples/advanced_server_management.py --action status
python examples/advanced_server_management.py --action install-mod --mod-id sodium
```

Run with `--help` to see all available options:

```
python examples/advanced_server_management.py --help
```

## Configuration

The Minecraft Server Manager can be configured with various options:

- **server_type**: Deployment type (docker or aws)
- **minecraft_version**: Version of Minecraft to run
- **server_flavor**: Server type (paper, spigot, vanilla, etc.)
- **auto_shutdown_enabled**: Whether to enable auto-shutdown
- **auto_shutdown_timeout**: Minutes of inactivity before shutdown
- **monitoring_enabled**: Whether to enable performance monitoring

## Development

### Running Tests

```
pytest
```

### Code Quality

```
ruff check src tests
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
