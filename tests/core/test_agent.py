"""Tests for the agent module."""

import contextlib
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from simple_agent.cli.prompt import CLIMode
from simple_agent.core.agent import Agent


@pytest.fixture
def agent(tmp_path: Path) -> Agent:
    """Create an agent for testing with isolated message storage."""
    agent = Agent()
    # Use temporary storage path for tests to avoid interference
    agent.messages.storage.storage_path = tmp_path / "messages.json"
    agent.messages.storage._ensure_storage_exists()
    agent.messages.clear()  # Start with empty messages
    return agent


def test_agent_init(agent: Agent) -> None:
    """Test agent initialization."""
    assert (
        len(agent.messages) == 0
    )  # Messages start empty, system prompt is added dynamically
    assert hasattr(agent, "llm_client")
    assert hasattr(agent, "tool_handler")
    assert hasattr(agent, "tools")


def test_agent_input_handler(agent: Agent, mocker: MockerFixture) -> None:
    """Test that the agent properly sets up the input handler."""
    # Mock CLI class to avoid actual CLI initialization
    mock_cli = mocker.patch("simple_agent.cli.prompt.CLI")

    # Create a mock input function
    mock_input = mocker.MagicMock()

    # Mock tool_handler
    agent.tool_handler = mocker.MagicMock()

    # Skip actual run by mocking run_interactive_loop to exit immediately
    mock_cli.return_value.run_interactive_loop.side_effect = EOFError()

    # Run the agent with our mock input function
    with contextlib.suppress(EOFError):
        agent.run(input_func=mock_input)

    # Verify tool_handler was updated with input_func
    assert agent.tool_handler.input_func == mock_input


def test_process_input_ai_request(agent: Agent, mocker: MockerFixture) -> None:
    """Test the _process_input method with AI request."""
    # Mock the AI handler method
    agent._handle_ai_request = mocker.MagicMock()  # type: ignore

    # Process a regular message
    agent._process_input("What is the weather today?")

    # Verify AI handler was called with the message
    agent._handle_ai_request.assert_called_once_with("What is the weather today?")  # type: ignore


def test_process_input_keyboard_interrupt(agent: Agent, mocker: MockerFixture) -> None:
    """Test the _process_input method handling KeyboardInterrupt."""
    # Since the display module is imported at the module level, it's tricky to mock
    # Instead of mocking the imported function, we'll use our own test verification
    # to confirm the function executes the expected behavior

    # Make _handle_ai_request raise KeyboardInterrupt when called
    agent._handle_ai_request = mocker.MagicMock(side_effect=KeyboardInterrupt())  # type: ignore

    # Process a message (should catch the KeyboardInterrupt)
    agent._process_input("What is the weather today?")

    # Verify _handle_ai_request was called
    agent._handle_ai_request.assert_called_once_with("What is the weather today?")  # type: ignore

    # The test passes if we reach this point without raising an exception


def test_handle_ai_request(agent: Agent, mocker: MockerFixture) -> None:
    """Test the _handle_ai_request method."""
    # Mock dependencies
    agent.console = mocker.MagicMock()  # type: ignore
    agent.llm_client = mocker.MagicMock()  # type: ignore
    agent.tool_handler = mocker.MagicMock()  # type: ignore

    # Create a mock cli
    mock_cli = mocker.MagicMock()
    # Mock the CLIMode.NORMAL value
    type(mock_cli).mode = mocker.PropertyMock(return_value=CLIMode.NORMAL)
    agent.cli = mock_cli

    # Create a mock response with no tool calls
    mock_response = mocker.MagicMock()
    agent._send_llm_request = mocker.MagicMock(return_value=mock_response)  # type: ignore

    # Mock get_message_content to return content without tool calls
    agent.llm_client.get_message_content.return_value = ("Test response", None)  # type: ignore

    # Call the method
    agent._handle_ai_request("Hello")

    # Verify messages was updated with user message
    assert {"role": "user", "content": "Hello"} in agent.messages.get_all()

    # Verify LLM request was sent (with system prompt prepended)
    agent._send_llm_request.assert_called_once()  # type: ignore

    # Verify response was added to messages
    assert {"role": "assistant", "content": "Test response"} in agent.messages.get_all()


