"""Tool for searching file contents using patterns."""

import os
import re
from pathlib import Path

from rich.console import Console

from simple_agent.tools.registry import register
from simple_agent.tools.utils import print_tool_call


def grep_files(
    pattern: str,
    file_paths: list[str] | None = None,
    directory: str | None = None,
    include_pattern: str | None = None,
    recursive: bool = True,  # Changed default to True for better searching
    case_sensitive: bool = False,
    include_hidden: bool = False,
    max_results: int = 1000,
    context_lines: int = 0,  # New parameter for showing context lines
) -> dict[str, list[tuple[int, str]]]:
    """Search file contents for a pattern.

    Args:
        pattern: Regular expression pattern to search for in file contents
        file_paths: List of specific file paths to search (optional)
        directory: Directory to search in (optional, default: current directory)
        include_pattern: File pattern to include (e.g., "*.py", "*.{js,ts}")
        recursive: Whether to search subdirectories recursively (default: True)
        case_sensitive: Whether the search should be case-sensitive
        include_hidden: Whether to include hidden files (starting with .)
        max_results: Maximum number of results to return
        context_lines: Number of context lines to include before and after matches

    Returns:
        Dictionary mapping file paths to lists of (line_number, line_content) tuples
    """
    console = Console()

    # Create a kwargs dictionary with all provided arguments
    kwargs: dict[str, object] = {}
    if file_paths:
        kwargs["file_paths"] = file_paths
    if directory:
        kwargs["directory"] = directory
    if include_pattern:
        kwargs["include_pattern"] = include_pattern

    # Print the tool call with cleaned paths
    print_tool_call("grep_files", pattern, **kwargs)

    try:
        # Compile the pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled_pattern = re.compile(pattern, flags)
        except re.error as e:
            console.print(f"[bold red]Invalid regex pattern:[/bold red] {e}")
            return {"error": [(-1, f"Invalid regex pattern: {e}")]}

        # Get the files to search
        files_to_search = []

        # Process specific file paths
        if file_paths:
            for path in file_paths:
                full_path = Path(path).expanduser().resolve()
                if full_path.is_file():
                    files_to_search.append(str(full_path))
                else:
                    console.print(f"[yellow]Warning:[/yellow] {path} is not a file")

        # Process directory search
        elif directory or include_pattern:
            base_dir = "."
            if directory:
                base_dir = directory

            base_path = Path(base_dir).expanduser().resolve()
            if not base_path.exists() or not base_path.is_dir():
                console.print(
                    f"[bold red]Error:[/bold red] {base_dir} is not a valid directory"
                )
                return {"error": [(-1, f"{base_dir} is not a valid directory")]}

            # Walk the directory tree if needed
            if recursive:
                for root, dirs, files in os.walk(str(base_path)):
                    # Skip hidden directories unless include_hidden is True
                    if not include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith(".")]

                    for file in files:
                        # Skip hidden files unless include_hidden is True
                        if not include_hidden and file.startswith("."):
                            continue

                        file_path = os.path.join(root, file)

                        # Apply include_pattern filter if specified
                        if include_pattern:
                            if _matches_pattern(file, include_pattern):
                                files_to_search.append(file_path)
                        else:
                            files_to_search.append(file_path)
            else:
                # Non-recursive search, just look at files in the current directory
                for file in os.listdir(str(base_path)):
                    # Skip hidden files unless include_hidden is True
                    if not include_hidden and file.startswith("."):
                        continue

                    file_path = os.path.join(str(base_path), file)

                    # Skip directories
                    if os.path.isdir(file_path):
                        continue

                    # Apply include_pattern filter if specified
                    if include_pattern:
                        if _matches_pattern(file, include_pattern):
                            files_to_search.append(file_path)
                    else:
                        files_to_search.append(file_path)
        else:
            # Default behavior: search all files in current directory
            for file in os.listdir("."):
                # Skip hidden files and directories
                if not include_hidden and file.startswith("."):
                    continue

                if os.path.isfile(file):
                    files_to_search.append(file)

        # Perform the search
        console.print(
            f"[bold blue]Searching in:[/bold blue] {len(files_to_search)} files"
        )
        result: dict[str, list[tuple[int, str]]] = {}
        total_matches = 0

        for file_path in files_to_search:
            if total_matches >= max_results:
                console.print(
                    f"[bold yellow]Warning:[/bold yellow] Reached maximum results limit ({max_results})"
                )
                break

            try:
                with open(file_path, encoding="utf-8", errors="replace") as f:
                    # Read all lines from the file
                    lines = list(f)
                    matches = []

                    for i, line in enumerate(lines, start=1):
                        if compiled_pattern.search(line):
                            # Add context lines if requested
                            if context_lines > 0:
                                # Add lines before match
                                start_idx = max(0, i - context_lines - 1)
                                for j in range(start_idx, i - 1):
                                    matches.append((j + 1, lines[j].rstrip("\n")))

                                # Add the match itself
                                matches.append((i, line.rstrip("\n")))

                                # Add lines after match
                                end_idx = min(len(lines), i + context_lines)
                                for j in range(i, end_idx):
                                    matches.append((j + 1, lines[j].rstrip("\n")))
                            else:
                                matches.append((i, line.rstrip("\n")))

                            total_matches += 1
                            if total_matches >= max_results:
                                break

                    if matches:
                        result[file_path] = matches
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/yellow] Error reading {file_path}: {e}"
                )
                # Continue with other files rather than failing completely

        console.print(
            f"[bold green]Found:[/bold green] {total_matches} matches in {len(result)} files"
        )
        return result

    except Exception as e:
        console.print(f"[bold red]Error during search:[/bold red] {e}")
        return {"error": [(-1, str(e))]}


