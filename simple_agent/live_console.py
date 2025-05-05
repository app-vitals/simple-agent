"""Live console display for dynamic updates during processing."""

import contextlib
import re
import threading
import time
from collections.abc import Callable, Generator

from rich.box import MINIMAL
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

# Regular expression pattern to identify status lines
STATUS_LINE_PATTERN = re.compile(r"\[blue\].*?(Processing|Analyzing|step).*?\[/blue\]")

# Create a shared Console instance for all output
console = Console()

# Create a shared Live display instance for dynamic updates
live_display: Live | None = None

# Current processing stage message
current_stage = "Processing..."


@contextlib.contextmanager
def live_context(
    status_callback: Callable[[], str] | None = None, update_interval: float = 0.25
) -> Generator[Live, None, None]:
    """Context manager for live display updates.

    Args:
        status_callback: Optional callback function that returns status text
        update_interval: Time between status updates in seconds

    Yields:
        Rich Live context for dynamic updates
    """
    global live_display

    # Create a new Live display
    live = Live(
        Panel(
            "[blue]Processing...[/blue] • Starting",
            title="",
            border_style="blue",
            box=MINIMAL,
        ),
        console=console,
        refresh_per_second=8,  # Increase refresh rate
        transient=False,
    )

    # Set up status updater thread if a callback is provided
    stop_event = threading.Event()
    status_thread = None

    if status_callback is not None:

        def update_status() -> None:
            while not stop_event.is_set():
                if live_display:
                    try:
                        # Get current status from callback
                        current_status = status_callback()

                        # Get current content
                        current_content = live_display.renderable
                        if isinstance(current_content, Panel):
                            # Extract content as lines
                            content_text = (
                                current_content.renderable
                                if hasattr(current_content, "renderable")
                                else ""
                            )
                            lines = (
                                content_text.split("\n")
                                if isinstance(content_text, str)
                                else []
                            )

                            # Filter out status lines
                            filtered_lines = [
                                line
                                for line in lines
                                if not STATUS_LINE_PATTERN.search(line)
                            ]

                            # Filter out consecutive and trailing empty lines
                            filtered_lines = _filter_empty_lines(filtered_lines)

                            # Format the status line
                            status_line = (
                                f"[blue]{current_stage}[/blue] • {current_status}"
                            )

                            # Create final display content
                            if filtered_lines:
                                # Create new content list with empty line separator
                                display_lines = filtered_lines + ["", status_line]
                            else:
                                # Just show the status line if there's no other content
                                display_lines = [status_line]

                            # Replace filtered_lines with the display lines that include status line
                            filtered_lines = display_lines

                            # Update the live display
                            live_display.update(
                                Panel(
                                    "\n".join(filtered_lines),
                                    title="",
                                    border_style="blue",
                                    box=MINIMAL,
                                )
                            )
                    except Exception:
                        # Ignore any errors in the update thread
                        pass

                # Sleep for the update interval
                time.sleep(update_interval)

        # Create and start the status update thread
        status_thread = threading.Thread(target=update_status, daemon=True)

    try:
        # Start the live display
        live.start()
        live_display = live

        # Start the status update thread if it exists
        if status_thread:
            status_thread.start()

        yield live
    finally:
        # Signal the status thread to stop
        stop_event.set()

        # Wait for the status thread to finish if it exists
        if status_thread and status_thread.is_alive():
            status_thread.join(timeout=0.5)  # Wait up to 0.5s for thread to end

        # Ensure the live display is stopped
        live.stop()
        live_display = None


def set_stage_message(message: str) -> None:
    """Set the current processing stage message.

    Args:
        message: The stage message to display
    """
    global current_stage
    current_stage = message


def _filter_empty_lines(lines: list[str]) -> list[str]:
    """Filter consecutive empty lines, keeping only single empty lines.
    Also removes empty lines at the end of the content.

    Args:
        lines: List of lines to filter

    Returns:
        Filtered list with no consecutive empty lines and no trailing empty lines
    """
    if not lines:
        return lines

    # First pass: filter consecutive empty lines
    result = []
    prev_empty = False

    for line in lines:
        is_empty = not line.strip()
        if not (is_empty and prev_empty):  # Skip if current and previous are empty
            result.append(line)
        prev_empty = is_empty

    # Second pass: remove trailing empty lines
    while result and not result[-1].strip():
        result.pop()

    return result


