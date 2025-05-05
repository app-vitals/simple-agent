"""Tool for patching files."""

from pathlib import Path

from simple_agent.display import (
    clean_path,
    display_warning,
    print_tool_call,
    print_tool_result,
)
from simple_agent.tools.files.diff_utils import patch_file_confirmation_handler
from simple_agent.tools.registry import register


def patch_file(file_path: str, old_content: str, new_content: str) -> bool:
    """Create a patch-style edit to a file, replacing specific content.

    Args:
        file_path: Path to the file to patch
        old_content: Content to be replaced
        new_content: New content to replace with

    Returns:
        True if successful, False otherwise
    """
    print_tool_call("patch_file", file_path=file_path)

    try:
        current_content = Path(file_path).read_text()
        if old_content not in current_content:
            display_warning(f"Old content not found in {file_path}")
            return False

        updated_content = current_content.replace(old_content, new_content)
        Path(file_path).write_text(updated_content)

        # Display success message
        print_tool_result(
            "patch_file", f"Successfully patched file {clean_path(file_path)}"
        )
        return True
    except Exception as e:
        display_warning(f"Error patching file {clean_path(file_path)}", e)
        return False


# Register this tool with the registry
register(
    name="patch_file",
    function=patch_file,
    description="Replace specific content in a file",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the file to patch",
        },
        "old_content": {
            "type": "string",
            "description": "Content to be replaced",
        },
        "new_content": {
            "type": "string",
            "description": "New content to replace with",
        },
    },
    returns="True if successful, False otherwise",
    requires_confirmation=True,  # Modifies the system
    confirmation_handler=patch_file_confirmation_handler,
)
