#!/usr/bin/env python3

"""
Tests for the Config class
"""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from src.utils.config import Config


class TestConfig:
    """Tests for the Config class"""

    def test_default_values(self):
        """Test that default values are set correctly"""
        config = Config()

        # Check server settings
        assert config.get("server.type") == "docker"
        assert config.get("server.version") == "latest"
        assert config.get("server.flavor") == "paper"
        assert config.get("server.memory") == "2G"

        # Check auto-shutdown settings
        assert config.get("auto_shutdown.enabled") is True
        assert config.get("auto_shutdown.timeout") == 120

        # Check monitoring settings
        assert config.get("monitoring.enabled") is True
        assert config.get("monitoring.prometheus") is True
        assert config.get("monitoring.cloudwatch") is False

        # Check debug mode
        assert config.get("debug") is False

    def test_from_file(self):
        """Test loading configuration from a file"""
        # Create a temporary config file
        config_data = {
            "server": {
                "type": "aws",
                "version": "1.19.2",
                "flavor": "forge",
                "memory": "4G",
            },
            "auto_shutdown": {
                "enabled": False,
                "timeout": 60,
            },
            "monitoring": {
                "enabled": False,
            },
            "paths": {
                "base_dir": "/tmp/minecraft",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml") as temp_file:
            yaml.dump(config_data, temp_file)
            temp_file.flush()

            # Load configuration from the file
            config = Config().from_file(temp_file.name)

            # Check that values were loaded correctly
            assert config.get("server.type") == "aws"
            assert config.get("server.version") == "1.19.2"
            assert config.get("server.flavor") == "forge"
            assert config.get("server.memory") == "4G"
            assert config.get("auto_shutdown.enabled") is False
            assert config.get("auto_shutdown.timeout") == 60
            assert config.get("monitoring.enabled") is False
            # Default value not overridden
            assert config.get("monitoring.prometheus") is True
            assert config.get("paths.base_dir") == Path("/tmp/minecraft")

    def test_from_env(self):
        """Test loading configuration from environment variables"""
        # Set environment variables
        with mock.patch.dict(os.environ, {
            "SERVER_TYPE": "aws",
            "MINECRAFT_VERSION": "1.19.2",
            "SERVER_FLAVOR": "forge",
            "SERVER_MEMORY": "4G",
            "AUTO_SHUTDOWN_ENABLED": "false",
            "AUTO_SHUTDOWN_TIMEOUT": "60",
            "MONITORING_ENABLED": "false",
            "DEBUG": "true",
        }):
            # Load configuration from environment variables
            config = Config().from_env()

            # Check that values were loaded correctly
            assert config.get("server.type") == "aws"
            assert config.get("server.version") == "1.19.2"
            assert config.get("server.flavor") == "forge"
            assert config.get("server.memory") == "4G"
            assert config.get("auto_shutdown.enabled") is False
            assert config.get("auto_shutdown.timeout") == 60
            assert config.get("monitoring.enabled") is False
            assert config.get("debug") is True

    def test_from_args(self):
        """Test loading configuration from command-line arguments"""
        # Create arguments dictionary
        args = {
            "type": "aws",
            "version": "1.19.2",
            "flavor": "forge",
            "memory": "4G",
            "disable_auto_shutdown": True,
            "timeout": 60,
            "debug": True,
        }

        # Load configuration from arguments
        config = Config().from_args(args)

        # Check that values were loaded correctly
        assert config.get("server.type") == "aws"
        assert config.get("server.version") == "1.19.2"
        assert config.get("server.flavor") == "forge"
        assert config.get("server.memory") == "4G"
        # Inverted from disable_auto_shutdown
        assert config.get("auto_shutdown.enabled") is False
        assert config.get("auto_shutdown.timeout") == 60
        assert config.get("debug") is True

    def test_precedence(self):
        """Test that configuration precedence is respected"""
        # Create a temporary config file
        config_data = {
            "server": {
                "type": "aws",
                "version": "1.18.2",
                "flavor": "forge",
                "memory": "2G",
            },
            "auto_shutdown": {
                "enabled": False,
                "timeout": 30,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml") as temp_file:
            yaml.dump(config_data, temp_file)
            temp_file.flush()

            # Set environment variables (should override file)
            with mock.patch.dict(os.environ, {
                "SERVER_TYPE": "docker",
                "MINECRAFT_VERSION": "1.19.2",
                "AUTO_SHUTDOWN_TIMEOUT": "60",
            }):
                # Create arguments dictionary (should override env and file)
                args = {
                    "version": "1.20.1",
                    "timeout": 120,
                }

                # Load configuration with precedence
                config = Config()
                config.from_file(temp_file.name)  # Lowest precedence
                config.from_env()                 # Medium precedence
                config.from_args(args)            # Highest precedence

                # Check that values respect precedence
                # From env, overrides file
                assert config.get("server.type") == "docker"
                # From args, overrides env and file
                assert config.get("server.version") == "1.20.1"
                # From file, not overridden
                assert config.get("server.flavor") == "forge"
                # From file, not overridden
                assert config.get("server.memory") == "2G"
                # From file, not overridden
                assert config.get("auto_shutdown.enabled") is False
                # From args, overrides env and file
                assert config.get("auto_shutdown.timeout") == 120

    def test_get_nonexistent_key(self):
        """Test getting a nonexistent key"""
        config = Config()

        # Should return the default value
        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"

    def test_get_all(self):
        """Test getting the entire configuration"""
        config = Config()

        # Should return a copy of the configuration
        all_config = config.get_all()
        assert isinstance(all_config, dict)
        assert "server" in all_config
        assert "auto_shutdown" in all_config
        assert "monitoring" in all_config

        # Modifying the returned dictionary should not affect the original
        all_config["server"]["type"] = "modified"
        assert config.get("server.type") == "docker"