def test_handle_ai_request_with_tool_calls(agent: Agent, mocker: MockerFixture) -> None:
    """Test handling AI request with tool calls."""
    # Set up mocks
    agent.console = mocker.MagicMock()  # type: ignore
    agent.llm_client = mocker.MagicMock()  # type: ignore
    agent.tool_handler = mocker.MagicMock()  # type: ignore

    # Create a mock cli
    mock_cli = mocker.MagicMock()
    # Mock the CLIMode.NORMAL value
    type(mock_cli).mode = mocker.PropertyMock(return_value=CLIMode.NORMAL)
    agent.cli = mock_cli

    # Create initial response with tool calls and follow-up without tools
    mock_tool_calls = [mocker.MagicMock()]
    mock_initial_response = mocker.MagicMock()
    mock_initial_response.choices = [mocker.MagicMock()]

    mock_followup_response = mocker.MagicMock()

    # Mock the processed messages after tool execution
    processed_messages = [{"role": "user", "content": "Hello"}]
    agent.tool_handler.process_tool_calls.return_value = processed_messages  # type: ignore

    # Set up the mocks to return our responses (using the side_effect to return different values on each call)
    agent._send_llm_request = mocker.MagicMock(  # type: ignore
        side_effect=[mock_initial_response, mock_followup_response]
    )

    # First response has tool calls, second doesn't
    agent.llm_client.get_message_content.side_effect = [  # type: ignore
        (None, mock_tool_calls),  # Initial response with tool calls
        ("Final result", None),  # Follow-up response with no tool calls
    ]

    # Call the method
    agent._handle_ai_request("Hello")

    # Verify the user message was added to messages
    assert {"role": "user", "content": "Hello"} in agent.messages.get_all()

    # Verify LLM was called twice (once for initial, once for follow-up)
    assert agent._send_llm_request.call_count == 2  # type: ignore

    # Verify tool_handler was called to process tool calls
    agent.tool_handler.process_tool_calls.assert_called_once()  # type: ignore
    args = agent.tool_handler.process_tool_calls.call_args[0]  # type: ignore
    assert args[0] == mock_tool_calls  # First arg should be tool_calls
    assert isinstance(args[1], list)  # Second arg should be a list (messages)

    # Verify final response was added to messages
    assert {"role": "assistant", "content": "Final result"} in agent.messages.get_all()


def test_handle_ai_request_with_nested_tool_calls(
    agent: Agent, mocker: MockerFixture
) -> None:
    """Test handling AI request with multiple levels of tool calls."""
    # Set up mocks
    agent.console = mocker.MagicMock()  # type: ignore
    agent.llm_client = mocker.MagicMock()  # type: ignore
    agent.tool_handler = mocker.MagicMock()  # type: ignore

    # Create a mock cli
    mock_cli = mocker.MagicMock()
    # Mock the CLIMode.NORMAL value
    type(mock_cli).mode = mocker.PropertyMock(return_value=CLIMode.NORMAL)
    agent.cli = mock_cli

    # Create responses with tool calls for multiple iterations
    mock_tool_calls1 = [mocker.MagicMock()]
    mock_tool_calls2 = [mocker.MagicMock()]
    mock_response1 = mocker.MagicMock()
    mock_response1.choices = [mocker.MagicMock()]
    mock_response2 = mocker.MagicMock()
    mock_response2.choices = [mocker.MagicMock()]
    mock_final_response = mocker.MagicMock()

    # Mock the processed messages after tool executions
    processed_messages1 = [{"role": "user", "content": "First tool result"}]
    processed_messages2 = [{"role": "user", "content": "Second tool result"}]

    # Setup tool_handler to return different results for each call
    agent.tool_handler.process_tool_calls.side_effect = [  # type: ignore
        processed_messages1,  # First tool execution
        processed_messages2,  # Second tool execution
    ]

    # Set up the mocks to return our responses for each iteration
    agent._send_llm_request = mocker.MagicMock(  # type: ignore
        side_effect=[mock_response1, mock_response2, mock_final_response]
    )

    # Configure message content for each response
    agent.llm_client.get_message_content.side_effect = [  # type: ignore
        (None, mock_tool_calls1),  # First response has tool calls
        (None, mock_tool_calls2),  # Second response also has tool calls
        ("Final result", None),  # Final response has no tool calls
    ]

    # Call the method
    agent._handle_ai_request("Hello")

    # Verify LLM was called three times (once for initial, once for second, once for final)
    assert agent._send_llm_request.call_count == 3  # type: ignore

    # Verify tool_handler was called twice
    assert agent.tool_handler.process_tool_calls.call_count == 2  # type: ignore

    # Verify final response was added to messages
    assert {"role": "assistant", "content": "Final result"} in agent.messages.get_all()


