"""Command execution tools."""

import subprocess
import sys
from select import select

from rich.console import Console


def execute_command(command: str) -> tuple[str, str, int]:
    """Execute a shell command and return its output.

    Args:
        command: Command string to execute

    Returns:
        Tuple containing (stdout, stderr, return_code)
    """

    console = Console()
    console.print(f"[bold yellow]Executing:[/bold yellow] {command}")

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
                    sys.stdout.write(output)
                    sys.stdout.flush()
                    stdout_capture.append(output)

            if process.stderr in rlist and process.stderr is not None:
                output = process.stderr.readline()
                if output:
                    sys.stderr.write(output)
                    sys.stderr.flush()
                    stderr_capture.append(output)

            # Check if the process has finished
            if process.poll() is not None:
                # Read any remaining output
                if process.stdout is not None:
                    for output in process.stdout:
                        sys.stdout.write(output)
                        sys.stdout.flush()
                        stdout_capture.append(output)

                if process.stderr is not None:
                    for output in process.stderr:
                        sys.stderr.write(output)
                        sys.stderr.flush()
                        stderr_capture.append(output)
                break

        stdout_result = "".join(stdout_capture)
        stderr_result = "".join(stderr_capture)
        return stdout_result, stderr_result, process.returncode
    except Exception as e:
        error_msg = str(e)
        sys.stderr.write(f"ERROR: {error_msg}\n")
        sys.stderr.flush()
        return "", error_msg, 1
