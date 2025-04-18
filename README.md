# Simple Agent

A CLI AI agent built on Unix philosophies.

## Guiding Principles

This project adheres to a set of core principles inspired by Unix philosophy:

- **Do one thing well** - Focused on providing AI assistance through a clean CLI interface
- **Programs that work together** - Designed to integrate with standard Unix tools and pipes
- **Everything is a file** - Using standard file formats for configuration and data
- **Plain text as interface** - Using readable, text-based inputs and outputs
- **Modularity** - Building from simple, well-defined components
- **Simplicity** - Keeping the design minimal and avoiding unnecessary complexity
- **Transparency** - Making behavior clear and predictable
- **Clarity over cleverness** - Prefer explicit, readable code over clever tricks
- **Solve real problems** - Build tools that address actual needs
- **Optimize for maintainability** - Write code your future self will thank you for
- **Design for extensibility** - Create useful abstractions that enable growth

## Agent Interaction Principles

For effective human-agent interaction, we embrace these additional principles:

- **Focused scope** - Handle one clear task at a time rather than attempting too much
- **Ask, don't guess** - Clarify user intent through questions rather than assumptions
- **Alignment through dialogue** - Maintain shared understanding between user and agent
- **Prefer accuracy over speed** - Get it right the first time to avoid backtracking
- **Explicit over implicit** - Make actions and reasoning transparent to the user
- **Less is more** - Provide concise, relevant responses without unnecessary complexity

## Features

The agent will include the following core features:

### Core Agent Loop
- Interactive command-line dialogue with the user
- Stateful conversation context management
- Structured command parsing with clear help system

### Command Execution
- Run shell commands in a controlled environment
- Capture and format command output
- Handle errors and provide helpful feedback

### File Operations
- Read files with proper error handling
- Write content to files safely
- Create patch-style edits to existing files
- Understand basic file types and formats

### API Integration
- Connect to external AI models (Anthropic Claude)
- Structured data exchange with APIs
- Manage API keys and configuration securely

## Development

This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

### Running Commands

We use the `uv run` approach instead of activating the virtual environment:

```bash
# Run the main application
uv run python main.py

# Install dependencies
uv add <package-name>

# Run tests (when added)
uv run pytest

# List installed packages
uv run pip list
```

This approach is preferred because:
- No need to remember activation/deactivation
- Works consistently in scripts and CI/CD pipelines
- Keeps your shell environment clean
- Requires fewer steps