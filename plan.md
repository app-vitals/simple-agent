# Plan: Context-First Execution Assistant

## Objective

Build a sustainable, context-aware execution assistant through **structured context representation** and **interactive compression workflows**. Focus on token efficiency and human-readable context.

## Core Insight

After real-world usage, we discovered:
- **Atomic fact extraction creates noise, not signal** (107 entries from one conversation)
- **Context files larger than source messages** (28KB context from 22KB messages)
- **Lost strategic thinking and relationships** when atomized
- **No compression mechanism** → linear token growth

**Solution:** Manual compression workflow that preserves narrative, uses structured markdown, and dramatically reduces tokens.

---

## Phase 1: Context Representation & Compression ✅ COMPLETE

### ✅ MCP Foundation (COMPLETED)

We already have working MCP integration:
- Toggl (time tracking)
- Trello (boards and cards)
- Linear (issue tracking)
- Dynamic tool registration
- MCP configuration at `.simple-agent/mcp_servers.json`

**Keep this.** MCP works great for pulling external context when needed.

### ✅ Step 1: Markdown Context Structure (COMPLETE)

**Goal:** Replace JSON context with human-readable, structured markdown.

**File Structure:**
```
~/src/<project>/
├── context/                    # Visible, editable context
│   ├── business.md            # Clients, team, revenue
│   ├── strategy.md            # Positioning, decisions, tradeoffs
│   ├── goals.md               # Immediate → mid-term → long-term
│   └── decisions.md           # Key decisions with reasoning
├── context-archive/           # Session archives
│   └── 2025-10-23-initial-context.md
└── .simple-agent/             # Hidden implementation
    ├── messages.json          # Current session only
    └── mcp_servers.json       # MCP configuration
```

**Goals Structure with Temporal Tracking:**
```markdown
# Goals

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

## Long-term (1-3 years)
- [ ] Reach 100K users
- [ ] Expand to 3 new markets
```

**Tasks:**
- [x] Remove `context/extractor.py` (auto-extraction)
- [x] Remove `context/manager.py` or simplify to file I/O only
- [x] Remove auto-extraction background thread from `agent.py`
- [x] Create context file templates (business, strategy, goals, decisions)
- [x] Update agent startup to read `context/*.md` files
- [x] Inject markdown context into system prompt
- [x] Add today's date to system prompt for temporal awareness

**Success Criteria:** ✅
- Context stored as markdown, not JSON
- Files in visible `context/` directory
- Agent reads context at startup via `context/loader.py`
- Context included in system prompt on every request
- Today's date included for temporal tracking

### ✅ Step 2: Interactive Compression Command (COMPLETE)

**Goal:** Build `/compress` command that uses existing file tools (Read/Edit/Write).

**User Flow:**
```
User: /compress

Agent: "I'll compress this session to context. Reviewing conversation..."

[Agent uses Read tool to load context/business.md]
Agent: "Reading current business context..."

[Agent uses Edit tool to update]
Agent: "I'm updating the team member entry to capture new responsibilities:
- OLD: Alex (engineer) joining in December 2025
- NEW: [shows updated section with role details, start date, initial projects]"

User: [approves change]

[Agent uses Edit tool for goals.md]
Agent: "Adding API integration deadline to context/goals.md..."

[Agent uses Write tool for archive]
Agent: "Archiving full session to context-archive/2025-10-23-project-planning.md..."

[Agent clears messages.json]
Agent: "✓ Session compressed
✓ 3 context files updated
✓ Session archived
✓ Messages cleared"
```

**Compression System Prompt:**
```markdown
# Compression Task

You are compressing a conversation session into structured context files.

## Instructions
1. Read the ENTIRE conversation history
2. Identify:
   - New information (clients, projects, people, decisions)
   - Strategic thinking (options, tradeoffs, reasoning)
   - Updates to existing context (progress, status changes)
   - Goals (with start dates, deadlines, progress)
   - Important decisions and rationale
3. Organize into appropriate context files
4. Preserve narrative and relationships
5. Write concise but complete summaries

## Context Files
- `context/business.md` - Clients, team, revenue, operations
- `context/strategy.md` - Positioning, market, strategic decisions
- `context/goals.md` - Hierarchical goals with temporal tracking
- `context/decisions.md` - Key decisions with context
- Create new files if needed

## Writing Style
- Use headers and subheaders for hierarchy
- Include specific details (dates, numbers, names)
- Capture "why" not just "what"
- Link related concepts
- Use checkboxes for trackable items
- Preserve uncertainty and open questions

## Process
Use existing file tools (Read, Edit, Write) to:
1. Read current context files
2. Edit to update existing sections
3. Write new files or archives
4. User approves each change interactively

## User Instructions
{optional_user_instructions}
```

