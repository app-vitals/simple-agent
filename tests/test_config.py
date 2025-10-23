"""Tests for configuration module."""

from simple_agent.config import MCPServerConfig


def test_mcp_server_config_defaults() -> None:
    """Test MCPServerConfig with default values."""
    config = MCPServerConfig(command="test-command")

    assert config.command == "test-command"
    assert config.args == []
    assert config.env == {}


def test_mcp_server_config_with_values() -> None:
    """Test MCPServerConfig with custom values."""
    config = MCPServerConfig(
        command="test-command", args=["--arg1", "--arg2"], env={"KEY": "value"}
    )

    assert config.command == "test-command"
    assert config.args == ["--arg1", "--arg2"]
    assert config.env == {"KEY": "value"}