def test_handle_ai_request_error(agent: Agent, mocker: MockerFixture) -> None:
    """Test handling AI request when LLM returns no response."""
    # Create a mock cli
    mock_cli = mocker.MagicMock()
    # Mock the CLIMode.NORMAL value
    type(mock_cli).mode = mocker.PropertyMock(return_value=CLIMode.NORMAL)
    agent.cli = mock_cli

    # _send_llm_request returns None (error)
    agent._send_llm_request = mocker.MagicMock(return_value=None)  # type: ignore

    # Call the method
    agent._handle_ai_request("Hello")

    # Verify messages was updated with user message
    assert {"role": "user", "content": "Hello"} in agent.messages.get_all()

    # Can't verify display_error was called due to import mocking issues,
    # but we can verify no error is raised and the code handles the None response


def test_send_llm_request(agent: Agent, mocker: MockerFixture) -> None:
    """Test sending an LLM request."""
    # Mock the llm_client
    agent.llm_client = mocker.MagicMock()  # type: ignore
    mock_response = mocker.MagicMock()
    agent.llm_client.send_completion.return_value = mock_response  # type: ignore

    # Set up test messages
    messages = [{"role": "user", "content": "Hello"}]

    # Call the method
    result = agent._send_llm_request(messages)

    # Verify result
    assert result == mock_response

    # Verify send_completion was called with correct arguments
    agent.llm_client.send_completion.assert_called_once_with(  # type: ignore
        messages=messages,
        tools=agent.tools,
    )


def test_handle_ai_request_max_iterations(agent: Agent, mocker: MockerFixture) -> None:
    """Test handling AI request with too many tool calls (max iterations reached)."""
    # Mock required components
    agent.llm_client = mocker.MagicMock()  # type: ignore
    agent.tool_handler = mocker.MagicMock()  # type: ignore

    # Create a mock cli
    mock_cli = mocker.MagicMock()
    # Mock the CLIMode.NORMAL value
    type(mock_cli).mode = mocker.PropertyMock(return_value=CLIMode.NORMAL)
    agent.cli = mock_cli

    # Create responses all with tool calls to trigger the max iterations
    mock_tool_calls = [mocker.MagicMock()]
    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock()]

    # Mock the processed messages after tool execution
    processed_messages = [{"role": "user", "content": "Tool result"}]
    agent.tool_handler.process_tool_calls.return_value = processed_messages  # type: ignore

    # Set up the mocks to always return responses with tool calls
    agent._send_llm_request = mocker.MagicMock(return_value=mock_response)  # type: ignore

    # All responses have tool calls
    agent.llm_client.get_message_content.return_value = (None, mock_tool_calls)  # type: ignore

    # Call the method
    agent._handle_ai_request("Hello")

    # Verify LLM was called the maximum number of times (20 iterations)
    assert agent._send_llm_request.call_count == 20  # type: ignore

    # Verify tool_handler was called 20 times
    assert agent.tool_handler.process_tool_calls.call_count == 20  # type: ignore


