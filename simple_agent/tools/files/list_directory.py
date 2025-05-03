"""Tool for listing directory contents."""

import os
from pathlib import Path
from typing import Any

from rich.console import Console

from simple_agent.tools.registry import register


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


# Register this tool with the registry
register(
    name="list_directory",
    function=list_directory,
    description="List directories and files in a given directory path",
    parameters={
        "directory_path": {
            "type": "string",
            "description": "Path to the directory to list",
        },
        "show_hidden": {
            "type": "boolean",
            "description": "Whether to include hidden files and directories (those starting with .)",
        },
        "recursive": {
            "type": "boolean",
            "description": "Whether to list subdirectories recursively",
        },
        "max_depth": {
            "type": "integer",
            "description": "Maximum recursion depth (only used if recursive=True)",
        },
    },
    returns="Dictionary with directory structure information including files and subdirectories",
    requires_confirmation=False,  # Reading directory structure doesn't modify the system
)
