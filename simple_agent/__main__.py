"""Main entry point for the simple-agent CLI."""

import argparse
import sys

from simple_agent.core.agent import Agent


def main():
    """Main entry point for the simple-agent CLI."""
    parser = argparse.ArgumentParser(
        description="Simple Agent - A CLI AI agent built on Unix philosophies"
    )
    parser.add_argument(
        "--version", 
        action="store_true", 
        help="Show version information"
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
        print("\nExiting Simple Agent.")
        sys.exit(0)


if __name__ == "__main__":
    main()