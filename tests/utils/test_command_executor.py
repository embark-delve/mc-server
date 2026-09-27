import sys

import pytest

from src.utils.command_executor import CommandExecutor


def test_shell_metacharacters_are_literal(tmp_path):
    marker = tmp_path / "should-not-exist"
    value = f"; touch {marker}"
    result = CommandExecutor.run(
        [sys.executable, "-c", "import sys; print(sys.argv[1])", value]
    )
    assert result.stdout.strip() == value
    assert not marker.exists()


def test_subprocess_deadline():
    with pytest.raises(RuntimeError, match="timed out"):
        CommandExecutor.run(
            [sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.01
        )


def test_failure_and_missing_executable(tmp_path):
    with pytest.raises(RuntimeError, match="exit 3"):
        CommandExecutor.run([sys.executable, "-c", "raise SystemExit(3)"])
    with pytest.raises(RuntimeError, match="not found"):
        CommandExecutor.run([str(tmp_path / "missing")])
