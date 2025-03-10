#!/usr/bin/env python3

"""
Command executor utility for running shell commands
"""

import subprocess
from typing import List, Optional, Union
from pathlib import Path

from src.utils.console import Console


class CommandExecutor:
    """Utility class for executing shell commands"""

    @staticmethod
    def run(
        cmd: Union[List[str], str],
        cwd: Optional[Path] = None,
        capture_output: bool = False,
        check: bool = True,
        shell: bool = False,
        verbose: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run a shell command and handle errors

        Args:
            cmd: The command to run (list or string)
            cwd: Working directory to run the command in
            capture_output: Whether to capture command output
            check: Whether to check for command success
            shell: Whether to run the command in a shell
            verbose: Whether to print command details

        Returns:
            CompletedProcess: Result of the command execution

        Raises:
            subprocess.CalledProcessError: If the command fails and check is True
        """
        # Convert string command to list if not using shell
        if not shell and isinstance(cmd, str):
            cmd = cmd.split()

        # Print command info if verbose
        if verbose:
            cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
            Console.print_info(f"Running: {cmd_str}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                check=check,
                text=True,
                shell=shell,
                capture_output=capture_output
            )
            return result
        except subprocess.CalledProcessError as e:
            if verbose:
                Console.print_error(f"Error executing command: {e}")
                if capture_output:
                    Console.print_warning(f"STDOUT: {e.stdout}")
                    Console.print_error(f"STDERR: {e.stderr}")
            if check:
                raise
            return e
