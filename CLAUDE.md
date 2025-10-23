# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Simple Agent is an **execution efficiency assistant** that helps users optimize daily task execution through context-aware AI guidance. It's a CLI tool built on Unix philosophy principles that answers "what should I work on next?" based on automatically extracted context from user interactions and external integrations.

### Vision & Roadmap

- **vision.md**: Describes the transformation to an execution efficiency assistant with daily and long-term goal capabilities
- **plan.md**: Implementation roadmap showing Phase 1 (context system, MCP integration) is complete; Phase 2 (context sync) is current focus

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
   - Builds dynamic system prompt with injected context
   - Sends messages to LLM with tool descriptions
   - Processes tool calls through ToolHandler
   - Extracts context after each interaction (background thread)
3. **Tool Handler (core/tool_handler.py)** - Manages tool execution with user confirmation
4. **LLM Client (llm/client.py)** - Claude API integration via LiteLLM

### Context System (Key Innovation)

The context system automatically builds user work context:

1. **Context Extractor (context/extractor.py)**:
   - Runs after each agent interaction in background thread
   - Uses LLM to extract facts from user messages and tool calls
   - Stores facts in ContextManager with appropriate types

2. **Context Manager (context/manager.py)**:
   - Disk-based JSON storage at `.simple-agent/context.json`
   - Auto-cleanup of entries older than 7 days
   - Context types: MANUAL, FILE, CALENDAR, TASK, TIME_TRACKING, GOAL

3. **System Prompt Injection (core/agent.py:_build_system_prompt)**:
   - Dynamically injects recent context (24h) into system prompt
   - Agent naturally references context in responses
   - No explicit tool calls needed for context awareness

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

### Context Extraction Tests
Context extraction uses LLM calls, so tests use `unittest.mock.patch`:
```python
@patch("simple_agent.context.extractor.LLMClient")
def test_extract_context(mock_llm_client):
    # Mock LLM response with tool call containing facts
    # Verify facts stored in context manager
```

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

### Dynamic System Prompt
The system prompt is rebuilt on **every LLM request** to include fresh context. This happens in `agent.py:_build_system_prompt()` called from `_handle_ai_request()`.

### Background Context Extraction
After each interaction, context extraction runs in a daemon thread to avoid blocking the UI. If extraction fails, it shows a warning but doesn't crash.

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

User data stored in `.simple-agent/` (in current working directory):
- `context.json` - Extracted context facts
- `messages.json` - Conversation history
- `mcp_servers.json` - MCP server configuration
- `mcp-{server-name}.log` - MCP server logs

## Common Patterns

### Adding a New Tool
1. Create tool function in `tools/` directory
2. Import and call `register()` in tool's `__init__.py`
3. Specify parameters, description, confirmation requirements
4. Write tests in `tests/tools/`

### Adding Context Sync for New MCP Source
Future work (Phase 2) will add `context/sources/mcp_sync.py` to:
1. Query MCP servers for current state
2. Extract relevant facts (time tracking, tasks, calendar)
3. Store in ContextManager with appropriate types
4. Triggered by `/sync-context` command

### Extending Context Types
Add new types to `context/schema.py:ContextType` enum, then update:
- `extractor.py:_determine_context_type()` - Detection logic
- `extractor.py:get_recent_context_summary()` - Display formatting
- `prompt.py:show_context()` - CLI display

## Code Guidelines

- Maintain 85%+ test coverage (enforced by CI)
- Use type annotations throughout
- Follow Unix philosophy: simple, modular, focused components
- Pydantic models for all data schemas
- Auto-save on state changes (messages, context)
