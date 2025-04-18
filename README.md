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
- Slash commands for system operations (`/help`, `/exit`)
- Command execution and file operations when needed
- Stateful conversation context management
- Claude API integration via LiteLLM

## Development

This project uses [uv](https://github.com/astral-sh/uv) for package management.

```bash
# Install dependencies
uv add <package-name>

# Run code quality tools
./lint.sh  # Black, Ruff, MyPy
./test.sh  # Pytest with 90% coverage requirement
```

Continuous integration runs on all PRs and pushes to main.

## Usage

```bash
# Install
git clone https://github.com/app-vitals/simple-agent.git
cd simple-agent
uv venv
uv pip install -e .

# Configure environment variables
cp .env.example .env
# Edit .env with your API key
nano .env

# Run
python -m simple_agent
```

Example interaction:
```
> Tell me about the Unix philosophy
[Processing...]
The Unix philosophy is a set of design principles...

> /help
[Shows help information]

> /exit
[Exits the agent]
```
