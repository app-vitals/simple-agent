"""Tool for reading files."""

from pathlib import Path

from simple_agent.display import display_warning, print_tool_call
from simple_agent.tools.registry import register
from simple_agent.tools.utils import clean_path


def read_files(file_paths: list[str]) -> dict[str, str | None]:
    """Read and return the contents of one or more files.

    Args:
        file_paths: List of paths to read (can be a single path in a list)

    Returns:
        Dictionary mapping each file path to its contents or None if an error occurred
    """
    results: dict[str, str | None] = {}

    # Format file paths for display
    if len(file_paths) == 1:
        print_tool_call("read_files", file_path=file_paths[0])
    else:
        print_tool_call("read_files", file_paths=file_paths)

    # Read each file
    for path in file_paths:
        try:
            results[path] = Path(path).read_text()
        except Exception as e:
            display_warning(f"Error reading file: {clean_path(path)}", e)
            results[path] = None

    return results


# Register this tool with the registry
register(
    name="read_files",
    function=read_files,
    description="Read the contents of one or more files in a single operation for improved efficiency",
    parameters={
        "file_paths": {
            "type": "array",
            "description": "List of file paths to read (for efficiency, include multiple files when needed)",
            "items": {"type": "string"},
        }
    },
    returns="Dictionary mapping each file path to its content or None if an error occurred",
    requires_confirmation=False,  # Reading files doesn't modify the system
)
