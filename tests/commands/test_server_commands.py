#!/usr/bin/env python3

"""
Tests for the server commands
"""

from pathlib import Path
from unittest import mock

import pytest

from src.commands import get_handler
from src.minecraft_server_manager import MinecraftServerManager


class TestServerCommands:
    """Tests for the server commands"""

    def setup_method(self):
        """Set up test fixtures"""
        # Import server commands to register them
        import src.commands.server_commands

        # Create a mock server manager
        self.manager = mock.MagicMock(spec=MinecraftServerManager)

    def test_start_command(self):
        """Test the start command"""
        # Get the start command handler
        start_handler = get_handler("start")
        assert start_handler is not None

        # Set up the manager mock
        self.manager.start.return_value = True
        self.manager.status.return_value = {"status": "running"}

        # Execute the command
        start_handler(self.manager, [])

        # Verify that the manager methods were called
        self.manager.start.assert_called_once()
        self.manager.status.assert_called_once()

    def test_stop_command(self):
        """Test the stop command"""
        # Get the stop command handler
        stop_handler = get_handler("stop")
        assert stop_handler is not None

        # Set up the manager mock
        self.manager.stop.return_value = True

        # Execute the command
        stop_handler(self.manager, [])

        # Verify that the manager methods were called
        self.manager.stop.assert_called_once()

    def test_restart_command(self):
        """Test the restart command"""
        # Get the restart command handler
        restart_handler = get_handler("restart")
        assert restart_handler is not None

        # Set up the manager mock
        self.manager.restart.return_value = True
        self.manager.status.return_value = {"status": "running"}

        # Execute the command
        restart_handler(self.manager, [])

        # Verify that the manager methods were called
        self.manager.restart.assert_called_once()
        self.manager.status.assert_called_once()

    def test_status_command(self):
        """Test the status command"""
        # Get the status command handler
        status_handler = get_handler("status")
        assert status_handler is not None

        # Set up the manager mock
        self.manager.status.return_value = {"status": "running"}

        # Execute the command
        status_handler(self.manager, [])

        # Verify that the manager methods were called
        self.manager.status.assert_called_once()

    def test_backup_command(self):
        """Test the backup command"""
        # Get the backup command handler
        backup_handler = get_handler("backup")
        assert backup_handler is not None

        # Set up the manager mock
        self.manager.backup.return_value = "/path/to/backup"

        # Execute the command
        backup_handler(self.manager, [])

        # Verify that the manager methods were called
        self.manager.backup.assert_called_once()

    def test_restore_command(self):
        """Test the restore command"""
        # Get the restore command handler
        restore_handler = get_handler("restore")
        assert restore_handler is not None

        # Set up the manager mock
        self.manager.restore.return_value = True

        # Execute the command with a backup path
        restore_handler(self.manager, ["/path/to/backup"])

        # Verify that the manager methods were called with the correct arguments
        # The Path object is created in the command handler, so we need to check the call differently
        assert self.manager.restore.call_count == 1
        args, kwargs = self.manager.restore.call_args
        assert len(args) == 1
        assert isinstance(args[0], Path)
        assert str(args[0]) == "/path/to/backup"

        # Reset the mock
        self.manager.restore.reset_mock()

        # Execute the command without a backup path
        restore_handler(self.manager, [])

        # Verify that the manager methods were called with None
        self.manager.restore.assert_called_once_with(None)

    def test_console_command_interactive(self):
        """Test the console command in interactive mode"""
        # Get the console command handler
        console_handler = get_handler("console")
        assert console_handler is not None

        # Set up the manager mock
        self.manager.execute_command.return_value = "Command output"

        # Mock the input function to simulate user input
        with mock.patch("builtins.input", side_effect=["list", "exit"]):
            # Mock the print function to capture output
            with mock.patch("builtins.print") as mock_print:
                # Execute the command without arguments (interactive mode)
                console_handler(self.manager, [])

                # Verify that the manager methods were called with the correct arguments
                self.manager.execute_command.assert_called_once_with("list")

                # Verify that the output was printed
                mock_print.assert_called_once_with("Command output")

    def test_console_command_single(self):
        """Test the console command with a single command"""
        # Get the console command handler
        console_handler = get_handler("console")
        assert console_handler is not None

        # Set up the manager mock
        self.manager.execute_command.return_value = "Command output"

        # Mock the print function to capture output
        with mock.patch("builtins.print") as mock_print:
            # Execute the command with arguments
            console_handler(self.manager, ["list", "players"])

            # Verify that the manager methods were called with the correct arguments
            self.manager.execute_command.assert_called_once_with(
                "list players")

            # Verify that the output was printed
            mock_print.assert_called_once_with("Command output")
