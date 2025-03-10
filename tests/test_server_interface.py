#!/usr/bin/env python3

"""
Tests for the server interface and implementations
"""

from src.utils.console import Console
from src.implementations.docker_server import DockerServer
from src.core.server_factory import ServerFactory
import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
import sys
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


class TestServerInterface(unittest.TestCase):
    """Test cases for server interface and implementations"""

    def setUp(self):
        """Set up test environment"""
        # Disable console output during tests
        self.console_patch = patch('src.utils.console.Console.print_colored')
        self.mock_console = self.console_patch.start()

        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

    def tearDown(self):
        """Clean up after tests"""
        # Remove the test directory
        shutil.rmtree(self.test_dir)

        # Stop the console patch
        self.console_patch.stop()

    def test_server_factory_registration(self):
        """Test server factory registration"""
        # Register a mock implementation
        class MockServer(DockerServer):
            pass

        ServerFactory.register("mock", MockServer)

        # Check if the implementation is registered
        self.assertIn("mock", ServerFactory.available_types())

    @patch('src.implementations.docker_server.CommandExecutor.run')
    def test_docker_server_is_running_true(self, mock_run):
        """Test DockerServer.is_running when server is running"""
        # Mock the command execution
        mock_process = MagicMock()
        mock_process.stdout = "minecraft-server"
        mock_run.return_value = mock_process

        # Create server instance
        server = DockerServer(base_dir=self.test_path)

        # Test is_running
        self.assertTrue(server.is_running())
        mock_run.assert_called_once()

    @patch('src.implementations.docker_server.CommandExecutor.run')
    def test_docker_server_is_running_false(self, mock_run):
        """Test DockerServer.is_running when server is not running"""
        # Mock the command execution
        mock_process = MagicMock()
        mock_process.stdout = "other-container"
        mock_run.return_value = mock_process

        # Create server instance
        server = DockerServer(base_dir=self.test_path)

        # Test is_running
        self.assertFalse(server.is_running())
        mock_run.assert_called_once()

    @patch('src.implementations.docker_server.CommandExecutor.run')
    @patch('src.implementations.docker_server.DockerServer.is_running')
    def test_docker_server_start_when_not_running(self, mock_is_running, mock_run):
        """Test DockerServer.start when server is not running"""
        # Mock is_running to return False
        mock_is_running.return_value = False

        # Create server instance
        server = DockerServer(base_dir=self.test_path)

        # Test start
        # Should return False since we don't mock the "Done" in logs
        self.assertFalse(server.start())
        mock_is_running.assert_called_once()
        # The implementation now calls run multiple times (for each check attempt)
        # We don't need to verify the exact number of calls, just that it was called at least once
        self.assertGreater(mock_run.call_count, 0)

    @patch('src.implementations.docker_server.DockerServer.is_running')
    def test_docker_server_start_when_already_running(self, mock_is_running):
        """Test DockerServer.start when server is already running"""
        # Mock is_running to return True
        mock_is_running.return_value = True

        # Create server instance
        server = DockerServer(base_dir=self.test_path)

        # Test start
        self.assertTrue(server.start())
        mock_is_running.assert_called_once()

    @patch('src.implementations.docker_server.CommandExecutor.run')
    @patch('src.implementations.docker_server.DockerServer.is_running')
    @patch('src.implementations.docker_server.DockerServer.execute_command')
    def test_docker_server_stop_when_running(self, mock_execute, mock_is_running, mock_run):
        """Test DockerServer.stop when server is running"""
        # Mock is_running to return True
        mock_is_running.return_value = True

        # Create server instance
        server = DockerServer(base_dir=self.test_path)

        # Test stop
        self.assertTrue(server.stop())
        mock_is_running.assert_called_once()
        mock_execute.assert_called_once_with("stop")
        mock_run.assert_called_once()

    @patch('src.implementations.docker_server.DockerServer.is_running')
    def test_docker_server_stop_when_not_running(self, mock_is_running):
        """Test DockerServer.stop when server is not running"""
        # Mock is_running to return False
        mock_is_running.return_value = False

        # Create server instance
        server = DockerServer(base_dir=self.test_path)

        # Test stop
        self.assertTrue(server.stop())
        mock_is_running.assert_called_once()

    @patch('src.implementations.docker_server.DockerServer.stop')
    @patch('src.implementations.docker_server.DockerServer.start')
    def test_docker_server_restart(self, mock_start, mock_stop):
        """Test DockerServer.restart"""
        # Mock stop and start to return True
        mock_stop.return_value = True
        mock_start.return_value = True

        # Create server instance
        server = DockerServer(base_dir=self.test_path)

        # Test restart
        self.assertTrue(server.restart())
        mock_stop.assert_called_once()
        mock_start.assert_called_once()

    @patch('src.implementations.docker_server.DockerServer.is_running')
    def test_docker_server_execute_command_not_running(self, mock_is_running):
        """Test DockerServer.execute_command when server is not running"""
        # Mock is_running to return False
        mock_is_running.return_value = False

        # Create server instance
        server = DockerServer(base_dir=self.test_path)

        # Test execute_command
        with self.assertRaises(RuntimeError):
            server.execute_command("test")
        mock_is_running.assert_called_once()

    @patch('src.implementations.docker_server.DockerServer.is_running')
    @patch('src.implementations.docker_server.CommandExecutor.run')
    def test_docker_server_execute_command_running(self, mock_run, mock_is_running):
        """Test DockerServer.execute_command when server is running"""
        # Mock is_running to return True
        mock_is_running.return_value = True

        # Mock command execution
        mock_process = MagicMock()
        mock_process.stdout = "Command output"
        mock_run.return_value = mock_process

        # Create server instance
        server = DockerServer(base_dir=self.test_path)

        # Test execute_command
        result = server.execute_command("test")
        self.assertEqual(result, "Command output")
        mock_is_running.assert_called_once()
        mock_run.assert_called_once()


if __name__ == '__main__':
    unittest.main()
