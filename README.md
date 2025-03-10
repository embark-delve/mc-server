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

```bash
git clone https://github.com/yourusername/minecraft-server-manager.git
cd minecraft-server-manager
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Quick Start

The easiest way to get started is with the included command-line script:

```bash
# Start a server
python minecraft-server.py start

# Check server status
python minecraft-server.py status

# Execute a command on the server console
python minecraft-server.py console list

# Stop the server
python minecraft-server.py stop
```

Use debug mode for detailed logs:

```bash
python minecraft-server.py --debug start
```

## Usage

### Basic Usage

```python
from src.minecraft_server_manager import MinecraftServerManager

# Create a Docker-based server manager
manager = MinecraftServerManager(server_type="docker")

# Start the server
manager.start()

# Get server status (shows connection info)
status = manager.status()

# Execute a command on the server
result = manager.execute_command("list")  # List online players

# Stop the server
manager.stop()
```

### Deployment Options

#### Docker Deployment (Default)

```python
# Default setup - uses Docker with Paper server
manager = MinecraftServerManager(
    server_type="docker",
    minecraft_version="latest",  # Use specific version like "1.20.1" if needed
    server_flavor="paper"        # Options: paper, spigot, vanilla, forge, etc.
)
```

#### AWS Deployment

```python
# AWS deployment
manager = MinecraftServerManager(
    server_type="aws",
    minecraft_version="1.20.1",
    server_flavor="paper",
    # AWS specific settings
    region="us-west-2",
    instance_type="t3.medium",
    # Optional: use an existing instance
    instance_id="i-1234567890abcdef0"
)
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

### Configuration

The Minecraft Server Manager supports various configuration options:

```python
manager = MinecraftServerManager(
    # Basic settings
    server_type="docker",              # "docker" or "aws"
    base_dir=Path("/path/to/server"),  # Server files location
    minecraft_version="1.20.1",        # Minecraft version
    server_flavor="paper",             # Server type (paper, spigot, vanilla, etc.)

    # Performance settings
    memory="4G",                       # Memory allocation

    # Auto-shutdown settings
    auto_shutdown_enabled=True,        # Enable auto-shutdown
    auto_shutdown_timeout=120,         # Minutes of inactivity before shutdown

    # Monitoring settings
    monitoring_enabled=True,           # Enable performance monitoring
    enable_prometheus=True,            # Export metrics to Prometheus
    enable_cloudwatch=False            # Export metrics to CloudWatch
)
```

### CLI Script Options

```bash
python minecraft-server.py --help
```

Common options:

```bash
# Use a specific Minecraft version
python minecraft-server.py --version 1.20.1 start

# Specify server flavor
python minecraft-server.py --flavor forge start

# Set memory allocation
python minecraft-server.py --memory 4G start

# Disable auto-shutdown
python minecraft-server.py --disable-auto-shutdown start

# Enable debug logging
python minecraft-server.py --debug start
```

## Troubleshooting

### Common Issues

#### Server Won't Start

**Problem**: The server keeps restarting or fails to initialize.

**Solutions**:

1. Check the Docker logs:

   ```bash
   docker logs minecraft-server
   ```

2. Verify Java compatibility:
   If you see `UnsupportedClassVersionError`, you need to update the Java version:

   ```yaml
   # In docker-compose.yml
   image: itzg/minecraft-server:java21 # Use java17 for older Minecraft versions
   ```

3. Ensure you have enough memory:
   ```bash
   # Increase memory allocation
   python minecraft-server.py --memory 4G start
   ```

#### Connection Issues

**Problem**: Can't connect to the server from Minecraft.

**Solutions**:

1. Check server status to verify it's running:

   ```bash
   python minecraft-server.py status
   ```

2. Ensure you're using the correct IP address (check the status output)

3. Verify the port is open and not blocked by a firewall:

   ```bash
   # Test port connectivity
   telnet localhost 25565
   ```

4. For AWS servers, check security group settings to allow port 25565

#### "Address already in use" Error

**Problem**: Docker complains that the port is already in use.

**Solution**:

1. Check for existing containers using the port:

   ```bash
   docker ps -a | grep 25565
   ```

2. Stop and remove the conflicting container:
   ```bash
   docker stop <container_id>
   docker rm <container_id>
   ```

### Logs and Debugging

1. Enable debug mode for verbose logging:

   ```bash
   python minecraft-server.py --debug start
   ```

2. Check Minecraft server logs:

   ```bash
   docker exec minecraft-server cat /data/logs/latest.log
   ```

3. View Docker container logs:
   ```bash
   docker logs minecraft-server
   ```

### Detailed Troubleshooting Guide

For more detailed troubleshooting steps and solutions to common problems, refer to the [Troubleshooting Guide](docs/troubleshooting.md).

## Documentation

### Core Documentation

- [Server Configuration Guide](docs/server-configuration.md) - Complete reference for all server settings
- [Server Flavors Guide](docs/server-flavors.md) - Comparison of different server types (Vanilla, Paper, Forge, etc.)
- [Mods and Plugins Guide](docs/mods-and-plugins.md) - Managing and configuring mods and plugins

### Additional Guides

- [Docker Deployment](docs/docker-deployment.md) - Detailed Docker deployment instructions
- [AWS Deployment](docs/aws-deployment.md) - Deploying to AWS cloud
- [API Reference](docs/api-reference.md) - Complete Python API documentation

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
ruff check src tests
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
