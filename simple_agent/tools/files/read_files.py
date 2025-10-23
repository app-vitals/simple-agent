"""Tool for reading files."""

from pathlib import Path

from simple_agent.display import clean_path, display_warning, print_tool_call
from simple_agent.tools.registry import register


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


def format_read_files_result(content: str) -> str:
    """Format read_files result for display.

    Args:
        content: Raw result string (dict representation)

    Returns:
        Formatted string for display
    """
    import ast

    try:
        # Parse the dict string
        result = ast.literal_eval(content)
        if isinstance(result, dict):
            # Show summary of files read (don't display file content, too verbose)
            success_count = sum(1 for v in result.values() if v is not None)
            total_count = len(result)
            if success_count == total_count:
                if total_count == 1:
                    return "[green]✓ File read successfully[/green]"
                else:
                    return f"[green]✓ {total_count} files read successfully[/green]"
            else:
                failed_count = total_count - success_count
                return f"[yellow]✓ {success_count}/{total_count} files read ({failed_count} failed)[/yellow]"
    except (ValueError, SyntaxError):
        pass

    # Fallback: don't show raw content (too verbose)
    return "[dim]✓ Files read[/dim]"


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
    format_result=format_read_files_result,
)
