#!/bin/bash
# lint.sh - Simple linting script for code quality

set -e  # Exit on error

# Print with color for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Running formatter (black) ===${NC}"
uv run black .

echo -e "${YELLOW}=== Running linter (ruff) ===${NC}"
uv run ruff check --fix .

echo -e "${YELLOW}=== Running type checker (mypy) ===${NC}"
uv run mypy simple_agent/

echo -e "${GREEN}✅ All linters passed!${NC}"