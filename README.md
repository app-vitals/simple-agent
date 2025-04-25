# Simple Agent

[![CI](https://github.com/app-vitals/simple-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/app-vitals/simple-agent/actions/workflows/ci.yml)

A CLI AI agent built on Unix philosophies that provides AI assistance through a natural command-line interface.

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

- Natural AI-first interaction - just type your request
- Enhanced interactive CLI with prompt_toolkit
  - Command completion with Tab
  - Multi-line input support with backslash continuation
  - History navigation with arrow keys
  - Syntax highlighting and styled output
- Slash commands for system operations (`/help`, `/exit`, `/clear`)
- Command execution and file operations with user confirmation
- Stateful conversation context management
- Tool-based interface with explicit permission model
- Claude API integration via LiteLLM

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

```bash
# Configure environment variables
cp .env.example .env

# Edit .env with your API key
nano .env
```

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

```
> Tell me about the Unix philosophy
The Unix philosophy is a set of design principles that emphasizes building simple, 
modular programs that do one thing well and work together through standard interfaces.

> Write a function that calculates fibonacci numbers \
  recursively in Python
[Function definition with docstring and implementation]

> /help
[Shows command help and usage information]

> /clear
[Clears the terminal screen]

> /exit
[Exits the agent]
```

Try pressing Tab to complete commands and use Up/Down arrows to navigate through command history.
