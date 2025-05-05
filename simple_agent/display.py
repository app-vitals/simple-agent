"""Display utilities for standardized output formatting."""

from pathlib import Path
from typing import Any

from rich.traceback import Traceback

from simple_agent.live_console import (
    console,
    live_confirmation,
    update_live_display,
)


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
            # Handle strings - remove CWD prefixes from paths
            formatted_args.append(f"'{clean_path(arg)}'")
        elif isinstance(arg, list | tuple) and all(isinstance(x, str) for x in arg):
            # For lists/tuples of strings, clean each path and format as comma-separated
            if len(arg) > 3:
                # For long lists, show the first 2 items and a count
                formatted_items = [f"'{clean_path(x)}'" for x in list(arg)[:2]]
                formatted_args.append(
                    f"{', '.join(formatted_items)}, ... ({len(arg)} items)"
                )
            else:
                # For short lists, show all items
                formatted_items = [f"'{clean_path(x)}'" for x in arg]
                formatted_args.append(", ".join(formatted_items))
        elif isinstance(arg, int | float | bool):
            # Format simple primitive types
            formatted_args.append(str(arg))
        else:
            # For other types, provide a simpler representation
            formatted_args.append(f"<{type(arg).__name__}>")

    # Format keyword arguments
    formatted_kwargs = []
    for key, value in kwargs.items():
        if isinstance(value, str):
            # Handle string values - clean paths
            if len(value) > 50:
                # Truncate long strings
                formatted_kwargs.append(f"{key}='{clean_path(value[:47])}...'")
            else:
                formatted_kwargs.append(f"{key}='{clean_path(value)}'")
        elif isinstance(value, list | tuple) and all(isinstance(x, str) for x in value):
            # For lists/tuples of strings, clean each path
            if len(value) > 3:
                # For long lists, show the first 2 items and a count
                formatted_items = [f"'{clean_path(x)}'" for x in list(value)[:2]]
                formatted_kwargs.append(
                    f"{key}=[{', '.join(formatted_items)}, ... ({len(value)} items)]"
                )
            else:
                # For short lists, show all items
                formatted_items = [f"'{clean_path(x)}'" for x in value]
                formatted_kwargs.append(f"{key}=[{', '.join(formatted_items)}]")
        elif isinstance(value, int | float | bool):
            # Format simple primitive types
            formatted_kwargs.append(f"{key}={value}")
        elif value is None:
            # Handle None values
            formatted_kwargs.append(f"{key}=None")
        else:
            # For other types, provide a simpler representation
            formatted_kwargs.append(f"{key}=<{type(value).__name__}>")

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
        status: Response status (COMPLETE, ASK)
        next_action: Optional follow-up action or question
    """
    console.print(message)

    if status == "ASK" and next_action:
        console.print(f"[bold yellow]Question:[/bold yellow] {next_action}")


def display_error(message: str, err: Exception | None = None) -> None:
    """Display formatted error message with optional exception details.

    Args:
        message: Human-readable error message
        err: Optional exception for display
    """
    # Format the error message
    error_message = f"[bold red]Error:[/bold red] {message}"

    # Update the live display if available
    update_live_display(error_message)

    # Display exception details if provided
    if err:
        # Import live_display from the live_console module
        from simple_agent.live_console import live_display

        if live_display is None:
            # Only show traceback in console output if no live display
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
        else:
            # For live display, show a simplified error message
            err_summary = f"[dim]Exception: {type(err).__name__} - {str(err)}[/dim]"
            update_live_display(err_summary)


def display_warning(message: str, err: Exception | None = None) -> None:
    """Display formatted warning message with optional exception details.

    Args:
        message: Human-readable warning message
        err: Optional exception for display
    """
    # Format the warning message
    warning_message = f"[bold yellow]Warning:[/bold yellow] {message}"

    # Update the live display if available
    update_live_display(warning_message)

    # Display exception details if provided (with different styling from errors)
    if err:
        err_summary = f"[dim]Exception: {type(err).__name__} '{err}'[/dim]"
        update_live_display(err_summary)


def display_info(message: str) -> None:
    """Display formatted information message.

    Args:
        message: Information text to display
    """
    # Update the live display if available
    update_live_display(message)


def display_command(command: str) -> None:
    """Display formatted shell command.

    Args:
        command: The shell command to be displayed
    """
    command_message = f"[cyan]$ {command}[/cyan]"
    update_live_display(command_message)


def get_confirmation(message: str, default: bool = True) -> bool:
    """Get user confirmation with standardized formatting.

    Args:
        message: Question to ask the user
        default: Default value if user hits Enter

    Returns:
        True if confirmed, False otherwise
    """
    # Use the live confirmation system which handles both live and standard modes
    return live_confirmation(message, default)


def display_exit(reason: str) -> None:
    """Display formatted exit message.

    Args:
        reason: The reason for exiting
    """
    console.print(f"[bold blue]Exiting:[/bold blue] {reason}")


def display_status_message(
    tokens_sent: int, tokens_received: int, elapsed_time: float | None = None
) -> str:
    """Format status message with token and time information.

    Args:
        tokens_sent: Number of tokens sent to the LLM
        tokens_received: Number of tokens received from the LLM
        elapsed_time: Optional elapsed time in seconds

    Returns:
        Formatted status message string
    """
    # Format token counts
    token_info = f"Tokens: {tokens_sent:,} sent / {tokens_received:,} recv"

    # Add time information if available
    if elapsed_time is not None:
        if elapsed_time < 60:
            time_info = f"{int(elapsed_time)}s"
        else:
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_info = f"{minutes}m {seconds}s"
        return f"{token_info} • Time: {time_info}"

    return token_info


def print_tool_call(tool_name: str, **args: Any) -> None:
    """Print standardized tool execution announcement.

    Args:
        tool_name: Name of the tool being executed
        **args: Tool arguments
    """
    # Format args for display using format_tool_args to clean paths
    args_str = format_tool_args(**args)
    tool_call_message = f"[cyan]{tool_name}[/cyan]({args_str})"

    # Update the display with the tool call message
    update_live_display(tool_call_message)


def print_tool_result(tool_name: str, message: str) -> None:
    """Print standardized tool execution result.

    Args:
        tool_name: Name of the tool that was executed
        message: Descriptive message about the result
    """
    tool_result_message = f"[cyan]{tool_name}[/cyan]: {message}"

    # Update the display with the tool result message
    update_live_display(tool_result_message)
