# Plan: First Steps Toward Execution Assistant

## Objective

Implement the minimal viable transformation from Simple Agent to Execution Efficiency Assistant. Focus on **Daily Execution Efficiency** use case first.

## Guiding Principle

**Start with the simplest possible version that provides value:** Manual context gathering + basic "what's next" recommendation.

---

## Phase 1: Foundation

### ✅ Step 1: Context System Foundation (COMPLETED)

Built a disk-based context storage system with automatic cleanup.

**What we built:**
- Context manager with JSON persistence at `~/.simple-agent/context.json`
- Context types: MANUAL, FILE, CALENDAR, TASK, TIME_TRACKING, GOAL
- Auto-cleanup of entries older than 7 days
- Full test coverage (13 tests)

### ✅ Step 2: Dynamic Context Extraction (COMPLETED)

Instead of manual context input, we built **automatic LLM-powered context extraction**.

**What we built:**
- Context extraction prompt inspired by mem0
- Extracts facts from user messages and tool calls automatically
- Runs after each agent interaction
- Slash commands: `/show-context`, `/clear-context`
- 20 new tests, 91.65% coverage

**This is better than the original plan** because:
- No manual effort required
- Context builds automatically as you work
- Smarter extraction (understands client/project/task relationships)

### ✅ Step 3: Inject Context into System Prompt (COMPLETED)

**Goal:** Make context available to the agent for all responses by including it in the system prompt.

**What we built:**
- Dynamic system prompt generation in `agent.py:_build_system_prompt()`
- Automatic injection of recent context (24 hours)
- Context-aware instructions for the LLM
- Formatted context summary grouped by type

**Success Criteria (Met):**
- ✅ Context automatically included in every request
- ✅ Agent can reference context naturally in responses
- ✅ No extra tool calls needed (context always available)
- ✅ System prompt updates dynamically on each interaction

### ✅ Step 4: External Integrations via MCP (COMPLETED)

**Goal:** Add external context sources through Model Context Protocol (MCP).

**What we built:**
- MCP server manager and adapter in `tools/mcp/`
- Dynamic tool registration from MCP servers
- Configuration via `~/.simple-agent/mcp_servers.json`
- Support for environment variables per server

**Integrated MCP Servers:**
1. **Toggl** - Time tracking integration
   - Track current time entries
   - View time spent on tasks
   - Historical time data

2. **Trello** - Board and card management
   - View boards and cards
   - Check card status and priorities
   - Track project progress

3. **Linear** - Issue tracking
   - View assigned issues
   - Check sprint/cycle status
   - Track project timelines

**Success Criteria (Met):**
- ✅ MCP servers load on agent startup
- ✅ Tools from MCP servers available to LLM
- ✅ Agent can query Toggl, Trello, Linear via natural language
- ✅ Context can be enriched from multiple sources

**Files Created:**
- `/simple_agent/tools/mcp/manager.py` - MCP server lifecycle
- `/simple_agent/tools/mcp/adapter.py` - Tool adaptation layer
- `/simple_agent/config.py` - MCP configuration loading

---

## Phase 2: Enhanced Context Intelligence (Current Focus)

**Building on completed Phase 1 foundation:**

### Organic Context Building (Current Approach)

**Philosophy:** Let context build naturally through user interactions rather than explicit sync.

**How it works:**
- User asks: "What's on my Toggl timer?" → LLM calls MCP tool → Response extracted to context
- User asks: "Show my Linear issues" → LLM calls MCP tool → Issues extracted to context
- User asks: "What should I work on next?" → Agent references accumulated context

**Benefits:**
- No background sync complexity
- Context reflects what user actually cares about
- Simpler implementation and maintenance
- Already working via existing context extraction

### Step 5: Proactive Context Gathering via System Prompt

**Goal:** Guide the agent to proactively gather context when asked "what's next" using available MCP tools.

**Approach:**
- Update system prompt to encourage checking current state before recommendations
- Agent naturally calls MCP tools (Toggl, Linear, Trello, Calendar) when needed
- Tool responses get extracted to context automatically (existing mechanism)
- Future "what's next" queries benefit from accumulated context

