"""Tool for reading files."""

from pathlib import Path

from rich.console import Console

from simple_agent.tools.registry import register


def read_files(file_paths: list[str]) -> dict[str, str | None]:
    """Read and return the contents of one or more files.

    Args:
        file_paths: List of paths to read (can be a single path in a list)

    Returns:
        Dictionary mapping each file path to its contents or None if an error occurred
    """
    console = Console()
    results: dict[str, str | None] = {}

    # For read_files, we want a special format with just filenames in a list
    cwd = str(Path.cwd())
    clean_paths = []

    for path in file_paths:
        if path.startswith(cwd):
            # If path starts with CWD, remove it to get a relative path
            rel_path = path[len(cwd) :].lstrip("/") or path.split("/")[-1]
            clean_paths.append(rel_path)
        else:
            # Otherwise use the basename
            clean_paths.append(path.split("/")[-1] if "/" in path else path)

    # Print formatted output
    if len(clean_paths) == 1:
        console.print(f"read_files({clean_paths[0]})")
    else:
        paths_str = ", ".join(clean_paths)
        console.print(f"read_files({paths_str})")

    # Read each file
    for path in file_paths:
        try:
            results[path] = Path(path).read_text()
        except Exception as e:
            console.print(f"[bold red]Error reading file:[/bold red] {e}")
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
