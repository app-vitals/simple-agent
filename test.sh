#!/bin/bash
# test.sh - Script for running tests with coverage enforcement

set -e  # Exit on any error

# Print with color for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Minimum required coverage percentage
MIN_COVERAGE=90

echo -e "${YELLOW}=== Running tests with coverage (minimum ${MIN_COVERAGE}%) ===${NC}"

# Run pytest with coverage
if uv run pytest --cov-fail-under=$MIN_COVERAGE; then
    echo -e "${GREEN}✅ Tests passed with sufficient coverage!${NC}"
else
    echo -e "${RED}❌ Tests failed or coverage requirement not met!${NC}"
    exit 1
fi