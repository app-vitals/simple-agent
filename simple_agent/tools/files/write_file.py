"""Tool for writing files."""

from pathlib import Path

from rich.console import Console

from simple_agent.tools.registry import register


def write_file(file_path: str, content: str) -> bool:
    """Write content to a file.

    Args:
        file_path: Path to the file to write
        content: String content to write to the file

    Returns:
        True if successful, False otherwise
    """
    console = Console()
    console.print(f"[bold green]Writing:[/bold green] {file_path}")

    try:
        Path(file_path).write_text(content)
        return True
    except Exception as e:
        console.print(f"[bold red]Error writing file:[/bold red] {e}")
        return False


# Register this tool with the registry
register(
    name="write_file",
    function=write_file,
    description="Write content to a file",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the file to write",
        },
        "content": {
            "type": "string",
            "description": "Content to write to the file",
        },
    },
    returns="True if successful, False otherwise",
    requires_confirmation=True,  # Modifies the system
)
