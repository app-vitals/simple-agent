"""Tests for MCP server manager."""

import pytest

from simple_agent.config import MCPServerConfig
from simple_agent.tools.mcp.manager import MCPServerManager


@pytest.fixture
def server_config() -> dict[str, MCPServerConfig]:
    """Create test server configuration."""
    return {
        "test_server": MCPServerConfig(
            command="test-command", args=["--test"], env={"TEST_VAR": "value"}
        )
    }


@pytest.fixture
def manager(server_config: dict[str, MCPServerConfig]) -> MCPServerManager:
    """Create an MCP server manager with test config."""
    return MCPServerManager(server_config)


def test_manager_initialization(
    server_config: dict[str, MCPServerConfig],
) -> None:
    """Test manager initializes correctly."""
    manager = MCPServerManager(server_config)

    assert manager.servers_config == server_config
    assert len(manager.sessions) == 0
    assert manager._loop is not None
    assert manager._loop_thread is not None
    assert manager._loop_thread.is_alive()


def test_run_coroutine_threadsafe(manager: MCPServerManager) -> None:
    """Test running coroutine in background event loop."""

    async def test_coro() -> str:
        return "test_result"

    result = manager._run_coroutine_threadsafe(test_coro())
    assert result == "test_result"


def test_start_server_sync_invalid_server(manager: MCPServerManager) -> None:
    """Test starting a server that doesn't exist in config."""
    with pytest.raises(KeyError, match="not found in configuration"):
        manager.start_server_sync("nonexistent_server")


def test_list_tools_sync_server_not_running(manager: MCPServerManager) -> None:
    """Test listing tools from a server that isn't running."""
    with pytest.raises(KeyError, match="is not running"):
        manager.list_tools_sync("test_server")


def test_call_tool_sync_server_not_running(manager: MCPServerManager) -> None:
    """Test calling a tool on a server that isn't running."""
    with pytest.raises(KeyError, match="is not running"):
        manager.call_tool_sync("test_server", "test_tool", {})


def test_shutdown_all_sync(manager: MCPServerManager) -> None:
    """Test shutting down all servers."""
    # Should not raise any errors even with no running servers
    manager.shutdown_all_sync()

    # Verify loop is stopped
    assert manager._loop is not None
    assert not manager._loop.is_running()


def test_shutdown_all_sync_no_loop() -> None:
    """Test shutdown with no event loop."""
    manager = MCPServerManager({})
    manager._loop = None

    # Should not raise any errors
    manager.shutdown_all_sync()
