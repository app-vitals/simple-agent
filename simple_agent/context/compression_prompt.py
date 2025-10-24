"""System prompt for compression workflow."""

from datetime import datetime

COMPRESSION_SYSTEM_PROMPT = """Today's date: {today}

You are compressing a conversation session into structured markdown context files.

Your task is to review the full conversation history and update context files to preserve:
- New information (clients, projects, people, decisions)
- Strategic thinking (options, tradeoffs, reasoning)
- Updates to existing context (progress, status changes)
- Goals (with start dates, deadlines, progress)
- Important decisions and rationale

## Context Files

Use these standard context files (create them if they don't exist):
- `context/business.md` - Clients, team, revenue, operations
- `context/strategy.md` - Positioning, market, strategic decisions
- `context/goals.md` - Hierarchical goals with temporal tracking
- `context/decisions.md` - Key decisions with context and reasoning

You may create additional context files if needed for specific domains.

## Writing Style

- Use headers and subheaders for hierarchy
- Include specific details (dates, numbers, names)
- Capture "why" not just "what"
- Link related concepts
- Use checkboxes for trackable items
- Preserve uncertainty and open questions
- Write in a narrative style that preserves relationships

## Goals Structure with Temporal Tracking

When updating goals, include progress tracking:

```markdown
## Immediate (Next 2 months)
- [ ] API v2 integration complete
  - Started: September 2025
  - Deadline: October 30, 2025
  - Elapsed: 3 weeks / 8 weeks (38%)
  - Status: Finishing up, deadline next week

## Mid-term (6 months)
- [ ] Launch product v2.0 by Q1 2026
  - Started: September 2025
  - Deadline: March 2026
  - Elapsed: 2 months / 6 months (33%)
  - Progress: 4/10 features complete (40%)
  - Remaining: 6 features in 4 months
```

## Process

Use the file tools to update context:

1. **Read existing context files** using `read_files` tool
2. **Update sections** using `patch_file` tool (user will confirm each change)
3. **Create new files** using `write_file` tool if needed
4. **Archive the session** to `context-archive/YYYY-MM-DD-topic.md`
5. After archiving, tell the user compression is complete

Important:
- Review the ENTIRE conversation, not just recent messages
- Preserve narrative flow and relationships between concepts
- Avoid atomizing information into disconnected facts
- Update existing sections rather than creating duplicates
- Focus on signal, not noise

## User Instructions

{user_instructions}
"""


def get_compression_prompt(
    conversation_history: list[dict],
    user_instructions: str = "",
) -> list[dict]:
    """Build messages for compression task.

    Args:
        conversation_history: Full conversation history to compress
        user_instructions: Optional user-provided instructions for compression

    Returns:
        Messages list with system prompt and conversation summary
    """
    # Build system prompt with today's date and user instructions
    today = datetime.now().strftime("%Y-%m-%d")
    system_prompt = COMPRESSION_SYSTEM_PROMPT.format(
        today=today,
        user_instructions=user_instructions or "No specific instructions provided.",
    )

    # Format conversation for review
    conversation_text = _format_conversation(conversation_history)

    user_prompt = f"""Please compress this conversation session into the context files.

Review the full conversation below and update the appropriate context files:

{conversation_text}

Steps:
1. Read existing context files to understand current state
2. Update relevant sections using patch_file (I'll confirm each change)
3. Create new context files if needed
4. Archive this session to context-archive/ with a descriptive filename
5. Let me know when compression is complete

Start by reading the existing context files."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _format_conversation(messages: list[dict]) -> str:
    """Format conversation history for compression review.

    Args:
        messages: List of conversation messages

    Returns:
        Formatted conversation text
    """
    lines = ["# Conversation History", ""]

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "system":
            # Skip system prompts in compression review
            continue
        elif role == "user":
            lines.append(f"**User:** {content}")
            lines.append("")
        elif role == "assistant":
            if msg.get("tool_calls"):
                # Show tool calls
                for tc in msg.get("tool_calls", []):
                    func = tc.get("function", {})
                    tool_name = func.get("name", "unknown")
                    lines.append(f"**Assistant:** [Called tool: {tool_name}]")
                lines.append("")
            elif content:
                lines.append(f"**Assistant:** {content}")
                lines.append("")
        elif role == "tool":
            # Show tool results briefly
            tool_name = msg.get("name", "unknown")
            lines.append(f"**Tool Result ({tool_name}):** {content[:200]}...")
            lines.append("")

    return "\n".join(lines)
