"""File operation tools."""

import glob
import os
from pathlib import Path
from typing import Any

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


def list_directory(
    directory_path: str,
    show_hidden: bool = False,
    recursive: bool = False,
    max_depth: int = 3,
) -> dict[str, Any]:
    """List directories and files in the given path.

    Args:
        directory_path: Path to the directory to list
        show_hidden: Whether to include hidden files/directories (starting with .)
        recursive: Whether to list directories recursively
        max_depth: Maximum recursion depth (only used if recursive=True)

    Returns:
        Dictionary with directory structure information
    """
    console = Console()
    console.print(f"[bold blue]Listing directory:[/bold blue] {directory_path}")

    try:
        path = Path(directory_path).expanduser().resolve()
        if not path.exists():
            console.print(f"[bold red]Error:[/bold red] Path does not exist: {path}")
            return {"error": f"Path does not exist: {path}"}

        if not path.is_dir():
            console.print(f"[bold red]Error:[/bold red] Not a directory: {path}")
            return {"error": f"Not a directory: {path}"}

        result = _scan_directory(
            path,
            show_hidden=show_hidden,
            recursive=recursive,
            max_depth=max_depth,
            current_depth=0,
        )
        return result

    except Exception as e:
        console.print(f"[bold red]Error listing directory:[/bold red] {e}")
        return {"error": str(e)}


def _scan_directory(
    path: Path, show_hidden: bool, recursive: bool, max_depth: int, current_depth: int
) -> dict[str, Any]:
    """Scan a directory and return its structure.

    This is a helper function for list_directory.

    Args:
        path: Path object to scan
        show_hidden: Whether to include hidden files/directories
        recursive: Whether to scan recursively
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth

    Returns:
        Dictionary with directory structure
    """
    result: dict[str, Any] = {
        "path": str(path),
        "name": path.name,
        "dirs": [],
        "files": [],
    }

    entries = list(os.scandir(path))

    # Process directories
    directories = [entry for entry in entries if entry.is_dir()]
    for dir_entry in sorted(directories, key=lambda e: e.name):
        # Skip hidden directories if show_hidden is False
        if not show_hidden and dir_entry.name.startswith("."):
            continue

        dir_info: dict[str, Any] = {
            "name": dir_entry.name,
            "path": str(dir_entry.path),
        }

        # Add to directories list
        dirs_list = result["dirs"]
        if isinstance(dirs_list, list):
            dirs_list.append(dir_info)

        # Process recursively if needed and depth allows
        if recursive and (current_depth < max_depth):
            subdir_path = Path(dir_entry.path)
            subdir_info = _scan_directory(
                subdir_path,
                show_hidden=show_hidden,
                recursive=recursive,
                max_depth=max_depth,
                current_depth=current_depth + 1,
            )
            # Add children to this directory
            # Type check already done with the explicit type annotation
            dir_info["children"] = {
                "dirs": subdir_info["dirs"],
                "files": subdir_info["files"],
            }

    # Process files
    files = [entry for entry in entries if entry.is_file()]
    for file_entry in sorted(files, key=lambda e: e.name):
        # Skip hidden files if show_hidden is False
        if not show_hidden and file_entry.name.startswith("."):
            continue

        # Get file info
        stat_info = file_entry.stat()
        file_info = {
            "name": file_entry.name,
            "path": str(file_entry.path),
            "size": stat_info.st_size,
            "modified": stat_info.st_mtime,
        }
        files_list = result["files"]
        if isinstance(files_list, list):
            files_list.append(file_info)

    return result


def glob_files(
    pattern: str,
    base_dir: str = ".",
    recursive: bool = False,
    include_hidden: bool = False,
) -> list[str]:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern to match (e.g., "*.py", "**/*.json")
        base_dir: Base directory to start the search from
        recursive: Whether to search recursively (automatically set to True for "**" patterns)
        include_hidden: Whether to include hidden files (starting with .)

    Returns:
        List of file paths matching the pattern
    """
    console = Console()
    console.print(f"[bold blue]Searching for files:[/bold blue] {pattern}")

    try:
        # Convert base_dir to absolute path and resolve any symlinks
        base_path = Path(base_dir).expanduser().resolve()
        if not base_path.exists():
            console.print(
                f"[bold red]Error:[/bold red] Base directory does not exist: {base_path}"
            )
            return []

        if not base_path.is_dir():
            console.print(f"[bold red]Error:[/bold red] Not a directory: {base_path}")
            return []

        # If pattern contains "**", set recursive to True automatically
        if "**" in pattern:
            recursive = True

        # Construct the full pattern
        full_pattern = os.path.join(str(base_path), pattern)

        # Use glob to find matching files
        matched_files = glob.glob(full_pattern, recursive=recursive)

        # If include_hidden is True, we may need to handle this specially for hidden files
        # Since glob might skip hidden files in some environments
        if include_hidden and "*" in pattern:
            # Get the directory where we're searching
            search_dir = os.path.dirname(full_pattern) or base_path
            # Get the pattern we're matching against
            base_pattern = os.path.basename(pattern)

            # For patterns like "*.py", manually check for hidden files matching the extension
            if base_pattern.startswith("*."):
                extension = base_pattern[1:]  # Get ".py" from "*.py"
                for item in os.listdir(str(search_dir)):
                    if item.startswith(".") and item.endswith(extension):
                        hidden_path = os.path.join(str(search_dir), item)
                        if (
                            os.path.isfile(hidden_path)
                            and hidden_path not in matched_files
                        ):
                            matched_files.append(hidden_path)

        # Filter out directories and hidden files if needed
        result = []
        for file_path in matched_files:
            path = Path(file_path)

            # Skip directories
            if path.is_dir():
                continue

            # Skip hidden files if include_hidden is False
            if not include_hidden and path.name.startswith("."):
                continue

            result.append(str(path))

        # Sort files by modification time (newest first)
        result.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        console.print(f"[bold green]Found:[/bold green] {len(result)} files")
        return result

    except Exception as e:
        console.print(f"[bold red]Error during glob search:[/bold red] {e}")
        return []
