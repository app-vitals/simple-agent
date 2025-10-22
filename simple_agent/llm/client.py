"""LLM client for model integration."""

from typing import Any

import litellm

from simple_agent.config import config
from simple_agent.display import display_error


class LLMClient:
    """Client for interacting with Large Language Model APIs."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the LLM client.

        Args:
            api_key: Optional API key, if not provided will look for an environment variable
        """
        self.api_key = api_key or config.llm.api_key

        # Initialize token counters
        self.tokens_sent = 0
        self.tokens_received = 0
        self.completion_cost = 0.0

        # Configure LiteLLM
        litellm.drop_params = True  # Don't send unnecessary params

    def send_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | str | None = None,
    ) -> Any | None:
        """Send a completion request to the LLM API.

        Args:
            messages: List of conversation messages in chat format
            tools: Optional list of tool definitions
            tool_choice: Optional tool choice (auto, required, or specific tool)

        Returns:
            The raw API response object, or None if an error occurs
        """
        if not self.api_key:
            display_error("No API key provided")
            return None

        try:
            # Call the model using config
            params: dict[str, Any] = {
                "model": config.llm.model,
                "messages": messages,
                "api_key": self.api_key,
            }

            # Add optional parameters if specified
            if tools:
                params["tools"] = tools
                # Use provided tool_choice or default to auto
                if tool_choice:
                    params["tool_choice"] = tool_choice
                else:
                    params["tool_choice"] = "auto"

            # Call the LLM API
            response = litellm.completion(**params)

            # Update token counters from response
            self.tokens_sent += response.usage.prompt_tokens
            self.tokens_received += response.usage.completion_tokens

            # Calculate cost using litellm.completion_cost function
            prompt_cost, completion_cost = litellm.cost_per_token(
                model=config.llm.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )
            self.completion_cost += prompt_cost + completion_cost

            return response
        except Exception as e:
            display_error(f"API Error: {e}")
            return None

    def get_message_content(self, response: Any) -> tuple[str | None, list | None]:
        """Extract content and tool calls from a completion response.

        Args:
            response: The LLM API response object

        Returns:
            Tuple of (message_content, tool_calls) - either may be None
        """
        if not response or not hasattr(response, "choices") or not response.choices:
            return None, None

        message = response.choices[0].message
        content = message.content
        tool_calls = getattr(message, "tool_calls", None)

        return content, tool_calls

    def get_token_counts(self) -> tuple[int, int, float]:
        """Get the current token counts and completion cost.

        Returns:
            Tuple of (tokens_sent, tokens_received, completion_cost)
        """
        return self.tokens_sent, self.tokens_received, self.completion_cost