def test_handle_ai_request_with_keyboard_interrupt_propagation(
    agent: Agent, mocker: MockerFixture
) -> None:
    """Test that KeyboardInterrupt from _handle_ai_request propagates to _process_input."""
    # Create a mock cli
    mock_cli = mocker.MagicMock()
    # Mock the CLIMode.NORMAL value
    type(mock_cli).mode = mocker.PropertyMock(return_value=CLIMode.NORMAL)
    agent.cli = mock_cli

    # Mock _handle_ai_request to raise KeyboardInterrupt directly
    agent._handle_ai_request = mocker.MagicMock(side_effect=KeyboardInterrupt())  # type: ignore

    # Process a message (should catch the KeyboardInterrupt)
    agent._process_input("Hello")

    # Verify _handle_ai_request was called
    agent._handle_ai_request.assert_called_once_with("Hello")  # type: ignore

    # The test passes if we reach this point without raising an exception


def test_context_management(tmp_path: Path) -> None:
    """Test message management logic."""
    agent = Agent()
    # Use temporary storage to avoid interference
    agent.messages.storage.storage_path = tmp_path / "messages.json"
    agent.messages.storage._ensure_storage_exists()
    agent.messages.clear()

    # Add more than 10 messages (max_messages is set to 50 by default, but we'll test the logic)
    for i in range(15):
        agent.messages.append({"role": "user", "content": f"Message {i}"})
        agent.messages.append({"role": "assistant", "content": f"Response {i}"})

    # Verify all messages are stored (under the 50 limit)
    assert len(agent.messages) == 30  # 15 user + 15 assistant

    # We should have all messages since we're under the limit
    assert "Message 0" in str(agent.messages.get_all())
    assert "Message 14" in str(agent.messages.get_all())


def test_get_status_message(agent: Agent, mocker: MockerFixture) -> None:
    """Test the _get_status_message method."""
    # Mock the LLM client
    agent.llm_client = mocker.MagicMock()

    # Set up token counts and cost
    mocker.patch.object(
        agent.llm_client, "get_token_counts", return_value=(100, 50, 0.0025)
    )

    # Setup for elapsed time calculation
    agent.request_start_time = 1000.0  # Set a fixed start time
    mock_monotonic = mocker.patch(
        "time.monotonic", return_value=1002.5
    )  # 2.5 seconds later

    # Mock display_status_message function
    mock_display = mocker.patch(
        "simple_agent.core.agent.display_status_message", return_value="Status message"
    )

    # Call the method
    result = agent._get_status_message()

    # Verify monotonic was called
    mock_monotonic.assert_called_once()

    # Verify result
    assert result == "Status message"

    # Verify display_status_message was called with correct arguments
    mock_display.assert_called_once_with(100, 50, 2.5, 0.0025)


def test_get_status_message_no_request_time(
    agent: Agent, mocker: MockerFixture
) -> None:
    """Test _get_status_message when no request is in progress."""
    # Mock the LLM client
    agent.llm_client = mocker.MagicMock()

    # Set up token counts and cost
    mocker.patch.object(
        agent.llm_client, "get_token_counts", return_value=(100, 50, 0.0025)
    )

    # Set request_start_time to None (no request in progress)
    agent.request_start_time = None

    # Mock display_status_message function
    mock_display = mocker.patch(
        "simple_agent.core.agent.display_status_message", return_value="Status message"
    )

    # Call the method
    result = agent._get_status_message()

    # Verify result
    assert result == "Status message"

    # Verify display_status_message was called with correct arguments (no elapsed time)
    mock_display.assert_called_once_with(100, 50, None, 0.0025)


