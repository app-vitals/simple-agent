"""Display utilities for standardized output formatting."""

from pathlib import Path
from typing import Any

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.traceback import Traceback

# Create a shared Console instance for all output
console = Console()


def clean_path(path: str) -> str:
    """Remove current working directory prefix from a path for display.

    Args:
        path: Path string to clean

    Returns:
        Path without CWD prefix, or unchanged if not under CWD
    """
    cwd = str(Path.cwd())
    if path.startswith(cwd):
        # Strip current working directory and any leading slashes
        clean = path[len(cwd) :].lstrip("/") or "."
        return clean
    return path


def format_tool_args(*args: object, **kwargs: object) -> str:
    """Format tool arguments for display by removing CWD prefixes.

    Args:
        *args: Positional arguments to format
        **kwargs: Keyword arguments to format

    Returns:
        String representation of arguments with clean paths
    """
    # Format positional arguments
    formatted_args = []
    for arg in args:
        if isinstance(arg, str):
            formatted_args.append(f"'{clean_path(arg)}'")
        elif isinstance(arg, list | tuple) and all(isinstance(x, str) for x in arg):
            # For lists/tuples of strings, clean each path and format as comma-separated
            formatted_items = [f"'{clean_path(x)}'" for x in arg]
            formatted_args.append(", ".join(formatted_items))
        else:
            formatted_args.append(str(arg))

    # Format keyword arguments
    formatted_kwargs = []
    for key, value in kwargs.items():
        if isinstance(value, str):
            formatted_kwargs.append(f"{key}='{clean_path(value)}'")
        elif isinstance(value, list | tuple) and all(isinstance(x, str) for x in value):
            # Special handling for file_paths which should be displayed as comma-separated values
            if key == "file_paths":
                cleaned_paths = [clean_path(x) for x in value]
                formatted_kwargs.append(", ".join(cleaned_paths))
            else:
                # For other lists/tuples, format as a list
                formatted_items = [f"'{clean_path(x)}'" for x in value]
                formatted_kwargs.append(f"{key}=[{', '.join(formatted_items)}]")
        else:
            formatted_kwargs.append(f"{key}={value}")

    # Combine positional and keyword arguments
    all_args = []
    if formatted_args:
        all_args.extend(formatted_args)
    if formatted_kwargs:
        all_args.extend(formatted_kwargs)

    return ", ".join(all_args)


def display_response(message: str, status: str, next_action: str | None = None) -> None:
    """Display formatted agent response based on status.

    Args:
        message: Main response message
        status: Response status (COMPLETE, CONTINUE, ASK)
        next_action: Optional follow-up action or question
    """
    console.print(message)

    if status == "CONTINUE" and next_action:
        console.print(f"[bold blue]Next:[/bold blue] {next_action}")
    elif status == "ASK" and next_action:
        console.print(f"[bold yellow]Question:[/bold yellow] {next_action}")


def display_error(message: str, err: Exception | None = None) -> None:
    """Display formatted error message with optional exception details.

    Args:
        message: Human-readable error message
        err: Optional exception for display
    """
    # Display the primary error message
    console.print(f"[bold red]Error:[/bold red] {message}")

    # Display exception details if provided
    if err:
        console.print(
            Traceback.from_exception(
                type(err),
                err,
                err.__traceback__,
                show_locals=False,
                width=100,
                extra_lines=3,
                theme=None,
                word_wrap=True,
            )
        )


def display_warning(message: str, err: Exception | None = None) -> None:
    """Display formatted warning message with optional exception details.

    Args:
        message: Human-readable warning message
        err: Optional exception for display
    """
    # Display the primary warning message
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")

    # Display exception details if provided (with different styling from errors)
    if err:
        console.print(
            Traceback.from_exception(
                type(err),
                err,
                err.__traceback__,
                show_locals=False,
                width=100,
                extra_lines=3,
                theme=None,
                word_wrap=True,
            )
        )


def display_info(message: str) -> None:
    """Display formatted information message.

    Args:
        message: Information text to display
    """
    console.print(message)


def display_command(command: str) -> None:
    """Display formatted shell command.

    Args:
        command: The shell command to be displayed
    """
    console.print(f"[cyan]$ {command}[/cyan]")


def get_confirmation(message: str, default: bool = True) -> bool:
    """Get user confirmation with standardized formatting.

    Args:
        message: Question to ask the user
        default: Default value if user hits Enter

    Returns:
        True if confirmed, False otherwise
    """
    default_text = "[Y/n]" if default else "[y/N]"
    result = prompt(
        HTML(
            f"<ansiyellow>Confirm</ansiyellow> {message} <ansiyellow>{default_text}</ansiyellow> "
        )
    )

    if not result:
        return default
    return result.lower() in ["y", "yes"]


def display_success(message: str) -> None:
    """Display formatted success message.

    Args:
        message: Success message to display
    """
    console.print(f"[green]Success:[/green] {message}")


def display_exit(reason: str) -> None:
    """Display formatted exit message.

    Args:
        reason: The reason for exiting
    """
    console.print(f"[bold blue]Exiting:[/bold blue] {reason}")


def print_tool_call(tool_name: str, **args: Any) -> None:
    """Print standardized tool execution announcement.

    Args:
        tool_name: Name of the tool being executed
        **args: Tool arguments
    """
    # Format args for display using format_tool_args to clean paths
    args_str = format_tool_args(**args)
    console.print(f"[cyan]{tool_name}[/cyan]({args_str})")


def print_tool_result(tool_name: str, message: str) -> None:
    """Print standardized tool execution result.

    Args:
        tool_name: Name of the tool that was executed
        message: Descriptive message about the result
    """
    console.print(f"[cyan]{tool_name}[/cyan]: {message}")
