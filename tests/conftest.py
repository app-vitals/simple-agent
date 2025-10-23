"""Pytest configuration and fixtures."""

import os

# Disable MCP servers during tests to speed up test execution
os.environ["SIMPLE_AGENT_DISABLE_MCP"] = "true"