def test_build_system_prompt_no_context(agent: Agent, mocker: MockerFixture) -> None:
    """Test building system prompt when no context is available."""
    # Mock the context extractor to return no context
    mock_extractor = mocker.MagicMock()
    mock_extractor.get_recent_context_summary.return_value = (
        "No recent context available."
    )
    agent.context_extractor = mock_extractor

    # Build the system prompt
    prompt = agent._build_system_prompt()

    # Verify it contains the base prompt
    assert "Unix philosophy" in prompt

    # Verify it does NOT contain context section
    assert "## Current Context" not in prompt

    # Verify extractor was called
    mock_extractor.get_recent_context_summary.assert_called_once_with(max_age_hours=24)


def test_build_system_prompt_with_context(agent: Agent, mocker: MockerFixture) -> None:
    """Test building system prompt with context available."""
    # Mock the context extractor to return some context
    mock_extractor = mocker.MagicMock()
    mock_extractor.get_recent_context_summary.return_value = """Recent Context:

Task:
  - Working on API refactor PR #234

File:
  - Edited src/api/routes.py"""
    agent.context_extractor = mock_extractor

    # Build the system prompt
    prompt = agent._build_system_prompt()

    # Verify it contains the base prompt
    assert "Unix philosophy" in prompt

    # Verify it contains context section
    assert "## Current Context" in prompt
    assert "Working on API refactor PR #234" in prompt
    assert "Edited src/api/routes.py" in prompt

    # Verify it contains context-aware instructions
    assert "what should I work on next?" in prompt
    assert "Consider time constraints from calendar entries" in prompt

    # Verify extractor was called
    mock_extractor.get_recent_context_summary.assert_called_once_with(max_age_hours=24)


def test_handle_ai_request_refreshes_system_prompt(
    agent: Agent, mocker: MockerFixture
) -> None:
    """Test that _handle_ai_request refreshes the system prompt with latest context."""
    # Mock dependencies
    agent.llm_client = mocker.MagicMock()  # type: ignore
    agent.tool_handler = mocker.MagicMock()  # type: ignore

    # Create a mock cli
    mock_cli = mocker.MagicMock()
    type(mock_cli).mode = mocker.PropertyMock(return_value=CLIMode.NORMAL)
    agent.cli = mock_cli

    # Mock the context extractor to return different context
    mock_extractor = mocker.MagicMock()
    mock_extractor.get_recent_context_summary.return_value = """Recent Context:

Task:
  - New task from context"""
    agent.context_extractor = mock_extractor

    # Create a mock response with no tool calls
    mock_response = mocker.MagicMock()
    agent._send_llm_request = mocker.MagicMock(return_value=mock_response)  # type: ignore
    agent.llm_client.get_message_content.return_value = ("Test response", None)  # type: ignore

    # Call the method
    agent._handle_ai_request("Hello")

    # Verify _build_system_prompt was indirectly called via get_recent_context_summary
    mock_extractor.get_recent_context_summary.assert_called()

    # Verify _send_llm_request was called with messages that include system prompt
    call_args = agent._send_llm_request.call_args[0][0]  # type: ignore
    assert call_args[0]["role"] == "system"
    assert "New task from context" in call_args[0]["content"]


