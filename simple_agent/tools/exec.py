"""Command execution tools."""

import subprocess

from rich.console import Console


def execute_command(command: str) -> tuple[str, str, int]:
    """Execute a shell command and return its output.

    Args:
        command: Command string to execute

    Returns:
        Tuple containing (stdout, stderr, return_code)
    """
    console = Console()
    console.print(f"[bold yellow]Executing:[/bold yellow] {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1