**Example Flow:**
```
User: "What should I work on next?"

Agent thinks: "I should check current context first"
→ Calls Toggl MCP tool to see current timer
→ Calls Linear MCP tool to see active issues
→ Calls Calendar MCP tool to see next meetings
→ Provides recommendation based on fresh data
→ All responses automatically extracted to context

Next time user asks: Context already available, agent references it directly
```

**Tasks:**
1. Enhance system prompt to encourage proactive tool usage for context gathering
2. Test that agent naturally calls MCP tools when asked "what's next"
3. Verify tool responses get extracted to context
4. Confirm subsequent queries use accumulated context without redundant tool calls

**Success Criteria:**
- First "what's next" query triggers context gathering via MCP tools
- Recommendations based on real-time data
- Subsequent queries leverage accumulated context
- Context naturally refreshes as user interacts

**Files to Modify:**
- `/simple_agent/core/agent.py` - Enhance SYSTEM_PROMPT with context-gathering guidance

### Step 6: Calendar Integration via MCP

**Goal:** Add time-awareness through calendar integration.

**Approach:**
- Use existing MCP Google Calendar server (available)
- Add to `mcp_servers.json` configuration
- Integrate with context sync

**Tasks:**
1. Add Google Calendar MCP server to config
2. Include calendar in context sync
3. Extract upcoming events as CALENDAR context type

**Additional MCP Integrations to Consider:**
- Git/GitHub MCP server (recent commits, PRs, branch status)
- Slack MCP server (communication context)
- File system watcher (automatic FILE context from edits)

---

## Phase 3: Long-term Goals (Future)

**After daily efficiency is solid:**

### Goal Inference and Tracking

**Approach:** Infer goals from existing documents (vision.md, plan.md, roadmaps) and confirm with user.

**Flow:**
```
User: "What are my goals?"

Agent:
→ Reads vision.md, plan.md, README.md
→ Infers potential goals from content
→ Proposes goals with milestones
→ Asks for user confirmation

Agent: "Based on your documents, I see these goals:
1. Ship Phase 2 context enhancements (milestone: Step 5 complete by end of week)
2. Reach 90% test coverage (currently 88%)
3. Add calendar integration (blocked by: finding MCP server)

Should I track these? Any adjustments?"

User confirms → Goals stored as GOAL context type
```

**Commands:**
1. **Implicit goal inference** - Agent reads files to understand goals
2. **`/set-goal`** - Explicitly define a goal with milestones (with confirmation)
3. **`/track-goal`** - View goal progress and milestones
4. **Goal context** - Stored like other context, included in system prompt

**Storage:**
- Goals stored in `context.json` as GOAL type
- Milestones as metadata on goal entries
- Progress tracked by checking file changes, commits, context entries

**Proactive Suggestions:**
- When working on related files, agent suggests: "This relates to your goal X"
- Detects opportunities: "Your recent work would help with milestone Y"
- Gentle nudges: "No progress on goal Z in 2 weeks, want to make time for it?"

---

## Implementation Timeline

### ✅ Phase 1: Foundation (COMPLETED)
- ✅ Step 1: Context system foundation
- ✅ Step 2: Dynamic LLM-based context extraction
- ✅ Step 3: Context injection into system prompt
- ✅ Step 4: MCP integration layer with Toggl, Trello, Linear

### Phase 2: Enhanced Intelligence (Current)
- [ ] Step 5: Enhanced MCP tool response extraction
  - [ ] Review extraction quality with MCP tools
  - [ ] Improve context type detection for MCP responses
  - [ ] Test organic context building from MCP interactions
- [ ] Step 6: Calendar integration via MCP
  - [ ] Add Google Calendar MCP server
  - [ ] Test time-aware recommendations
  - [ ] Verify calendar context extraction

### Phase 3: Long-term Goals (Future)
- [ ] Goal inference from existing documents
- [ ] `/set-goal` and `/track-goal` commands with confirmation
- [ ] Goal progress tracking via file/commit analysis
- [ ] Proactive goal-related suggestions

