"""Tool for finding files using glob patterns."""

import glob
import os
from pathlib import Path

from simple_agent.display import (
    display_error,
    display_info,
    print_tool_call,
    print_tool_result,
)
from simple_agent.tools.registry import register
from simple_agent.tools.utils import clean_path


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
    # Print the tool call with cleaned paths
    if base_dir == ".":
        print_tool_call(
            "glob_files",
            pattern=pattern,
            recursive=recursive,
            include_hidden=include_hidden,
        )
    else:
        print_tool_call(
            "glob_files",
            pattern=pattern,
            base_dir=base_dir,
            recursive=recursive,
            include_hidden=include_hidden,
        )

    try:
        # Convert base_dir to absolute path and resolve any symlinks
        base_path = Path(base_dir).expanduser().resolve()
        if not base_path.exists():
            display_error(
                f"Base directory does not exist: {clean_path(str(base_path))}"
            )
            return []

        if not base_path.is_dir():
            display_error(f"Not a directory: {clean_path(str(base_path))}")
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

        # Display results summary
        if result:
            display_info(f"Found {len(result)} file(s) matching pattern '{pattern}'")
        else:
            display_info(f"No files found matching pattern '{pattern}'")

        # Display tool result
        print_tool_result("glob_files", result)

        return result

    except Exception as e:
        display_error(f"Error during glob search with pattern '{pattern}'", e)
        return []


# Register this tool with the registry
register(
    name="glob_files",
    function=glob_files,
    description="Find files matching a glob pattern",
    parameters={
        "pattern": {
            "type": "string",
            "description": 'Glob pattern to match (e.g., "*.py", "**/*.json")',
        },
        "base_dir": {
            "type": "string",
            "description": "Base directory to start the search from (defaults to current directory)",
        },
        "recursive": {
            "type": "boolean",
            "description": 'Whether to search recursively (automatically set to True for "**" patterns)',
        },
        "include_hidden": {
            "type": "boolean",
            "description": "Whether to include hidden files (starting with .)",
        },
    },
    returns="List of file paths matching the pattern",
    requires_confirmation=False,  # Reading file information doesn't modify the system
)
