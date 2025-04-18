"""Main entry point for the simple-agent CLI."""

import argparse
import sys

from rich.console import Console

from simple_agent.core.agent import Agent


def main() -> None:
    """Main entry point for the simple-agent CLI."""
    console = Console()
    parser = argparse.ArgumentParser(
        description="Simple Agent - A CLI AI agent built on Unix philosophies"
    )
    parser.add_argument(
        "--version", action="store_true", help="Show version information"
    )

    args = parser.parse_args()

    if args.version:
        print("simple-agent version 0.1.0")
        return

    # Run the agent
    agent = Agent()

    try:
        agent.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C with a clean exit
        console.print("\n[yellow]Interrupted. Exiting.[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
