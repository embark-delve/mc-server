#!/usr/bin/env python3

"""
Configuration management for Minecraft Server Manager
Handles loading configuration from different sources with proper precedence:
1. Command-line arguments (highest precedence)
2. Environment variables (.env file)
3. Configuration file (config.yml)
4. Default values (lowest precedence)
"""

import os
import logging
import copy
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for Minecraft Server Manager"""

    def __init__(self):
        """Initialize with default values"""
        self._config = {
            "server": {
                "type": "docker",
                "version": "latest",
                "flavor": "paper",
                "memory": "2G",
            },
            "auto_shutdown": {
                "enabled": True,
                "timeout": 120,
            },
            "monitoring": {
                "enabled": True,
                "prometheus": True,
                "cloudwatch": False,
            },
            "paths": {
                "base_dir": None,
            },
            "debug": False,
        }

    def from_file(self, config_path: Union[str, Path]) -> "Config":
        """
        Load configuration from a YAML file

        Args:
            config_path: Path to the configuration file

        Returns:
            Self for method chaining
        """
        config_path = Path(config_path)
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return self

        try:
            with open(config_path, "r") as f:
                file_config = yaml.safe_load(f)

            # Update configuration with values from file
            if file_config:
                # Server settings
                if "server" in file_config:
                    server_config = file_config["server"]
                    if "type" in server_config:
                        self._config["server"]["type"] = server_config["type"]
                    if "version" in server_config:
                        self._config["server"]["version"] = server_config["version"]
                    if "flavor" in server_config or "type" in server_config:
                        # Support both "flavor" and "type" for backwards compatibility
                        self._config["server"]["flavor"] = server_config.get(
                            "flavor", server_config.get("type", "paper")
                        )
                    if "memory" in server_config:
                        self._config["server"]["memory"] = server_config["memory"]

                # Auto-shutdown settings
                if "backup" in file_config:
                    backup_config = file_config["backup"]
                    # Process backup settings...

                # Auto-shutdown settings
                if "auto_shutdown" in file_config:
                    shutdown_config = file_config["auto_shutdown"]
                    if "enabled" in shutdown_config:
                        self._config["auto_shutdown"]["enabled"] = shutdown_config["enabled"]
                    if "timeout" in shutdown_config:
                        self._config["auto_shutdown"]["timeout"] = shutdown_config["timeout"]

                # Monitoring settings
                if "monitoring" in file_config:
                    monitoring_config = file_config["monitoring"]
                    if "enabled" in monitoring_config:
                        self._config["monitoring"]["enabled"] = monitoring_config["enabled"]
                    if "prometheus" in monitoring_config:
                        self._config["monitoring"]["prometheus"] = monitoring_config["prometheus"]
                    if "cloudwatch" in monitoring_config:
                        self._config["monitoring"]["cloudwatch"] = monitoring_config["cloudwatch"]

                # Paths
                if "paths" in file_config:
                    paths_config = file_config["paths"]
                    if "base_dir" in paths_config:
                        self._config["paths"]["base_dir"] = Path(
                            paths_config["base_dir"])

            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(
                f"Error loading configuration from {config_path}: {e}")

        return self

    def from_env(self) -> "Config":
        """
        Load configuration from environment variables

        Returns:
            Self for method chaining
        """
        # Load .env file if it exists
        load_dotenv()

        # Server settings
        if "SERVER_TYPE" in os.environ:
            self._config["server"]["type"] = os.environ["SERVER_TYPE"]
        if "MINECRAFT_VERSION" in os.environ:
            self._config["server"]["version"] = os.environ["MINECRAFT_VERSION"]
        if "SERVER_FLAVOR" in os.environ:
            self._config["server"]["flavor"] = os.environ["SERVER_FLAVOR"]
        if "SERVER_MEMORY" in os.environ:
            self._config["server"]["memory"] = os.environ["SERVER_MEMORY"]

        # Auto-shutdown settings
        if "AUTO_SHUTDOWN_ENABLED" in os.environ:
            self._config["auto_shutdown"]["enabled"] = os.environ["AUTO_SHUTDOWN_ENABLED"].lower(
            ) in ("true", "1", "yes")
        if "AUTO_SHUTDOWN_TIMEOUT" in os.environ:
            try:
                self._config["auto_shutdown"]["timeout"] = int(
                    os.environ["AUTO_SHUTDOWN_TIMEOUT"])
            except ValueError:
                logger.warning(
                    f"Invalid auto-shutdown timeout: {os.environ['AUTO_SHUTDOWN_TIMEOUT']}")

        # Monitoring settings
        if "MONITORING_ENABLED" in os.environ:
            self._config["monitoring"]["enabled"] = os.environ["MONITORING_ENABLED"].lower(
            ) in ("true", "1", "yes")
        if "PROMETHEUS_ENABLED" in os.environ:
            self._config["monitoring"]["prometheus"] = os.environ["PROMETHEUS_ENABLED"].lower(
            ) in ("true", "1", "yes")
        if "CLOUDWATCH_ENABLED" in os.environ:
            self._config["monitoring"]["cloudwatch"] = os.environ["CLOUDWATCH_ENABLED"].lower(
            ) in ("true", "1", "yes")

        # Paths
        if "BASE_DIR" in os.environ:
            self._config["paths"]["base_dir"] = Path(os.environ["BASE_DIR"])

        # Debug mode
        if "DEBUG" in os.environ:
            self._config["debug"] = os.environ["DEBUG"].lower() in (
                "true", "1", "yes")

        logger.info("Loaded configuration from environment variables")
        return self

    def from_args(self, args: Dict[str, Any]) -> "Config":
        """
        Load configuration from command-line arguments

        Args:
            args: Dictionary of command-line arguments

        Returns:
            Self for method chaining
        """
        # Server settings
        if "type" in args and args["type"] is not None:
            self._config["server"]["type"] = args["type"]
        if "version" in args and args["version"] is not None:
            self._config["server"]["version"] = args["version"]
        if "flavor" in args and args["flavor"] is not None:
            self._config["server"]["flavor"] = args["flavor"]
        if "memory" in args and args["memory"] is not None:
            self._config["server"]["memory"] = args["memory"]

        # Auto-shutdown settings
        if "disable_auto_shutdown" in args:
            self._config["auto_shutdown"]["enabled"] = not args["disable_auto_shutdown"]
        if "timeout" in args and args["timeout"] is not None:
            self._config["auto_shutdown"]["timeout"] = args["timeout"]

        # Debug mode
        if "debug" in args:
            self._config["debug"] = args["debug"]

        logger.info("Loaded configuration from command-line arguments")
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value

        Args:
            key: Dot-separated path to the configuration value
            default: Default value to return if the key is not found

        Returns:
            The configuration value or the default
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration

        Returns:
            A deep copy of the entire configuration as a dictionary
        """
        return copy.deepcopy(self._config)
