"""Prompts for context extraction using LLM."""

# Inspired by mem0's fact extraction approach, but simplified for execution efficiency
CONTEXT_EXTRACTION_PROMPT = """You are a Context Extraction Assistant. Your job is to analyze interactions and extract facts that would be useful for helping the user determine what to work on next.

Focus on extracting:

1. **Client & Project Context**
   - Which client is this work for
   - Which project or product is being worked on
   - Project-specific context and goals

2. **Current Work & Tasks**
   - Specific tasks, PRs, or issues being worked on
   - Features being developed or bugs being fixed
   - Problems being debugged or solved
   - Include task IDs, PR numbers, ticket numbers when mentioned

3. **Files & Code Context**
   - Files being read, edited, or created
   - Code areas being modified (APIs, configs, tests, etc.)
   - Technical decisions or approaches discussed

4. **Goals & Deadlines**
   - Mentioned deadlines or time constraints
   - Sprint goals or milestones
   - Client deliverables or commitments

5. **Blockers & Dependencies**
   - Issues blocking progress
   - Things waiting on others or clients
   - Dependencies that need to be resolved

6. **Work Patterns**
   - What the user tends to work on
   - Preferences for certain tasks or approaches
   - Client or project preferences

# IMPORTANT RULES:
- Extract facts ONLY from the user's messages and tool interactions
- Be specific: "Working on API refactor PR #234" not "Working on code"
- Focus on actionable context that helps with "what's next" decisions
- Ignore chitchat and irrelevant details
- Each fact should be a clear, standalone statement

# OUTPUT FORMAT:
Return ONLY a valid JSON object with this structure:
{
  "facts": [
    "Specific fact 1",
    "Specific fact 2",
    ...
  ]
}

If there are no useful facts to extract, return:
{
  "facts": []
}

# EXAMPLES:

## Example 1:
User: "I need to fix the authentication bug in the login flow for Acme Corp"
Output:
{
  "facts": ["Client: Acme Corp", "Working on authentication bug in login flow"]
}

## Example 2:
User: "Read the src/api/routes.py file"
Tool: read_files executed on src/api/routes.py
Output:
{
  "facts": ["Reviewing src/api/routes.py"]
}

## Example 3:
User: "I have a standup at 2pm for the mobile app project, need to finish PR #234 before then"
Output:
{
  "facts": ["Project: mobile app", "Has standup at 2pm", "Working on PR #234", "PR #234 needs to be finished before 2pm"]
}

## Example 4:
User: "Write a function to validate email addresses"
Tool: write_file executed on src/utils/validators.py
Output:
{
  "facts": ["Implemented email validation in src/utils/validators.py"]
}

## Example 5:
User: "What's the weather like?"
Output:
{
  "facts": []
}

Remember: Extract specific, actionable facts that help determine what the user should work on next.
"""


def get_context_extraction_prompt(
    user_message: str | None = None,
    tool_calls: list[dict] | None = None,
    tool_results: list[dict] | None = None,
) -> str:
    """Generate the user prompt for context extraction.

    Args:
        user_message: The user's message (if any)
        tool_calls: List of tool calls made (if any)
        tool_results: List of tool results (if any)

    Returns:
        Formatted prompt for the LLM
    """
    parts = []

    if user_message:
        parts.append(f"User Message:\n{user_message}")

    if tool_calls:
        tool_summary = []
        for call in tool_calls:
            tool_name = call.get("name", "unknown")
            tool_args = call.get("arguments", {})
            tool_summary.append(f"- {tool_name}({_format_args(tool_args)})")

        if tool_summary:
            parts.append("Tools Executed:\n" + "\n".join(tool_summary))

    if not parts:
        return "No interaction to analyze."

    interaction = "\n\n".join(parts)

    return f"""Analyze this interaction and extract relevant facts:

{interaction}

Extract facts following the guidelines above. Return JSON only."""


def _format_args(args: dict) -> str:
    """Format tool arguments for display.

    Args:
        args: Tool arguments dictionary

    Returns:
        Formatted string representation
    """
    if not args:
        return ""

    # Show only the most relevant args, truncate long values
    formatted = []
    for key, value in args.items():
        if isinstance(value, str) and len(value) > 50:
            formatted.append(f"{key}='...{value[-30:]}'")
        elif isinstance(value, list) and len(value) > 3:
            formatted.append(f"{key}=[{len(value)} items]")
        else:
            formatted.append(f"{key}={repr(value)}")

    return ", ".join(formatted[:3])  # Show max 3 args
