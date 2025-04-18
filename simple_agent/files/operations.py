"""File operation tools."""

from pathlib import Path
from typing import Optional

from rich.console import Console


def read_file(file_path: str) -> Optional[str]:
    """Read and return the contents of a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        String contents of the file, or None if an error occurs
    """
    console = Console()
    console.print(f"[bold blue]Reading:[/bold blue] {file_path}")
    
    try:
        return Path(file_path).read_text()
    except Exception as e:
        console.print(f"[bold red]Error reading file:[/bold red] {e}")
        return None


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
            console.print(f"[bold red]Error:[/bold red] Old content not found in {file_path}")
            return False
        
        updated_content = current_content.replace(old_content, new_content)
        Path(file_path).write_text(updated_content)
        console.print(f"[bold green]Patched:[/bold green] {file_path}")
        return True
    except Exception as e:
        console.print(f"[bold red]Error patching file:[/bold red] {e}")
        return False