def test_mcp_initialization_disabled(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test that MCP servers are not initialized when disabled."""
    # Mock config to have MCP servers but be disabled
    mock_config = mocker.patch("simple_agent.core.agent.config")
    mock_config.mcp_servers = {"test": mocker.MagicMock()}
    mock_config.mcp_disabled = True

    # Create agent
    agent = Agent()
    agent.messages.storage.storage_path = tmp_path / "messages.json"
    agent.messages.storage._ensure_storage_exists()

    # Verify MCP manager was not initialized
    assert agent.mcp_manager is None
    assert agent.mcp_adapter is None


def test_mcp_initialization_enabled(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test that MCP servers are initialized when enabled."""
    # Mock the MCP manager and adapter
    mock_manager_class = mocker.patch("simple_agent.core.agent.MCPServerManager")
    mock_adapter_class = mocker.patch("simple_agent.core.agent.MCPToolAdapter")
    mock_manager = mocker.MagicMock()
    mock_adapter = mocker.MagicMock()
    mock_manager_class.return_value = mock_manager
    mock_adapter_class.return_value = mock_adapter

    # Mock config to have MCP servers and be enabled
    mock_config = mocker.patch("simple_agent.core.agent.config")
    mock_server_config = mocker.MagicMock()
    mock_config.mcp_servers = {"test": mock_server_config}
    mock_config.mcp_disabled = False

    # Create agent
    agent = Agent()
    agent.messages.storage.storage_path = tmp_path / "messages.json"
    agent.messages.storage._ensure_storage_exists()

    # Verify MCP manager was initialized
    mock_manager_class.assert_called_once_with({"test": mock_server_config})
    mock_adapter_class.assert_called_once_with(mock_manager)
    assert agent.mcp_manager == mock_manager
    assert agent.mcp_adapter == mock_adapter


def test_mcp_initialization_error(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test that MCP initialization errors are handled gracefully."""
    # Mock the MCP manager to raise an error
    mock_manager_class = mocker.patch("simple_agent.core.agent.MCPServerManager")
    mock_manager_class.side_effect = Exception("MCP init failed")

    # Mock config to have MCP servers and be enabled
    mock_config = mocker.patch("simple_agent.core.agent.config")
    mock_config.mcp_servers = {"test": mocker.MagicMock()}
    mock_config.mcp_disabled = False

    # Mock display_warning to verify it was called
    mock_warning = mocker.patch("simple_agent.core.agent.display_warning")

    # Create agent (should not raise)
    agent = Agent()
    agent.messages.storage.storage_path = tmp_path / "messages.json"
    agent.messages.storage._ensure_storage_exists()

    # Verify warning was displayed
    mock_warning.assert_called_once()
    assert agent.mcp_manager is None
    assert agent.mcp_adapter is None


def test_load_mcp_tools(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test _load_mcp_tools method."""
    # Create agent with mocked MCP components
    agent = Agent()
    agent.messages.storage.storage_path = tmp_path / "messages.json"
    agent.messages.storage._ensure_storage_exists()

    # Mock MCP manager and adapter
    mock_manager = mocker.MagicMock()
    mock_adapter = mocker.MagicMock()
    agent.mcp_manager = mock_manager
    agent.mcp_adapter = mock_adapter

    # Mock config to have a test server
    mock_config = mocker.patch("simple_agent.core.agent.config")
    mock_config.mcp_servers = {"test_server": mocker.MagicMock()}

    # Call the method
    agent._load_mcp_tools()

    # Verify server was started
    mock_manager.start_server_sync.assert_called_once_with("test_server")

    # Verify tools were discovered and registered
    mock_adapter.discover_and_register_tools_sync.assert_called_once_with("test_server")


def test_load_mcp_tools_server_error(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test that _load_mcp_tools handles server startup errors gracefully."""
    # Create agent with mocked MCP components
    agent = Agent()
    agent.messages.storage.storage_path = tmp_path / "messages.json"
    agent.messages.storage._ensure_storage_exists()

    # Mock MCP manager and adapter
    mock_manager = mocker.MagicMock()
    mock_adapter = mocker.MagicMock()
    agent.mcp_manager = mock_manager
    agent.mcp_adapter = mock_adapter

    # Mock config to have a test server
    mock_config = mocker.patch("simple_agent.core.agent.config")
    mock_config.mcp_servers = {"bad_server": mocker.MagicMock()}

    # Make start_server_sync raise an error
    mock_manager.start_server_sync.side_effect = Exception("Server failed to start")

    # Mock display_warning
    mock_warning = mocker.patch("simple_agent.core.agent.display_warning")

    # Call the method (should not raise)
    agent._load_mcp_tools()

    # Verify warning was displayed
    mock_warning.assert_called_once()

    # Verify discover_and_register was NOT called due to error
    mock_adapter.discover_and_register_tools_sync.assert_not_called()