**Tasks:**
- [x] Create compression system prompt in `context/compression_prompt.py`
- [x] Implement `/compress [instructions]` command handler in CLI
- [x] Build compression workflow using Read/Edit/Write tools
- [x] Archive session to `context-archive/YYYY-MM-DD-topic.md`
- [x] Clear `messages.json` after compression via `_handle_compression()`
- [ ] Add compression suggestions (e.g., after 20+ messages) - DEFERRED

**Success Criteria:** ✅
- `/compress` reviews full conversation history
- Uses Read/Edit/Write tools with user confirmation
- Updates context files preserving narrative and strategic thinking
- Archives complete session with analysis
- Clears messages for fresh start
- 2-4x token reduction achieved (11KB context vs 20KB+ messages)

### ✅ Step 3: Remove Legacy Context System (COMPLETE)

**Goal:** Clean up old auto-extraction system.

**Tasks:**
- [x] Delete `context/extractor.py`
- [x] Delete `context/manager.py`, `context/globals.py`, `context/prompts.py`, `context/schema.py`
- [x] Remove auto-extraction call from `agent.py`
- [x] Remove context-specific slash commands:
  - [x] `/show-context` → removed
  - [x] `/clear-context` → removed
  - [x] `/sync-context` → removed
- [x] Update tests to remove extraction tests
- [x] Keep `/clear` command for clearing messages without compression

**Success Criteria:** ✅
- No automatic extraction after each message
- Only manual `/compress` workflow
- Cleaner codebase (removed 5 context files)
- Lower token costs (no extraction LLM calls)

### ✅ Step 4: Project-Scoped Context (COMPLETE)

**Goal:** Support different context per project directory.

**Current Behavior:**
```
~/.simple-agent/context.json  # Global context
```

**New Behavior:**
```
~/src/simple-agent/context/   # Simple Agent project context
~/src/my-startup/context/     # Business/startup context
~/src/client-project/context/ # Client project context
```

**Agent Startup:**
```python
def load_context():
    cwd = os.getcwd()

    # Load project context from current directory
    project_context = read_context_files(f"{cwd}/context/")

    return project_context
```

**Tasks:**
- [x] Update context loading to check `<cwd>/context/`
- [x] Context loader implemented in `simple_agent/context/loader.py`
- [x] Document context scoping in CLAUDE.md

**Success Criteria:** ✅
- Context scoped to current working directory
- Different projects maintain separate context
- No global context file (deferred until needed)

---

## Phase 2: Context Intelligence

### Step 5: Optimize Context Loading

**Goal:** Handle large context files efficiently.

**Progressive Enhancement:**

**Level 1: Load Everything** (start here)
```python
context = read_all_context_files("context/*.md")
# Inject full context into system prompt
```

**Level 2: Section-Based Loading** (when context > 20KB)
```python
sections = parse_context_sections("context/*.md")
relevant = select_relevant_sections(sections, recent_messages)
# Load only relevant sections, list others as available
```

**Level 3: Semantic Search** (when context > 100KB)
```python
relevant = semantic_search(user_query, vector_index)
# Vector search for relevant context chunks
```

**Tasks:**
- [ ] Monitor context file sizes
- [ ] Implement section parsing when needed
- [ ] Add "Available Context" listing to system prompt
- [ ] Agent can use Read tool to load more context on demand

**Success Criteria:**
- Efficient context loading at any scale
- Graceful degradation as context grows
- Agent aware of what context is available

### Step 6: Enhanced Compression

**Goal:** Improve compression quality through iteration.

**Enhancements:**
- [ ] Interactive compression with agent questions
  - "Should this go under 'Immediate Goals' or 'Team Decisions'?"
  - "Is this an active decision or just context?"
  - "Any key insights I'm missing?"
