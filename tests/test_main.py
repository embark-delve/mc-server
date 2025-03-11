#!/usr/bin/env python3

"""
Tests for the main function
"""

import sys
from unittest import mock

import pytest

# Import the main module
import importlib.util
import os

# Get the absolute path to the main script
script_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "minecraft-server.py"))

# Load the module from the file path
spec = importlib.util.spec_from_file_location("main_module", script_path)
main_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_module)


class TestMain:
    """Tests for the main function"""

    def test_setup_argument_parser(self):
        """Test setting up the argument parser"""
        parser = main_module.setup_argument_parser()

        # Check that the parser has the expected arguments
        actions = {action.dest: action for action in parser._actions}

        assert "type" in actions
        assert "version" in actions
        assert "flavor" in actions
        assert "memory" in actions
        assert "disable_auto_shutdown" in actions
        assert "timeout" in actions
        assert "debug" in actions
        assert "config" in actions
        assert "command" in actions
        assert "args" in actions

    def test_main_function(self):
        """Test the main function"""
        # Mock the argument parser
        mock_parser = mock.MagicMock()
        mock_args = mock.MagicMock()
        mock_args.command = "status"
        mock_args.args = []
        mock_args.config = "config.yml"
        mock_parser.parse_args.return_value = mock_args

        # Mock the Config class
        mock_config = mock.MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "debug": False,
            "server.type": "docker",
            "server.version": "latest",
            "server.flavor": "paper",
            "auto_shutdown.enabled": True,
            "auto_shutdown.timeout": 120,
        }.get(key, default)

        # Mock the MinecraftServerManager
        mock_manager = mock.MagicMock()
        mock_manager_class = mock.MagicMock(return_value=mock_manager)

        # Mock the command handler
        mock_handler = mock.MagicMock()

        # Apply the mocks
        with mock.patch.object(main_module, "setup_argument_parser", return_value=mock_parser):
            with mock.patch("src.utils.config.Config", return_value=mock_config):
                with mock.patch("src.minecraft_server_manager.MinecraftServerManager", mock_manager_class):
                    with mock.patch("src.commands.get_handler", return_value=mock_handler):
                        # Call the main function
                        main_module.main()

                        # Verify that the mocks were called correctly
                        mock_parser.parse_args.assert_called_once()
                        mock_config.from_file.assert_called_once_with(
                            "config.yml")
                        mock_config.from_env.assert_called_once()
                        mock_config.from_args.assert_called_once()

                        # Verify that the manager was created with the correct arguments
                        mock_manager_class.assert_called_once_with(
                            server_type="docker",
                            minecraft_version="latest",
                            server_flavor="paper",
                            auto_shutdown_enabled=True,
                            auto_shutdown_timeout=120,
                        )

                        # Verify that the command handler was called with the correct arguments
                        mock_handler.assert_called_once_with(mock_manager, [])

    def test_main_function_error_handling(self):
        """Test error handling in the main function"""
        # Mock the argument parser
        mock_parser = mock.MagicMock()
        mock_args = mock.MagicMock()
        mock_args.command = "status"
        mock_args.args = []
        mock_args.config = "config.yml"
        mock_parser.parse_args.return_value = mock_args

        # Mock the Config class
        mock_config = mock.MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "debug": True,  # Enable debug mode for traceback
            "server.type": "docker",
            "server.version": "latest",
            "server.flavor": "paper",
            "auto_shutdown.enabled": True,
            "auto_shutdown.timeout": 120,
        }.get(key, default)

        # Mock the MinecraftServerManager
        mock_manager = mock.MagicMock()

        # Mock the command handler to raise an exception
        mock_handler = mock.MagicMock(side_effect=Exception("Test error"))

        # Mock sys.exit to prevent the test from exiting
        mock_exit = mock.MagicMock()

        # Apply the mocks
        with mock.patch.object(main_module, "setup_argument_parser", return_value=mock_parser):
            with mock.patch("src.utils.config.Config", return_value=mock_config):
                with mock.patch("src.minecraft_server_manager.MinecraftServerManager", return_value=mock_manager):
                    with mock.patch("src.commands.get_handler", return_value=mock_handler):
                        with mock.patch("sys.exit", mock_exit):
                            with mock.patch("traceback.print_exc") as mock_traceback:
                                # Call the main function
                                main_module.main()

                                # Verify that the error was handled correctly
                                mock_exit.assert_called_once_with(1)
                                mock_traceback.assert_called_once()

    def test_main_function_unknown_command(self):
        """Test handling of unknown commands in the main function"""
        # Mock the argument parser
        mock_parser = mock.MagicMock()
        mock_args = mock.MagicMock()
        mock_args.command = "unknown"
        mock_args.args = []
        mock_args.config = "config.yml"
        mock_parser.parse_args.return_value = mock_args

        # Mock the Config class
        mock_config = mock.MagicMock()

        # Mock the MinecraftServerManager
        mock_manager = mock.MagicMock()

        # Mock get_handler to return None (unknown command)
        mock_get_handler = mock.MagicMock(return_value=None)

        # Mock sys.exit to prevent the test from exiting
        mock_exit = mock.MagicMock()

        # Apply the mocks
        with mock.patch.object(main_module, "setup_argument_parser", return_value=mock_parser):
            with mock.patch("src.utils.config.Config", return_value=mock_config):
                with mock.patch("src.minecraft_server_manager.MinecraftServerManager", return_value=mock_manager):
                    with mock.patch("src.commands.get_handler", mock_get_handler):
                        with mock.patch("sys.exit", mock_exit):
                            # Call the main function
                            main_module.main()

                            # Verify that the error was handled correctly
                            mock_exit.assert_called_once_with(1)
