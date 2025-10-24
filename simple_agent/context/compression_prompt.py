"""System prompt for compression workflow."""

from datetime import datetime

COMPRESSION_SYSTEM_PROMPT = """Today's date: {today}

You are compressing a conversation session into structured markdown context files.

## CRITICAL: Compression = Distillation, Not Elaboration

**Your goal is to make context MORE CONCISE:**
- One clear sentence > three paragraphs of explanation
- Essential facts only - remove redundancy and over-explanation
- **Clean up existing verbose content** - distill over-detailed sections
- **Remove outdated/superseded information**
- **Context should SHRINK or stay same size** - if files grow significantly, you're over-explaining

**Anti-patterns to avoid:**
- ❌ Exhaustive scenario analysis ("If X... If Y...")
- ❌ Over-explaining with bullets when one sentence would do
- ❌ Duplicating information across files
- ❌ Expanding content that should stay the same or shrink

**Deduplication:**
- Before adding info, check if it exists in other files
- Use cross-references instead of duplicating
- Example: decisions.md has full context, business.md just says "see decisions.md"

## Context Files

Use these standard files:
- `context/business.md` - Clients, team, revenue, operations
- `context/strategy.md` - Positioning, market, strategic decisions
- `context/goals.md` - Hierarchical goals with temporal tracking
- `context/decisions.md` - Key decisions with context and reasoning

Create additional files only if needed for specific domains.

## Writing Style

- **Be concise** - prefer brevity over completeness
- Capture "why" not just "what"
- Include specific details (dates, numbers, names) but don't over-explain
- Use checkboxes for trackable items
- Preserve uncertainty and open questions

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

## Active vs Completed Discussions

**Completed discussions** (clear outcome/decision made):
- Distill heavily to essential facts and outcomes
- Archive full conversation for reference
- Remove from active context once captured

**Active/ongoing discussions** (still exploring, no final decision):
- Add "## Active Discussions" section to relevant file
- Include:
  - What question/decision is being explored
  - What's been discussed so far (brief summary)
  - Where the conversation left off
  - Next steps or open questions
- This preserves conversational momentum across sessions

## Process

1. **Read existing context files** using `read_files` tool
2. **Plan your updates** - think through what needs to change across ALL files first
3. **Update sections** using `patch_file` tool (user confirms each change)
   - Cleanup pass: Distill verbose sections, remove outdated info, deduplicate
   - New content pass: Add new information from this conversation
   - **CRITICAL**: Copy `old_string` EXACTLY from the file - whitespace, line breaks, punctuation must match perfectly
4. **Archive session** to `context-archive/YYYY-MM-DD-topic.md`
5. Tell user compression is complete

**Key principles:**
- Review ENTIRE conversation, not just recent messages
- One pass per file - don't keep going back to add more detail
- Preserve narrative flow, avoid atomizing into disconnected facts

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
