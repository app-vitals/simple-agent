"""Tool for patching files."""

from pathlib import Path

from rich.console import Console

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
)