---

## Decision Points

### After Step 3 (Manual Context + Recommendations)

**Question:** Is manual context sufficient, or do we need integrations?
- If manual context provides good value: slow down, polish UX
- If context is too stale/incomplete: accelerate to Step 4

### After Step 4 (Calendar Integration)

**Question:** Which integration adds most value next?
- If time-blocking is key bottleneck: focus on calendar features
- If task selection is key bottleneck: add Jira/Linear
- If context-switching is key bottleneck: add Git/file context

### After Phase 1

**Question:** Daily efficiency vs long-term goals?
- If daily execution improved significantly: move to Phase 3
- If still struggling with priorities: add more sources (Phase 2)
- If integrations are too complex: simplify and polish

---

## Technical Notes

### Keep It Simple

- **Simple storage**: JSON file at `~/.simple-agent/context.json` (no database)
- **MCP-based integrations**: No custom API clients, use MCP servers
- **Organic context building**: No background sync, context builds through natural interactions
- **Minimal config**: Reuse existing `~/.simple-agent/` directory

### Make It Easy to Extend

- **MCP pattern**: Add new integrations by configuring MCP servers
- **Context extraction**: LLM automatically extracts facts from tool responses
- **Typed schemas**: Use Pydantic for all context data
- **Test each feature**: Unit tests for context extraction and sync

### Migration Path

This plan requires minimal changes to existing Simple Agent:
- ✅ Keep all existing tools (file, command execution)
- ✅ Keep CLI interface and UX
- ✅ Keep tool registry system
- ✅ Extend with new context system (additive)
- ✅ Extend with new planning tools (additive)
- ✅ Update system prompt (refinement)

No breaking changes needed.

---

## Success Indicators

### ✅ Phase 1 Achievements (Current State)

1. **Automatic context extraction from interactions:**
   - ✅ Context builds automatically as user works
   - ✅ File operations, tool calls extracted to context
   - ✅ View context with `/show-context`, clear with `/clear-context`

2. **Context-aware conversations:**
   - ✅ System prompt includes recent context (24h)
   - ✅ Agent references previous work naturally
   - ✅ MCP tools (Toggl, Trello, Linear) available on-demand

3. **Core capabilities retained:**
   - ✅ File operations (read, write, patch)
   - ✅ Command execution
   - ✅ Interactive CLI with rich features

### Phase 2 Target (Next)

1. **Organic context building through interactions:**
   ```
   > What's on my Toggl timer?
   [Agent calls MCP tool, shows result, context extracted automatically]

   > What Linear issues do I have?
   [Agent calls MCP tool, shows issues, context extracted automatically]

   > What should I work on next?
   [Agent uses accumulated context from previous interactions]
   ```

2. **Context-enriched recommendations:**
   ```
   > what should I work on next?

   Agent: "Based on your context:
   - You have 90 minutes before standup (calendar)
   - Already spent 2h 15m on API refactor today (Toggl)
   - Linear sprint ends in 2 days with 3 tickets left
   - Urgent Trello card: Deploy v2.0

   Recommendation: Switch to Linear ticket ENG-456 (auth bug)

   Reasoning:
   - Sprint deadline approaching
   - You've hit context-switch point on API work
   - 90 min is enough to make meaningful progress
   - Unblocks deployment (Trello dependency)"
   ```

The assistant becomes truly context-aware and proactive through MCP integrations.

---

## Next Actions

**Immediate (Phase 2, Step 5):**
1. Test current context extraction with MCP tools
2. Enhance `_determine_context_type()` for MCP-specific patterns
3. Verify organic context building through natural interactions
4. Validate that accumulated context improves "what's next" recommendations

**Near-term (Phase 2, Step 6):**
1. Add Google Calendar MCP server to configuration
2. Test time-aware recommendations with calendar data
3. Verify calendar events extracted to context

**Future (Phase 3):**
1. Implement goal inference from documents (vision.md, plan.md, etc.)
2. Add `/set-goal` with user confirmation for inferred goals
3. Implement `/track-goal` for progress visibility
4. Add proactive goal suggestions based on current work
