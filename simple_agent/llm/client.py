"""LLM client for model integration."""

import os

import litellm
from rich.console import Console


class LLMClient:
    """Client for interacting with Large Language Model APIs."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the LLM client.

        Args:
            api_key: Optional API key, if not provided will look for an environment variable
        """
        self.console = Console()
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        # Configure LiteLLM
        litellm.drop_params = True  # Don't send unnecessary params

    def send_message(
        self, message: str, context: list[dict] | None = None
    ) -> str | None:
        """Send a message to the AI model API.

        Args:
            message: The message to send
            context: Optional conversation context

        Returns:
            The model's response, or None if an error occurs
        """
        if not self.api_key:
            self.console.print("[bold red]Error:[/bold red] No API key provided")
            return None

        try:
            # Create messages format
            messages = context or []
            messages.append({"role": "user", "content": message})

            # Call the model
            response = litellm.completion(
                model="anthropic.claude-3-haiku-20240307",
                messages=messages,
                api_key=self.api_key,
            )

            # Extract and return the response content
            content = response.choices[0].message.content
            if content is None:
                return None
            return str(content)
        except Exception as e:
            self.console.print(f"[bold red]API Error:[/bold red] {e}")
            return None
