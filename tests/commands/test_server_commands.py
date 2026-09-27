from unittest.mock import Mock

import pytest

from src.commands.server_commands import (
    handle_backup,
    handle_console,
    handle_restart,
    handle_restore,
    handle_start,
    handle_stop,
)


@pytest.mark.parametrize(
    ("handler", "method"),
    [(handle_start, "start"), (handle_stop, "stop"), (handle_restart, "restart")],
)
def test_failures_are_not_success(handler, method):
    manager = Mock()
    getattr(manager, method).return_value = False
    with pytest.raises(RuntimeError):
        handler(manager, [])


def test_restore_requires_path():
    with pytest.raises(ValueError):
        handle_restore(Mock(), [])


def test_console_is_one_command():
    manager = Mock()
    handle_console(manager, ["say", "hello"])
    manager.execute_command.assert_called_once_with("say hello")


def test_backup_exception_propagates():
    manager = Mock()
    manager.backup.side_effect = RuntimeError("running")
    with pytest.raises(RuntimeError, match="running"):
        handle_backup(manager, [])
