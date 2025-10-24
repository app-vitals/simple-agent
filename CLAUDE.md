# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Simple Agent is an **execution efficiency assistant** that helps users optimize daily task execution through context-aware AI guidance. It's a CLI tool built on Unix philosophy principles that answers "what should I work on next?" based on structured, human-readable context built through interactive compression workflows and external integrations.

**Key Innovation**: Interactive compression workflow that converts rich conversations into structured markdown context files while maintaining token efficiency (3-4x reduction).

### Vision & Roadmap

- **vision.md**: Describes the execution efficiency assistant with compression-first context approach, daily execution, and long-term goal tracking
- **plan.md**: Implementation roadmap focused on Phase 1 (context representation & compression), Phase 2 (context intelligence), Phase 3 (goal tracking)

## Development Commands

### Running Tests
```bash
./test.sh              # Run all tests with 85% coverage requirement
uv run pytest          # Run tests without coverage enforcement
uv run pytest tests/context/test_manager.py  # Run specific test file
uv run pytest -k test_function_name          # Run specific test by name
```

### Code Quality
```bash
./lint.sh              # Run black (formatter), ruff (linter), and mypy (type checker)
uv run black .         # Format code only
uv run ruff check .    # Lint only
uv run mypy simple_agent/ tests/  # Type check only
```

### Running the Agent
```bash
simple-agent           # After installation
python -m simple_agent # Direct module execution
```

## Architecture Overview

### Core System Flow

1. **CLI (cli/prompt.py)** - User input via prompt_toolkit, handles slash commands
2. **Agent (core/agent.py)** - Main loop that:
   - Loads context from `context/*.md` files at startup
   - Builds dynamic system prompt with injected context
   - Sends messages to LLM with tool descriptions
   - Processes tool calls through ToolHandler
   - Handles `/compress` command for interactive context updates
3. **Tool Handler (core/tool_handler.py)** - Manages tool execution with user confirmation
4. **LLM Client (llm/client.py)** - Claude API integration via LiteLLM

### Context System (Key Innovation)

The context system uses **interactive compression** to build structured, human-readable context:

**File Structure:**
```
~/src/<project>/
├── context/                    # Visible, editable markdown files
│   ├── business.md            # Clients, team, revenue
│   ├── strategy.md            # Positioning, decisions, tradeoffs
│   ├── goals.md               # Hierarchical goals with temporal tracking
│   └── decisions.md           # Key decisions with reasoning
├── context-archive/           # Archived conversation sessions
│   └── 2025-10-23-session.md
└── .simple-agent/
    ├── messages.json          # Current session (cleared after compression)
    └── mcp_servers.json
```

**Compression Workflow (`/compress` command)**:
1. User triggers compression at natural breakpoints (after decisions, end of session)
2. Agent reviews FULL conversation history for narrative and insights
3. Agent uses Read/Edit/Write tools to update context files interactively
4. User approves each change (standard tool confirmation)
5. Session archived to `context-archive/YYYY-MM-DD-topic.md`
6. Messages cleared for fresh start

**Key Benefits:**
- Preserves strategic thinking and relationships (not just atomic facts)
- 3-4x token reduction (5KB context vs 20KB+ messages)
- Human-readable, editable markdown files
- Project-scoped (different context per directory)
- Version-controllable with git

**Context Loading (core/agent.py:_build_system_prompt)**:
- Reads `context/*.md` files at agent startup
- Injects full context into system prompt
- Agent naturally references context in responses
- Will optimize to section-based loading as context grows

### Tool Registry Pattern

Tools are registered globally via `tools/registry.py`:
- Each tool defines: name, function, description, parameters, confirmation requirements
- Tools can have custom confirmation handlers and result formatters
- `get_tool_descriptions()` converts registry to LLM tool calling format
- MCP tools are dynamically registered at startup

### MCP Integration Layer

**Model Context Protocol** enables pluggable external integrations:

1. **MCP Manager (tools/mcp/manager.py)**:
   - Loads config from `.simple-agent/mcp_servers.json`
   - Starts MCP server processes (stdio communication)
   - Manages server lifecycle (async via asyncio)

2. **MCP Adapter (tools/mcp/adapter.py)**:
   - Discovers tools from MCP servers
   - Registers them in tool registry
   - Translates between Simple Agent and MCP tool formats

