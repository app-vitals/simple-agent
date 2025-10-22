# Plan: First Steps Toward Execution Assistant

## Objective

Implement the minimal viable transformation from Simple Agent to Execution Efficiency Assistant. Focus on **Daily Execution Efficiency** use case first.

## Guiding Principle

**Start with the simplest possible version that provides value:** Manual context gathering + basic "what's next" recommendation.

---

## Phase 1: Foundation (Current Focus)

### Step 1: Context System Foundation

**Goal:** Create a simple context gathering and storage system.

**Tasks:**
1. Create `simple_agent/context/` directory structure:
   - `manager.py` - Context manager for storing/retrieving context
   - `sources/` - Directory for integration modules
   - `schema.py` - Data models for context entries

2. Implement basic context storage:
   - JSON file storage at `~/.simple-agent/context.json`
   - Context entry model: `{id, type, source, content, timestamp, metadata}`
   - Methods: `add_context()`, `get_context()`, `clear_context()`
   - Auto-cleanup: Remove entries older than 7 days
   - Persists across sessions for multi-day context building

3. Add file context gathering (leverage existing tools):
   - Recent files read/written become context automatically
   - Store file paths and summaries in context

**Success Criteria:**
- Can add context entries
- Can retrieve all context
- File operations automatically contribute to context

**Files to Create:**
- `/simple_agent/context/__init__.py`
- `/simple_agent/context/manager.py`
- `/simple_agent/context/schema.py`
- `/simple_agent/context/sources/__init__.py`

### Step 2: Manual Context Input

**Goal:** Allow user to manually add context via commands.

**Tasks:**
1. Add new slash command: `/context <text>`
   - Adds user-provided context to context manager
   - Example: `/context working on webhook retry system`
   - Example: `/context sprint ends Friday`

2. Add context display command: `/show-context`
   - Pretty-prints current context
   - Shows type, source, timestamp for each entry

3. Add clear context command: `/clear-context`
   - Resets context store
   - Useful for switching projects/focus areas

**Success Criteria:**
- User can add arbitrary context
- User can view all stored context
- User can clear context when needed

**Files to Modify:**
- `/simple_agent/cli/prompt.py` - Add command handlers

### Step 3: "What's Next" Tool

**Goal:** Create a tool that uses context to recommend next actions.

**Tasks:**
1. Create new tool: `recommend_next_action`
   - Tool in `/simple_agent/tools/planning/recommend_next.py`
   - Inputs: None (uses context manager)
   - Outputs: Structured recommendation with reasoning

2. Enhance system prompt:
   - Update agent prompt to understand its role as execution assistant
   - Include context awareness instructions
   - Add recommendation formatting guidelines

3. Agent integration:
   - When user asks "what should I work on?" or similar
   - Agent calls `recommend_next_action` tool
   - Tool gathers all context and formats for LLM
   - LLM provides recommendation with reasoning

**Success Criteria:**
- User asks "what should I work on next?"
- Agent responds with prioritized recommendation
- Recommendation references available context
- Reasoning is clear and actionable

**Files to Create:**
- `/simple_agent/tools/planning/__init__.py`
- `/simple_agent/tools/planning/recommend_next.py`

**Files to Modify:**
- `/simple_agent/core/agent.py` - Update system prompt
- `/simple_agent/tools/registry.py` - Register new tool

### Step 4: First External Integration (Calendar)

**Goal:** Add one real external context source to prove the pattern.

**Tasks:**
1. Choose calendar integration (Google Calendar or macOS Calendar)
   - Start with simplest: macOS Calendar via command-line
   - Alternative: Google Calendar API (more setup but more common)

2. Create calendar context source:
   - Module: `/simple_agent/context/sources/calendar.py`
   - Function: `fetch_calendar_context()` returns upcoming events
   - Format: Next 3 events with time, title, duration

3. Add calendar sync command: `/sync-calendar`
   - Fetches calendar data
   - Adds to context manager
   - Shows what was added

4. Enhance recommendations with time awareness:
   - Include time blocks in recommendation logic
   - Suggest tasks that fit available time
   - Flag upcoming meetings

**Success Criteria:**
- User runs `/sync-calendar`
- Context includes next 3 calendar events
- "What's next" recommendations consider time availability
- Agent suggests tasks that fit before next meeting

**Files to Create:**
- `/simple_agent/context/sources/calendar.py`

**Files to Modify:**
- `/simple_agent/cli/prompt.py` - Add `/sync-calendar` command

---

## Phase 2: Multi-Source Intelligence (Future)

**Next additions after Phase 1 is working:**

1. **Jira Integration**
   - Fetch assigned tickets
   - Include sprint information
   - Priority and status awareness

2. **Linear Integration**
   - Similar to Jira
   - Fetch issues, projects, cycles

3. **Git Context**
   - Recent commits
   - Open PRs
   - Branch status

4. **Automatic Context Refresh**
   - Background context updates
   - Configurable sync intervals
   - Smart caching

---

## Phase 3: Long-term Goals (Future)

**After daily efficiency is solid:**

1. **Goal Definition**
   - Add `/set-goal` command
   - Goal storage (JSON file)
   - Goal categories

2. **Progress Tracking**
   - Milestone definitions
   - Progress calculation
   - Status reporting

3. **Proactive Suggestions**
   - Detect goal-related opportunities
   - Nudge on stalled goals
   - Celebrate progress

---

## Implementation Order

### Week 1: Core Context System
- [ ] Step 1: Context system foundation
- [ ] Step 2: Manual context input
- [ ] Test: Can add/view/clear context manually

### Week 2: First Recommendations
- [ ] Step 3: "What's next" tool
- [ ] Test: Get recommendations from manual context
- [ ] Validate: Is this actually useful?

### Week 3: First Integration
- [ ] Step 4: Calendar integration
- [ ] Test: Time-aware recommendations
- [ ] Validate: Does calendar context improve recommendations?

### Week 4+: Iterate
- Assess value and usage
- Decide on next integration (Jira vs Linear vs Git)
- Consider automatic refresh vs manual sync
- Plan Phase 2 based on learnings

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
- **No API servers**: Direct integration calls
- **No background processes**: Manual sync commands only
- **Minimal config**: Reuse existing `~/.simple-agent/` directory

### Make It Easy to Extend

- **Source pattern**: Each integration is a module in `context/sources/`
- **Registry pattern**: Context sources register like tools
- **Typed schemas**: Use Pydantic for all context data
- **Test each source**: Unit tests for each integration

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

After Phase 1, we should be able to:

1. **Add context from multiple sources:**
   ```
   > /context working on API refactor PR #234
   > /sync-calendar
   > what should I work on next?
   ```

2. **Get intelligent recommendations:**
   ```
   Agent: "You have 90 minutes before your 2pm standup.

   Recommendation: Complete API refactor PR #234 review.

   Reasoning:
   - You mentioned working on this (context)
   - Reviews typically take 45-60 minutes
   - Fits comfortably in your available time
   - Keeps momentum on current focus area

   After standup, you'll have 3 hours before your next meeting
   for deeper work."
   ```

3. **Still use file/command tools:**
   ```
   > read the API refactor PR diff
   > edit src/api/routes.py and add rate limiting
   ```

The assistant becomes context-aware and proactive while maintaining all existing capabilities.

---

## Next Actions

1. Review this plan
2. Confirm Phase 1 approach
3. Begin Step 1: Context system foundation
4. Iterate based on feedback
