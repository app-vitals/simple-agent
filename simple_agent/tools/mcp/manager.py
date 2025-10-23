"""MCP server manager for handling server lifecycle and communication."""

import asyncio
import contextlib
import threading
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from simple_agent.config import MCPServerConfig


class MCPServerManager:
    """Manages MCP server connections via stdio transport."""

    def __init__(self, servers_config: dict[str, MCPServerConfig]) -> None:
        """Initialize the MCP server manager.

        Args:
            servers_config: Dictionary mapping server names to their configurations
        """
        self.servers_config = servers_config
        self.sessions: dict[str, ClientSession] = {}
        self._server_tasks: dict[str, asyncio.Task[None]] = {}
        self._shutdown_events: dict[str, asyncio.Event] = {}
        self._log_files: dict[str, Any] = {}  # Keep log file handles open

        # Create a dedicated event loop for MCP servers in a background thread
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self._start_event_loop()

    def _start_event_loop(self) -> None:
        """Start a background event loop in a separate thread."""

        def run_loop(loop: asyncio.AbstractEventLoop) -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=run_loop, args=(self._loop,), daemon=True
        )
        self._loop_thread.start()

    def _run_coroutine_threadsafe(self, coro: Any) -> Any:
        """Run a coroutine in the background event loop and wait for result.

        Args:
            coro: Coroutine to run

        Returns:
            Result of the coroutine
        """
        if not self._loop:
            raise RuntimeError("Event loop not started")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    async def _run_server(
        self, server_name: str, server_params: StdioServerParameters, log_file: Any
    ) -> None:
        """Run an MCP server in a background task.

        Args:
            server_name: Name of the server
            server_params: Server parameters for stdio connection
            log_file: File handle for stderr redirection
        """
        shutdown_event = asyncio.Event()
        self._shutdown_events[server_name] = shutdown_event

        # Use errlog parameter to redirect stderr to file
        async with (
            stdio_client(server_params, errlog=log_file) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            self.sessions[server_name] = session

            # Wait for shutdown signal
            await shutdown_event.wait()

            # Cleanup
            if server_name in self.sessions:
                del self.sessions[server_name]

    async def _start_server_async(self, server_name: str) -> None:
        """Async implementation of start_server.

        Args:
            server_name: Name of the server to start
        """
        if server_name not in self.servers_config:
            raise KeyError(f"Server '{server_name}' not found in configuration")

        if server_name in self.sessions:
            return

        config = self.servers_config[server_name]

        # Create log file for this server's stderr
        log_dir = Path.home() / ".simple-agent"
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / f"mcp-{server_name}.log"
        log_file = log_path.open("a")  # noqa: SIM115
        self._log_files[server_name] = log_file

        # Create server parameters
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env if config.env else None,
        )

        # Start server in background task with log file
        task = asyncio.create_task(
            self._run_server(server_name, server_params, log_file)
        )
        self._server_tasks[server_name] = task

        # Wait for session to be initialized
        for _ in range(50):  # Wait up to 5 seconds
            if server_name in self.sessions:
                break
            await asyncio.sleep(0.1)
        else:
            raise TimeoutError(f"Server '{server_name}' failed to start")

    def start_server_sync(self, server_name: str) -> None:
        """Start an MCP server synchronously.

        Args:
            server_name: Name of the server to start
        """
        self._run_coroutine_threadsafe(self._start_server_async(server_name))

    async def _list_tools_async(self, server_name: str) -> list[Any]:
        """Async implementation of list_tools."""
        if server_name not in self.sessions:
            raise KeyError(f"Server '{server_name}' is not running")

        session = self.sessions[server_name]
        result = await session.list_tools()
        return result.tools

    def list_tools_sync(self, server_name: str) -> list[Any]:
        """List all available tools from an MCP server synchronously.

        Args:
            server_name: Name of the server to query

        Returns:
            List of tool definitions from the server
        """
        result: list[Any] = self._run_coroutine_threadsafe(
            self._list_tools_async(server_name)
        )
        return result

    async def _call_tool_async(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """Async implementation of call_tool."""
        if server_name not in self.sessions:
            raise KeyError(f"Server '{server_name}' is not running")

        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        return result.content

    def call_tool_sync(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """Call a tool on an MCP server synchronously.

        Args:
            server_name: Name of the server hosting the tool
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        return self._run_coroutine_threadsafe(
            self._call_tool_async(server_name, tool_name, arguments)
        )

    async def _shutdown_all_async(self) -> None:
        """Async implementation of shutdown_all."""
        # Signal all servers to shutdown
        for event in self._shutdown_events.values():
            event.set()

        # Wait for all tasks to complete with timeout
        if self._server_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        *self._server_tasks.values(), return_exceptions=True
                    ),
                    timeout=5.0,
                )
            except TimeoutError:
                # Cancel tasks that didn't finish
                for task in self._server_tasks.values():
                    task.cancel()

        self.sessions.clear()
        self._server_tasks.clear()
        self._shutdown_events.clear()

    def shutdown_all_sync(self) -> None:
        """Shutdown all running MCP servers synchronously."""
        if not self._loop or not self._loop.is_running():
            return

        # Shutdown all servers
        if self._shutdown_events:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._shutdown_all_async(), self._loop
                )
                # Wait for shutdown to complete with timeout
                future.result(timeout=3.0)
            except Exception:
                # Ignore errors during shutdown
                pass

        # Stop the event loop
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        # Wait for thread to finish
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=2.0)

        # Close all log files
        for log_file in self._log_files.values():
            with contextlib.suppress(Exception):
                log_file.close()
        self._log_files.clear()
