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

    # Print summary if reading multiple files
    if len(file_paths) > 1:
        console.print(
            f"[bold blue]Reading multiple files:[/bold blue] {len(file_paths)} files"
        )

    # Read each file
    for path in file_paths:
        console.print(f"[bold blue]Reading:[/bold blue] {path}")
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
