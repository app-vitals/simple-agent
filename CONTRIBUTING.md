# Contributing to Simple Agent

## Setup

```bash
# Clone and install
git clone https://github.com/app-vitals/simple-agent.git
cd simple-agent
pip install uv
uv pip install -e .[dev]

# Set API key for testing
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Code Guidelines

- Use type annotations
- Follow PEP 8 and Unix philosophy
- Keep modules focused and small
- Maintain 90%+ test coverage

## Workflow

1. Create a feature branch
2. Write tests for new functionality
3. Run `./lint.sh` and `./test.sh`
4. Submit a PR with a clear description

## Project Structure

- `simple_agent/core/` - Agent loop and utilities
- `simple_agent/llm/` - LLM integration
- `simple_agent/tools/` - Command and file tools
- `tests/` - Test files

By contributing, you agree your code will be licensed under the project's license.
