"""Tool for writing files."""

from pathlib import Path

from rich.console import Console

from simple_agent.tools.files.diff_utils import write_file_confirmation_handler
from simple_agent.tools.registry import register
from simple_agent.tools.utils import print_tool_call


def write_file(file_path: str, content: str) -> bool:
    """Write content to a file.

    Args:
        file_path: Path to the file to write
        content: String content to write to the file

    Returns:
        True if successful, False otherwise
    """
    console = Console()
    print_tool_call("write_file", file_path=file_path)

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
    confirmation_handler=write_file_confirmation_handler,
)
