"""Bounded subprocess execution without shell interpretation."""

import shutil
import subprocess  # nosec B404
from pathlib import Path


class CommandExecutor:
    @staticmethod
    def run(
        cmd: list[str],
        cwd: Path | None = None,
        capture_output: bool = True,
        check: bool = True,
        timeout: float = 60,
        verbose: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        if (
            not isinstance(cmd, list)
            or not cmd
            or any(not isinstance(x, str) for x in cmd)
        ):
            raise ValueError("Commands must be a nonempty list of arguments")
        if cmd[0] == "docker" and shutil.which("docker") is None:
            bundled = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
            if bundled.is_file():
                cmd = [str(bundled), *cmd[1:]]
        try:
            return subprocess.run(  # noqa: S603 # nosec B603
                cmd,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                check=check,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(f"Executable not found: {cmd[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Operation timed out after {timeout}s: {cmd[0]}"
            ) from exc
        except subprocess.CalledProcessError as exc:
            # Arguments may contain a console command; do not echo them.
            raise RuntimeError(
                f"{cmd[0]} failed (exit {exc.returncode}): {exc.stderr or 'no diagnostic'}"
            ) from exc
