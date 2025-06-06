"""Tool for executing shell commands."""

import subprocess
from select import select

from simple_agent.display import (
    display_command,
    display_warning,
    print_tool_call,
    update_live_display,
)
from simple_agent.tools.registry import register


def execute_command(command: str) -> tuple[str, str, int]:
    """Execute a shell command and return its output.

    Args:
        command: Command string to execute

    Returns:
        Tuple containing (stdout, stderr, return_code)
    """

    print_tool_call("execute_command", command=command)
    display_command(command)

    # For capturing the complete output to return
    stdout_capture = []
    stderr_capture = []

    try:
        # Run the command directly, without capturing output to show it in real-time
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            universal_newlines=True,
        )

        # Use select to handle stdout and stderr without blocking
        while True:
            # Wait for the process to produce output or finish
            rlist, _, _ = select([process.stdout, process.stderr], [], [], 0.1)

            if process.stdout in rlist and process.stdout is not None:
                output = process.stdout.readline()
                if output:
                    # Capture the output
                    stdout_capture.append(output)

                    # Display the output in the live console if available, otherwise to stdout
                    # Use update_live_display which handles the case when live_display is None
                    update_live_display(f"[dim]{output.rstrip()}[/dim]")

            if process.stderr in rlist and process.stderr is not None:
                output = process.stderr.readline()
                if output:
                    # Capture the error
                    stderr_capture.append(output)

                    # Display the error in the live console if available, otherwise to stderr
                    # Use update_live_display which handles the case when live_display is None
                    update_live_display(f"[red]{output.rstrip()}[/red]")

            # Check if the process has finished
            if process.poll() is not None:
                # Read any remaining output
                if process.stdout is not None:
                    for output in process.stdout:
                        # Capture the output
                        stdout_capture.append(output)

                        # Display in live console or stdout using update_live_display
                        if output.strip():
                            update_live_display(f"[dim]{output.rstrip()}[/dim]")

                if process.stderr is not None:
                    for output in process.stderr:
                        # Capture the error
                        stderr_capture.append(output)

                        # Display in live console or stderr using update_live_display
                        if output.strip():
                            update_live_display(f"[red]{output.rstrip()}[/red]")

                # Show completion status in the live console
                status = (
                    "[green]✓[/green]"
                    if process.returncode == 0
                    else f"[red]✗ (code: {process.returncode})[/red]"
                )
                update_live_display(f"[dim]Command completed: {status}[/dim]")

                break

        stdout_result = "".join(stdout_capture)
        stderr_result = "".join(stderr_capture)
        return stdout_result, stderr_result, process.returncode
    except Exception as e:
        display_warning(f"Failed to execute command: {command}", e)
        return "", str(e), 1


# Register this tool with the registry
register(
    name="execute_command",
    function=execute_command,
    description="Execute a shell command",
    parameters={
        "command": {
            "type": "string",
            "description": "Command to execute",
        }
    },
    returns="Tuple containing (stdout, stderr, return_code)",
    requires_confirmation=True,  # Modifies the system
)
