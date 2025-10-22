"""Context extraction using LLM."""

import json

from simple_agent.context.globals import get_context_manager
from simple_agent.context.prompts import (
    CONTEXT_EXTRACTION_PROMPT,
    get_context_extraction_prompt,
)
from simple_agent.context.schema import ContextExtractionResponse, ContextType
from simple_agent.llm.client import LLMClient


class ContextExtractor:
    """Extracts context facts from user interactions using LLM."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """Initialize the context extractor.

        Args:
            llm_client: LLM client to use for extraction. If None, creates a new one.
        """
        self.llm_client = llm_client or LLMClient()
        self.context_manager = get_context_manager()

    def extract_from_messages(
        self,
        messages: list[dict],
    ) -> list[str]:
        """Extract context from a list of conversation messages.

        Args:
            messages: List of messages in OpenAI format (role, content, tool_calls, etc.)

        Returns:
            List of extracted facts
        """
        # Find the last user message and subsequent tool calls
        user_message = None
        tool_calls = []

        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break
            elif msg.get("role") == "assistant" and msg.get("tool_calls"):
                # Convert tool_calls to dict format for our prompt
                for tc in msg.get("tool_calls", []):
                    function = tc.get("function", {})
                    name = function.get("name")
                    args = function.get("arguments", {})

                    # Parse arguments if it's a JSON string
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}

                    tool_calls.append({"name": name, "arguments": args})

        return self.extract_and_store(
            user_message=user_message,
            tool_calls=tool_calls if tool_calls else None,
        )

    def extract_and_store(
        self,
        user_message: str | None = None,
        tool_calls: list[dict] | None = None,
        tool_results: list[dict] | None = None,
    ) -> list[str]:
        """Extract context from an interaction and store it.

        Args:
            user_message: The user's message
            tool_calls: List of tool calls that were made
            tool_results: Results from tool executions

        Returns:
            List of extracted facts
        """
        # Skip extraction if there's nothing to analyze
        if not user_message and not tool_calls:
            return []

        # Generate the extraction prompt
        user_prompt = get_context_extraction_prompt(
            user_message=user_message,
            tool_calls=tool_calls,
            tool_results=tool_results,
        )

        # Define the extraction tool
        extraction_tool = {
            "type": "function",
            "function": {
                "name": "extract_context",
                "description": "Extract context facts from the interaction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "facts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of extracted context facts",
                        }
                    },
                    "required": ["facts"],
                },
            },
        }

        # Call LLM with forced tool choice
        response = self.llm_client.send_completion(
            messages=[
                {"role": "system", "content": CONTEXT_EXTRACTION_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            tools=[extraction_tool],
            tool_choice={"type": "function", "function": {"name": "extract_context"}},
        )

        if not response:
            return []

        # Extract tool call from response
        message = response.choices[0].message
        if not hasattr(message, "tool_calls") or not message.tool_calls:
            return []

        # Parse the tool call arguments using Pydantic
        tool_call = message.tool_calls[0]
        result = ContextExtractionResponse.model_validate_json(
            tool_call.function.arguments
        )
        facts: list[str] = result.facts

        # Store each fact in context manager
        for fact in facts:
            if fact and isinstance(fact, str):
                self.context_manager.add_context(
                    type=self._determine_context_type(fact, tool_calls),
                    source="llm_extraction",
                    content=fact,
                    metadata={
                        "user_message": user_message[:100] if user_message else None,
                        "extraction_method": "llm",
                    },
                )

        return facts

    def _determine_context_type(
        self,
        fact: str,
        tool_calls: list[dict] | None,
    ) -> ContextType:
        """Determine the most appropriate context type for a fact.

        Args:
            fact: The extracted fact
            tool_calls: Tool calls that were made (helps determine type)

        Returns:
            Appropriate ContextType
        """
        fact_lower = fact.lower()

        # Check if related to file operations
        if tool_calls:
            tool_names = [call.get("name", "") for call in tool_calls]
            if any(
                name in ["read_files", "write_file", "patch_file"]
                for name in tool_names
            ):
                return ContextType.FILE

        # Check for time-related keywords
        if any(
            keyword in fact_lower
            for keyword in [
                "deadline",
                "sprint",
                "standup",
                "meeting",
                "at ",
                "pm",
                "am",
            ]
        ):
            return ContextType.CALENDAR

        # Check for task-related keywords
        if any(
            keyword in fact_lower
            for keyword in ["pr #", "issue", "ticket", "task", "bug", "feature"]
        ):
            return ContextType.TASK

        # Default to manual type
        return ContextType.MANUAL

    def get_recent_context_summary(self, max_age_hours: int = 24) -> str:
        """Get a formatted summary of recent context.

        Args:
            max_age_hours: Only include context from last N hours

        Returns:
            Formatted string summary of recent context
        """
        entries = self.context_manager.get_context(max_age_hours=max_age_hours)

        if not entries:
            return "No recent context available."

        # Group by type
        by_type: dict[ContextType, list[str]] = {}
        for entry in entries:
            if entry.type not in by_type:
                by_type[entry.type] = []
            by_type[entry.type].append(entry.content)

        # Format summary
        lines = ["Recent Context:"]
        for context_type in [
            ContextType.TASK,
            ContextType.FILE,
            ContextType.CALENDAR,
            ContextType.MANUAL,
        ]:
            if context_type in by_type:
                type_name = context_type.value.replace("_", " ").title()
                lines.append(f"\n{type_name}:")
                for content in by_type[context_type][:5]:  # Max 5 per type
                    lines.append(f"  - {content}")

        return "\n".join(lines)
