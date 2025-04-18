"""Core agent loop implementation."""

import argparse
from typing import Dict, List, Optional

from rich.console import Console

from simple_agent.api.client import ApiClient
from simple_agent.exec.command import execute_command
from simple_agent.files.operations import read_file, write_file


class Agent:
    """Simple agent that manages the conversation loop."""
    
    def __init__(self):
        """Initialize the agent."""
        self.context = []
        self.console = Console()
        self.api_client = ApiClient()
    
    def run(self):
        """Run the agent's main loop."""
        self.console.print("[bold green]Simple Agent[/bold green] ready. Type 'exit' to quit.")
        
        while True:
            # Get input from user
            user_input = input("> ")
            
            if user_input.lower() == "exit":
                break
            
            # Process the user input
            self._process_input(user_input)
    
    def _process_input(self, user_input: str):
        """Process user input and generate a response.
        
        Args:
            user_input: The user's input text
        """
        # Simple processing for now - will be expanded
        self.console.print(f"Received: {user_input}")