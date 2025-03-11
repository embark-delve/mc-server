#!/usr/bin/env python3

"""
Tests for the command registry
"""

import pytest

from src.commands import register, get_handler, get_available_commands


# Test functions to be registered
def test_function_1():
    return "test_function_1"


def test_function_2():
    return "test_function_2"


class TestCommandRegistry:
    """Tests for the command registry"""

    def test_register_decorator(self):
        """Test registering a command with the decorator"""
        # Register a test function
        decorated_function = register("test_command")(test_function_1)

        # The decorator should return the original function
        assert decorated_function is test_function_1

        # The function should be registered
        handler = get_handler("test_command")
        assert handler is test_function_1
        assert handler() == "test_function_1"

    def test_get_handler(self):
        """Test getting a command handler"""
        # Register a test function
        register("another_command")(test_function_2)

        # Get the handler
        handler = get_handler("another_command")
        assert handler is test_function_2
        assert handler() == "test_function_2"

        # Getting a nonexistent handler should return None
        assert get_handler("nonexistent_command") is None

    def test_get_available_commands(self):
        """Test getting available commands"""
        # Get available commands
        commands = get_available_commands()

        # Should include the commands registered in previous tests
        assert "test_command" in commands
        assert "another_command" in commands

        # Register a new command
        @register("third_command")
        def test_function_3():
            return "test_function_3"

        # Should include the new command
        commands = get_available_commands()
        assert "third_command" in commands