3. **Configuration (config.py)**:
   - Loads MCP servers from config file
   - Each server has: command, args, env vars
   - Can be disabled via `SIMPLE_AGENT_DISABLE_MCP=true`

### Message Management

**MessageManager (messages/manager.py)**:
- Automatic persistence to `.simple-agent/messages.json`
- Stores up to 50 messages (configurable)
- `build_for_llm()` prepends dynamic system prompt
- Loaded on startup to resume conversations

## Testing Patterns

### Tool Tests
File and command tools have dedicated test modules:
- `tests/tools/files/` - File operation tools
- `tests/tools/exec/` - Command execution tools
- `tests/tools/mcp/` - MCP adapter and manager tests

### MCP Tests
MCP tests are disabled during normal test runs via:
```python
@pytest.fixture(autouse=True)
def disable_mcp():
    os.environ["SIMPLE_AGENT_DISABLE_MCP"] = "true"
```

## Key Implementation Details

### Dynamic System Prompt with Context Loading
The system prompt is rebuilt on **every LLM request** to include context from markdown files:
- `agent.py:_build_system_prompt()` called from `_handle_ai_request()` and `_handle_compression()`
- Includes **today's date** in format "Today's date: YYYY-MM-DD" for temporal awareness
- Uses `context/loader.py:load_context_from_directory()` to read all `context/*.md` files
- Injects full context into system prompt
- As context grows, will optimize to section-based loading

### Compression Workflow
The `/compress` command triggers an interactive workflow:
- Compression prompt built in `context/compression_prompt.py`
- Agent receives **full conversation history** to review
- Agent reviews conversation for insights, decisions, strategic thinking
- Uses Read/Edit/Write tools to update context files
- User confirms each change (standard tool confirmation)
- Archives session to `context-archive/YYYY-MM-DD-topic.md`
- Clears `messages.json` for fresh start via `_handle_compression()` in agent.py
- Achieves 3-4x token reduction

### Tool Confirmation Flow
1. Agent calls tool → ToolHandler checks `requires_confirmation()`
2. If required, calls custom handler or default confirmation prompt
3. User approves/denies in real-time
4. Result added to messages for next LLM turn

### MCP Tool Discovery
MCP tools are discovered at startup:
1. Start each MCP server process
2. Call `tools/list` on the server
3. Register discovered tools in global registry
4. Tools appear alongside native tools to the LLM

## File Locations

**Visible Context Files** (in current working directory):
- `context/` - Structured markdown context files (business.md, strategy.md, goals.md, etc.)
- `context-archive/` - Archived conversation sessions

**Hidden Implementation** (in current working directory):
- `.simple-agent/messages.json` - Current conversation session
- `.simple-agent/mcp_servers.json` - MCP server configuration
- `.simple-agent/mcp-{server-name}.log` - MCP server logs

## Common Patterns

### Adding a New Tool
1. Create tool function in `tools/` directory
2. Import and call `register()` in tool's `__init__.py`
3. Specify parameters, description, confirmation requirements
4. Write tests in `tests/tools/`

### Compressing a Session

User triggers compression at natural breakpoints:
```bash
/compress                           # Standard compression
/compress focus on business goals   # With specific instructions
```

Agent workflow:
1. Reviews full conversation history
2. Uses Read tool to load existing context files
3. Uses Edit tool to update sections (user confirms each)
4. Uses Write tool to archive session
5. Clears messages for fresh start

### Adding New Context Files

Context files are just markdown - create them as needed:
- `context/technical.md` - Technical decisions, architecture
- `context/people.md` - Key relationships, collaborators
- `context/ideas.md` - Unorganized ideas, brainstorming

Agent will discover and read any `.md` files in `context/` directory.

### Goals with Temporal Tracking

Include progress tracking in `context/goals.md`:
```markdown
## Mid-term (6 months)
- [ ] Launch product v2.0 by Q1 2026
  - Started: September 2025
  - Deadline: March 2026
  - Elapsed: 2 months / 6 months (33%)
  - Progress: 4/10 features complete (40%)
  - Remaining: 6 features in 4 months
```

Agent updates during compression based on conversation.

## Code Guidelines

- Maintain 85%+ test coverage (enforced by CI)
- Use type annotations throughout
- Follow Unix philosophy: simple, modular, focused components
- Pydantic models for all data schemas
- Auto-save on state changes (messages, context)
