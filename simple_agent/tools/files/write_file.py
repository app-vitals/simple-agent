"""Tool for writing files."""

from pathlib import Path

from simple_agent.display import (
    clean_path,
    display_warning,
    print_tool_call,
    print_tool_result,
)
from simple_agent.tools.files.diff_utils import write_file_confirmation_handler
from simple_agent.tools.registry import register


def write_file(file_path: str, content: str) -> bool:
    """Write content to a file.

    Args:
        file_path: Path to the file to write
        content: String content to write to the file

    Returns:
        True if successful, False otherwise
    """
    print_tool_call("write_file", file_path=file_path)

    try:
        Path(file_path).write_text(content)
        print_tool_result(
            "write_file", f"Successfully wrote file '{clean_path(file_path)}'"
        )
        return True
    except Exception as e:
        display_warning(f"Error writing file '{clean_path(file_path)}'", e)
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