def _matches_pattern(filename: str, pattern: str) -> bool:
    """Check if a filename matches a pattern.

    Args:
        filename: Filename to check
        pattern: Pattern such as "*.py" or "*.{js,ts}"

    Returns:
        True if the filename matches the pattern
    """
    # Handle extension groups like *.{js,ts}
    if "{" in pattern and "}" in pattern:
        prefix = pattern[: pattern.find("{")]
        suffix_group = pattern[pattern.find("{") + 1 : pattern.find("}")]
        suffixes = suffix_group.split(",")

        for suffix in suffixes:
            full_pattern = prefix + suffix
            if _simple_pattern_match(filename, full_pattern):
                return True
        return False
    else:
        return _simple_pattern_match(filename, pattern)


def _simple_pattern_match(filename: str, pattern: str) -> bool:
    """Perform a simple globbing-style match.

    Args:
        filename: Filename to check
        pattern: Simple pattern like "*.py"

    Returns:
        True if the filename matches the pattern
    """
    if pattern.startswith("*"):
        return filename.endswith(pattern[1:])
    elif pattern.endswith("*"):
        return filename.startswith(pattern[:-1])
    else:
        return filename == pattern


# Register this tool with the registry
register(
    name="grep_files",
    function=grep_files,
    description="Search file contents for a regular expression pattern",
    parameters={
        "pattern": {
            "type": "string",
            "description": "Regular expression pattern to search for in file contents",
        },
        "file_paths": {
            "type": "array",
            "description": "List of specific file paths to search (optional)",
            "items": {"type": "string"},
        },
        "directory": {
            "type": "string",
            "description": "Directory to search in (optional, default: current directory)",
        },
        "include_pattern": {
            "type": "string",
            "description": 'File pattern to include (e.g., "*.py", "*.{js,ts}")',
        },
        "recursive": {
            "type": "boolean",
            "description": "Whether to search subdirectories recursively (default: True)",
        },
        "case_sensitive": {
            "type": "boolean",
            "description": "Whether the search should be case-sensitive",
        },
        "include_hidden": {
            "type": "boolean",
            "description": "Whether to include hidden files (starting with .)",
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return",
        },
        "context_lines": {
            "type": "integer",
            "description": "Number of context lines to include before and after matches",
        },
    },
    returns="Dictionary mapping file paths to lists of (line_number, line_content) tuples",
    requires_confirmation=False,  # Reading file information doesn't modify the system
)
