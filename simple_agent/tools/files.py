"""File operation tools."""

from pathlib import Path

from rich.console import Console


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


def patch_file(file_path: str, old_content: str, new_content: str) -> bool:
    """Create a patch-style edit to a file, replacing specific content.

    Args:
        file_path: Path to the file to patch
        old_content: Content to be replaced
        new_content: New content to replace with

    Returns:
        True if successful, False otherwise
    """
    console = Console()
    try:
        current_content = Path(file_path).read_text()
        if old_content not in current_content:
            console.print(
                f"[bold red]Error:[/bold red] Old content not found in {file_path}"
            )
            return False

        updated_content = current_content.replace(old_content, new_content)
        Path(file_path).write_text(updated_content)
        console.print(f"[bold green]Patched:[/bold green] {file_path}")
        return True
    except Exception as e:
        console.print(f"[bold red]Error patching file:[/bold red] {e}")
        return False