def update_live_display(new_content: str) -> None:
    """Update the live display with new content.

    This is a helper function that handles all the common logic for adding content
    to the live display, including filtering out status lines and managing empty lines.

    Args:
        new_content: The new content to add to the display
    """
    if live_display is None:
        # No live display available, fallback to console
        # Use highlight=False to preserve any ANSI color codes in the content
        console.print(new_content, highlight=False)
        return

    current_content = live_display.renderable
    if not isinstance(current_content, Panel):
        return

    # Extract existing content as lines
    lines = (
        current_content.renderable.split("\n")
        if isinstance(current_content.renderable, str)
        else []
    )

    # Separate status lines from content
    status_line = None
    for line in lines:
        if STATUS_LINE_PATTERN.search(line):
            status_line = line
            break

    # Filter out any status lines using the regex pattern
    filtered_lines = [line for line in lines if not STATUS_LINE_PATTERN.search(line)]

    # Filter out consecutive empty lines
    filtered_lines = _filter_empty_lines(filtered_lines)

    # Add the new content
    filtered_lines.append(new_content)

    # Add the status line back if it exists
    if status_line:
        # Make sure we have an empty line before the status if there's other content
        if filtered_lines:
            display_lines = filtered_lines + ["", status_line]
        else:
            display_lines = [status_line]
    else:
        display_lines = filtered_lines

    # Update the panel with filtered content
    live_display.update(
        Panel("\n".join(display_lines), title="", border_style="blue", box=MINIMAL)
    )


def live_confirmation(message: str, default: bool = True) -> bool:
    """Get user confirmation within the live display.

    Args:
        message: The confirmation message to display
        default: Default response if user just presses Enter

    Returns:
        True if confirmed, False if denied
    """
    if live_display is None:
        # Fallback to standard input if live display isn't available
        default_text = "Y/n" if default else "y/N"
        response = input(f"Confirm {message} [{default_text}] ")
        if not response:
            return default
        return response.lower() in ["y", "yes"]

    # Create the confirmation message but don't add it to the live display yet
    # We'll show it only at the input prompt at the bottom of the console
    confirm_message = (
        f"[bold yellow]Confirm[/bold yellow] {message} [bold yellow][Y/n][/bold yellow]"
    )

    # Temporarily stop the live display to get user input
    live_display.stop()

    try:
        # Use a colored prompt for the confirmation
        # This uses ANSI escape codes for color since we're outside of Rich's rendering
        default_text = "Y/n" if default else "y/N"
        yellow_text = "\033[93m"  # ANSI bright yellow
        cyan_text = "\033[96m"  # ANSI bright cyan
        reset_text = "\033[0m"  # ANSI reset

        # Convert any Rich markup to ANSI colors
        formatted_message = message

        # Common color conversions
        formatted_message = formatted_message.replace("[cyan]", cyan_text)
        formatted_message = formatted_message.replace("[/cyan]", reset_text)
        formatted_message = formatted_message.replace("[blue]", "\033[94m")
        formatted_message = formatted_message.replace("[/blue]", reset_text)
        formatted_message = formatted_message.replace("[green]", "\033[92m")
        formatted_message = formatted_message.replace("[/green]", reset_text)
        formatted_message = formatted_message.replace("[red]", "\033[91m")
        formatted_message = formatted_message.replace("[/red]", reset_text)
        formatted_message = formatted_message.replace("[yellow]", "\033[93m")
        formatted_message = formatted_message.replace("[/yellow]", reset_text)

        # Style conversions
        formatted_message = formatted_message.replace("[bold]", "\033[1m")
        formatted_message = formatted_message.replace("[/bold]", reset_text)
        formatted_message = formatted_message.replace("[dim]", "\033[2m")
        formatted_message = formatted_message.replace("[/dim]", reset_text)
        formatted_message = formatted_message.replace("[italic]", "\033[3m")
        formatted_message = formatted_message.replace("[/italic]", reset_text)

        response = input(
            f"{yellow_text}Confirm{reset_text} {formatted_message} {yellow_text}[{default_text}]{reset_text} "
        )

        # Process the response
        if not response:
            result = default
        else:
            result = response.lower() in ["y", "yes"]

        # Display the user's choice in the live context
        choice_text = "Yes" if result else "No"
        confirmation_result = (
            f"[bold yellow]Confirm[/bold yellow] {message} [bold]→ {choice_text}[/bold]"
        )

        # Resume the live display and update it with the confirmation result
        live_display.start()
        update_live_display(confirmation_result)

        return result
    except Exception as e:
        # Make sure we restart the live display even if there's an error
        if live_display and not live_display.is_active:
            live_display.start()
        # Re-raise the exception
        raise e