- [ ] Compression quality metrics
  - Measure token reduction
  - Track context file sizes
  - User satisfaction with compressions
- [ ] Smart compression suggestions
  - After major decisions
  - After long conversations (20+ messages)
  - When user says "that's all for now"

**Tasks:**
- [ ] Add interactive questions during compression
- [ ] Track compression metrics
- [ ] Implement smart suggestion triggers
- [ ] Allow compression edits/refinements

**Success Criteria:**
- High-quality compressions preserve key insights
- User confident in compressed context
- Minimal information loss

### Step 7: Calendar Integration (Optional)

**Goal:** Add time-awareness through calendar MCP.

**Approach:**
- [ ] Add Google Calendar MCP server to config
- [ ] Include calendar events in context when relevant
- [ ] Extract upcoming events during compression
- [ ] Use for "what's next" time-based recommendations

**This is lower priority** - context representation is more important.

---

## Phase 3: Long-term Goals (Future)

### Goal Progress Tracking

Goals are already in `context/goals.md` with temporal tracking. Future enhancements:

- [ ] Agent proactively updates goal progress during compression
- [ ] Detects milestone achievements
- [ ] Suggests next steps toward goals
- [ ] Identifies opportunities (e.g., "recent work would make a good blog post")

### Proactive Nudges

Once context is stable:

- [ ] "No progress on goal X in 2 weeks"
- [ ] "You have 90 minutes before standup - perfect for task Y"
- [ ] "Sprint deadline in 2 days, 3 tickets remaining"

---

## Success Metrics

### Phase 1 Targets

**Context Quality:**
- ✅ Preserves narrative and relationships (not atomic facts)
- ✅ Human-readable and editable
- ✅ 3-4x more compact than message history
- ✅ Strategic thinking captured

**Token Efficiency:**
- ✅ 20KB conversation → 5KB context
- ✅ Fresh sessions start with minimal context
- ✅ No auto-extraction token costs
- ✅ Sustainable for long-term projects

**User Experience:**
- ✅ Visible context files (not hidden JSON)
- ✅ Interactive compression with confirmation
- ✅ Simple commands (`/compress`, `/clear`)
- ✅ Natural file editing workflow

### Phase 2 Targets

**Context Intelligence:**
- Efficient loading at any scale
- Smart compression suggestions
- High compression quality
- Interactive refinement

### Phase 3 Targets

**Goal Achievement:**
- Consistent progress on goals
- Opportunistic progress capture
- Proactive helpful suggestions

---

## Migration Notes

### What Changes

**Removed:**
- Auto-extraction after every message
- `context/extractor.py`
- Context stored in `.simple-agent/context.json`
- Context-specific commands (`/show-context`, `/clear-context`, `/sync-context`)

**Added:**
- Markdown context in visible `context/` directory
- `/compress` command with interactive workflow
- Session archiving to `context-archive/`
- Project-scoped context
- Goals with temporal tracking

**Unchanged:**
- MCP integration (Toggl, Linear, Trello)
- File operation tools
- Command execution
- CLI interface
- Tool confirmation system
- Message auto-saving

### No Breaking Changes

Users can:
- Continue using all existing tools
- Use MCP integrations
- Work with files and commands
- New `/compress` is purely additive

---

## Next Actions

### Immediate (Phase 1, Step 1-3)

1. [ ] Remove auto-extraction system
   - Delete `context/extractor.py`
   - Remove background thread from `agent.py`
   - Remove context-specific commands

2. [ ] Implement markdown context loading
   - Read `context/*.md` at startup
   - Inject into system prompt
   - Test with sample context files

3. [ ] Build `/compress` command
   - Create compression system prompt
   - Use Read/Edit/Write tools for updates
   - Archive sessions
   - Clear messages

4. [ ] Update documentation
   - Update CLAUDE.md with new approach
   - Add context file templates
   - Document compression workflow

### Near-term (Phase 1, Step 4)

5. [ ] Project-scoped context
   - Load from `<cwd>/context/`
   - Support global context optionally
   - Test with multiple projects

### Future (Phase 2-3)

6. [ ] Optimize context loading
7. [ ] Enhanced compression
8. [ ] Calendar integration
9. [ ] Goal progress tracking
10. [ ] Proactive suggestions
