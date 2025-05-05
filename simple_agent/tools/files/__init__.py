"""File operation tools package."""

# Re-export everything so imports from simple_agent.tools.files continue to work
from simple_agent.tools.files.diff_utils import (
    create_git_diff_view,
    get_file_diff_for_patch,
    get_file_diff_for_write,
    patch_file_confirmation_handler,
    show_git_diff_confirmation,
    write_file_confirmation_handler,
)
from simple_agent.tools.files.glob_files import glob_files
from simple_agent.tools.files.grep_files import grep_files
from simple_agent.tools.files.list_directory import list_directory
from simple_agent.tools.files.patch_file import patch_file
from simple_agent.tools.files.read_files import read_files
from simple_agent.tools.files.write_file import write_file

__all__ = [
    # Basic file tools
    "read_files",
    "write_file",
    "patch_file",
    "list_directory",
    "glob_files",
    "grep_files",
    # Diff utilities
    "create_git_diff_view",
    "get_file_diff_for_write",
    "get_file_diff_for_patch",
    "show_git_diff_confirmation",
    "write_file_confirmation_handler",
    "patch_file_confirmation_handler",
]
