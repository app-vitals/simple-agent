# Simple Agent

[![CI](https://github.com/app-vitals/simple-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/app-vitals/simple-agent/actions/workflows/ci.yml)

An **execution efficiency assistant** that helps you optimize daily task execution through context-aware AI guidance. Built on Unix philosophy principles with a clean command-line interface.

Ask "what should I work on next?" and get intelligent recommendations based on your current work context, time tracking, task boards, and calendar.

## Guiding Principles

This project follows Unix philosophy principles:

- **Do one thing well** - AI assistance through a clean CLI interface
- **Programs that work together** - Integration with standard Unix tools
- **Modularity** - Simple, well-defined components
- **Simplicity** - Minimal design, avoid complexity
- **Plain text** - Text-based interface for everything

Additional agent interaction principles:
- **Focused scope** - One task at a time
- **Ask, don't guess** - Clarify intent through questions
- **Less is more** - Concise, relevant responses

## Features

### Core Capabilities
- **Context-Aware Assistance** - Automatically remembers your work context (files, tasks, time tracking)
- **Intelligent Recommendations** - Ask "what should I work on next?" for prioritization help
- **Natural Interaction** - Just type your request in plain language
- **File Operations** - Read, write, and edit files with AI assistance
- **Command Execution** - Run shell commands with confirmation

### Context & Integrations
- **Automatic Context Extraction** - Learns from your interactions to build context
- **MCP Integration Support** - Connect to external services via Model Context Protocol
  - Time tracking services
  - Task management tools
  - Calendar applications
  - Issue trackers
  - Any MCP-compatible service

### Interactive CLI
- Command completion with Tab
- Multi-line input support with backslash continuation
- History navigation with arrow keys
- Syntax highlighting and styled output
- Slash commands: `/help`, `/exit`, `/clear`, `/show-context`, `/clear-context`

### Technical
- Claude API integration via LiteLLM
- Stateful conversation management
- Tool-based architecture with explicit permissions
- 88%+ test coverage

## Development

This project uses [uv](https://github.com/astral-sh/uv) for package management and [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for the interactive CLI.

```bash
# Install dependencies
uv add <package-name>

# Run code quality tools
./lint.sh  # Black, Ruff, MyPy
./test.sh  # Pytest with 90% coverage requirement
```

Continuous integration runs on all PRs and pushes to main.

## Installation

### Option 1: Using pip (Recommended)

```bash
# Install directly from the repository
pip install git+https://github.com/app-vitals/simple-agent.git

# Or install in development mode from a local clone
git clone https://github.com/app-vitals/simple-agent.git
cd simple-agent
pip install -e .
```

### Option 2: Using uv

```bash
# Clone the repository
git clone https://github.com/app-vitals/simple-agent.git
cd simple-agent

# Set up a virtual environment and install
uv venv
uv pip install -e .
```

## Configuration

### Basic Configuration

```bash
# Configure environment variables
cp .env.example .env

# Edit .env with your API key
nano .env
```

### MCP Server Configuration (Optional)

To enable integrations with external services via Model Context Protocol:

```bash
# Create MCP server configuration
nano ~/.simple-agent/mcp_servers.json
```

Example configuration:

```json
{
  "server-name": {
    "command": "mcp-server-command",
    "env": {
      "API_KEY": "your_api_key_here"
    }
  }
}
```

Simple Agent can integrate with any MCP-compatible server for time tracking, task management, calendars, issue trackers, and more. See [vision.md](vision.md) for details.

## Running Simple Agent

Once installed, you can run Simple Agent from anywhere:

```bash
# Run the agent
simple-agent
```

Alternatively, you can run the module directly:

```bash
python -m simple_agent
```

## Example Interactions

### Execution Efficiency

```
> what should I work on next?

Based on your context:
- You have 90 minutes before your next meeting
- Currently working on API refactor (context from recent files)
- Sprint ends in 2 days with 3 tickets remaining
- One urgent task flagged in your task management system

Recommendation: Focus on ticket ENG-456 (auth bug - high priority)

Reasoning:
- Sprint deadline approaching
- Task fits your available time block
- Unblocks other team members
```

### File Operations & Code Assistance

```
> Read src/main.py and suggest improvements

[Analyzes file and provides recommendations]

> Write a function that calculates fibonacci numbers recursively

[Provides implementation with docstring]
```

### Context Management

```
> /show-context
[Displays recent work context and integrations]

> /clear-context
[Clears stored context]

> /help
[Shows all available commands]
```

Press Tab for command completion and use arrow keys for history navigation.
