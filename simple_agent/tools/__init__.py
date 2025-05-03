"""Tool registry for Simple Agent."""

# Import registry functions for backward compatibility
# Import tools to ensure they register themselves
from simple_agent.tools.exec import execute_command
from simple_agent.tools.files import (
    glob_files,
    grep_files,
    list_directory,
    patch_file,
    read_files,
    write_file,
)
from simple_agent.tools.registry import (
    execute_tool_call,
    get_tool_descriptions,
    requires_confirmation,
)

# Export tools and registry functions for backward compatibility
__all__ = [
    # Registry functions
    "get_tool_descriptions",
    "requires_confirmation",
    "execute_tool_call",
    # File tools
    "read_files",
    "write_file",
    "patch_file",
    "list_directory",
    "glob_files",
    "grep_files",
    # Exec tools
    "execute_command",
]
