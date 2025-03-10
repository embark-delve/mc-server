#!/usr/bin/env python3

"""
Console utilities for terminal output formatting
"""

from typing import Any, Dict

from rich import box
from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.syntax import Syntax
from rich.table import Table


class Console:
    """Enhanced console output utilities using Rich"""

    # Main Rich console instance
    _console = RichConsole()

    @staticmethod
    def print_colored(message: str, style: str) -> None:
        """
        Print a message with the specified style

        Args:
            message: The message to print
            style: Rich style string (e.g., "bold green")
        """
        Console._console.print(message, style=style)

    @staticmethod
    def print_success(message: str) -> None:
        """Print a success message in green"""
        Console.print_colored(message, "bold green")

    @staticmethod
    def print_warning(message: str) -> None:
        """Print a warning message in yellow"""
        Console.print_colored(message, "bold yellow")

    @staticmethod
    def print_error(message: str) -> None:
        """Print an error message in red"""
        Console.print_colored(message, "bold red")

    @staticmethod
    def print_info(message: str) -> None:
        """Print an informational message in blue"""
        Console.print_colored(message, "bold blue")

    @staticmethod
    def print_header(title: str) -> None:
        """
        Print a formatted header with a title

        Args:
            title: The title to display in the header
        """
        Console._console.print(Panel(title, border_style="blue", expand=True))

    @staticmethod
    def print_status(status_data: Dict[str, Any]) -> None:
        """
        Print a status dictionary in a formatted table

        Args:
            status_data: Dictionary containing status information
        """
        table = Table(title="Server Status", box=box.ROUNDED)

        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        for key, value in status_data.items():
            # Format key for display (capitalize and replace underscores with spaces)
            display_key = key.replace("_", " ").title()

            # Format value based on type
            if isinstance(value, bool):
                display_value = "✓" if value else "✗"
                style = "green" if value else "red"
            elif isinstance(value, (int, float)) and "memory" in key.lower():
                display_value = f"{value} MB"
                style = "green"
            else:
                display_value = str(value)
                style = "green"

            table.add_row(display_key, display_value, style=style)

        Console._console.print(table)

    @staticmethod
    def create_progress() -> Progress:
        """
        Create a Rich progress bar for tracking operations

        Returns:
            Progress: A configured Rich progress bar
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[bold green]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        )

    @staticmethod
    def print_code(code: str, language: str = "python") -> None:
        """
        Print code with syntax highlighting

        Args:
            code: The code to display
            language: The programming language for syntax highlighting
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        Console._console.print(syntax)
