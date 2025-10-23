"""Main entry point for the simple-agent CLI."""

import argparse
import sys

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from simple_agent.core.agent import Agent


def main() -> None:
    """Main entry point for the simple-agent CLI."""
    parser = argparse.ArgumentParser(
        description="Simple Agent - A CLI AI agent built on Unix philosophies"
    )
    parser.add_argument(
        "--version", action="store_true", help="Show version information"
    )

    args = parser.parse_args()

    if args.version:
        version_style = Style.from_dict(
            {
                "app": "ansibrightgreen",
                "version": "ansiyellow",
            }
        )
        print_formatted_text(
            HTML("<app>simple-agent</app> <version>version 0.1.0</version>"),
            style=version_style,
        )
        return

    # Run the agent
    agent = Agent()

    try:
        agent.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C with a clean exit via prompt_toolkit
        print_formatted_text(HTML("<ansiyellow>\nInterrupted. Exiting.</ansiyellow>"))
    finally:
        # Ensure MCP servers are shut down cleanly
        if agent.mcp_manager:
            agent.mcp_manager.shutdown_all_sync()
        sys.exit(0)


if __name__ == "__main__":
    main()
