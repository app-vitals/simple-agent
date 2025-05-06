"""Utilities for displaying git diff-like views for file operations."""

import difflib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from simple_agent.display import (
    clean_path,
    display_info,
    display_warning,
    format_tool_args,
    get_confirmation,
)
from simple_agent.live_console import update_live_display


def create_git_diff_view(file_path: str, old_content: str, new_content: str) -> str:
    """Create a git diff-like view for file changes.

    Args:
        file_path: Path to the file being modified
        old_content: Original content or empty string for new files
        new_content: New content that will be written

    Returns:
        Formatted diff view as a string
    """
    clean_file_path = clean_path(file_path)

    # For new files (when old_content is empty)
    if not old_content:
        # Format as a new file diff
        lines = new_content.splitlines()
        header = [
            f"diff --git a/{clean_file_path} b/{clean_file_path}",
            "new file mode 100644",
            "--- /dev/null",
            f"+++ b/{clean_file_path}",
            f"@@ -0,0 +1,{len(lines)} @@",
        ]
        diff_lines = [f"+{line}" for line in lines]
        return "\n".join(header + diff_lines)

    # For existing files - create a unified diff
    a_lines = old_content.splitlines()
    b_lines = new_content.splitlines()

    diff = difflib.unified_diff(
        a_lines,
        b_lines,
        fromfile=f"a/{clean_file_path}",
        tofile=f"b/{clean_file_path}",
        lineterm="",
    )

    return "\n".join(diff)


def get_file_diff_for_write(file_path: str, content: str) -> str:
    """Generate a git diff-like view for a write operation.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file

    Returns:
        Formatted diff view as a string
    """
    # Check if file exists to determine if this is a new file or modification
    path = Path(file_path)
    old_content = ""

    if path.exists():
        from contextlib import suppress

        with suppress(Exception):
            # If we can't read the file, treat it as a new file
            old_content = path.read_text()

    return create_git_diff_view(file_path, old_content, content)


def get_file_diff_for_patch(file_path: str, old_content: str, new_content: str) -> str:
    """Generate a git diff-like view for a patch operation.

    Args:
        file_path: Path to the file to patch
        old_content: Content to be replaced
        new_content: New content to replace with

    Returns:
        Formatted diff view as a string
    """
    # For patch operations, we need to read the file and apply the change
    # to generate an accurate diff view
    path = Path(file_path)

    try:
        current_file_content = path.read_text()
        if old_content not in current_file_content:
            return f"ERROR: Old content not found in {clean_path(file_path)}"

        updated_content = current_file_content.replace(old_content, new_content)
        return create_git_diff_view(file_path, current_file_content, updated_content)
    except Exception as e:
        display_warning(f"Error creating diff for {clean_path(file_path)}", e)
        return f"Error creating diff: {e}"


def show_git_diff_confirmation(
    diff_content: str,
    tool_name: str,
    input_func: Callable[[str], str],
    tool_args: dict[str, Any] | None = None,
) -> bool:
    """Show a git diff-like view and prompt for confirmation.

    Args:
        diff_content: Git diff-like content to display
        tool_name: Name of the tool being executed
        input_func: Function to use for getting user input
        tool_args: Arguments passed to the tool

    Returns:
        True if user confirms, False if denied
    """
    # Show the diff with syntax highlighting
    display_info(f"Changes for {tool_name}:")

    # Update the live display with the diff content
    update_live_display("")  # Add a blank line for spacing

    # Format diff content with rich markup

    # Use console directly to render the syntax in the live display
    # We'll format the diff content as plain text for update_live_display
    for line in diff_content.splitlines():
        if line.startswith("+"):
            update_live_display(f"[green]{line}[/green]")
        elif line.startswith("-"):
            update_live_display(f"[red]{line}[/red]")
        elif line.startswith("@@"):
            update_live_display(f"[cyan]{line}[/cyan]")
        else:
            update_live_display(line)

    update_live_display("")  # Add a blank line for spacing

    # Format the tool arguments if they exist
    args_display = ""
    if tool_args:
        args_display = f"({format_tool_args(**tool_args)})"

    # For test input function, use a simple prompt
    if input_func != input:
        confirmation = input_func(f"Confirm {tool_name}{args_display}? [Y/n] ")
        if confirmation == "":
            confirmation = "y"
        return confirmation.lower() in ["y", "yes"]
    else:
        # Use the standardized confirmation function from display module
        return get_confirmation(f"[cyan]{tool_name}[/cyan]{args_display}?")


def write_file_confirmation_handler(
    tool_name: str, tool_args: dict[str, Any], input_func: Callable[[str], str]
) -> bool:
    """Custom confirmation handler for write_file tool.

    Args:
        tool_name: Name of the tool (write_file)
        tool_args: Arguments passed to write_file
        input_func: Function to use for getting user input

    Returns:
        True if user confirms, False if denied
    """
    file_path = tool_args.get("file_path", "")
    content = tool_args.get("content", "")

    # Generate a diff view for the file
    diff_content = get_file_diff_for_write(file_path, content)

    # Create a simplified version of tool_args with only the file_path
    display_args = {"file_path": file_path}

    # Show the diff and get confirmation
    return show_git_diff_confirmation(diff_content, tool_name, input_func, display_args)


def patch_file_confirmation_handler(
    tool_name: str, tool_args: dict[str, Any], input_func: Callable[[str], str]
) -> bool:
    """Custom confirmation handler for patch_file tool.

    Args:
        tool_name: Name of the tool (patch_file)
        tool_args: Arguments passed to patch_file
        input_func: Function to use for getting user input

    Returns:
        True if user confirms, False if denied
    """
    file_path = tool_args.get("file_path", "")
    old_content = tool_args.get("old_content", "")
    new_content = tool_args.get("new_content", "")

    # Generate a diff view for the patch
    diff_content = get_file_diff_for_patch(file_path, old_content, new_content)

    # Create a simplified version of tool_args with only the file_path
    display_args = {"file_path": file_path}

    # Show the diff and get confirmation
    return show_git_diff_confirmation(diff_content, tool_name, input_func, display_args)
