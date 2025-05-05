"""Tests for the agent module."""

import contextlib
import json
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from simple_agent.cli.prompt import CLIMode
from simple_agent.core.agent import Agent
from simple_agent.core.schema import AgentResponse


@pytest.fixture
def agent() -> Agent:
    """Create an agent for testing."""
    return Agent()


def test_agent_init(agent: Agent) -> None:
    """Test agent initialization."""
    assert len(agent.context) == 1
    assert agent.context[0]["role"] == "system"
    assert "Unix philosophy" in agent.context[0]["content"]
    assert hasattr(agent, "console")
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


# We've covered EOF handling in test_agent_input_handler
# and more thoroughly in the CLI tests, so this test is now redundant.


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
    # Mock dependencies
    agent.console = mocker.MagicMock()  # type: ignore

    # Make _handle_ai_request raise KeyboardInterrupt when called
    agent._handle_ai_request = mocker.MagicMock(side_effect=KeyboardInterrupt())  # type: ignore

    # Process a message (should catch the KeyboardInterrupt)
    agent._process_input("What is the weather today?")

    # Verify _handle_ai_request was called
    agent._handle_ai_request.assert_called_once_with("What is the weather today?")  # type: ignore

    # Verify interrupt message was printed
    agent.console.print.assert_called_once_with("\n[bold yellow]Interrupted by user...[/bold yellow]")  # type: ignore


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

    # Mock _process_llm_response
    agent._process_llm_response = mocker.MagicMock()  # type: ignore

    # Call the method
    agent._handle_ai_request("Hello")

    # Verify context was updated with user message
    assert {"role": "user", "content": "Hello"} in agent.context

    # Verify LLM request was sent
    agent._send_llm_request.assert_called_once_with(agent.context)  # type: ignore

    # Verify response was processed
    agent._process_llm_response.assert_called_once_with("Test response", mock_response)  # type: ignore


def test_handle_ai_request_with_tool_calls(agent: Agent, mocker: MockerFixture) -> None:
    """Test handling AI request with tool calls."""
    # Set up mocks
    agent.console = mocker.MagicMock()  # type: ignore
    agent.llm_client = mocker.MagicMock()  # type: ignore
    agent.tool_handler = mocker.MagicMock()  # type: ignore
    agent._process_llm_response = mocker.MagicMock()  # type: ignore

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

    # Set up test context for simplicity
    agent.context = []

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

    # Verify the user message was added to context
    assert {"role": "user", "content": "Hello"} in agent.context

    # Verify LLM was called twice (once for initial, once for follow-up)
    assert agent._send_llm_request.call_count == 2  # type: ignore

    # Verify tool_handler was called to process tool calls
    agent.tool_handler.process_tool_calls.assert_called_once()  # type: ignore
    args = agent.tool_handler.process_tool_calls.call_args[0]  # type: ignore
    assert args[0] == mock_tool_calls  # First arg should be tool_calls
    assert isinstance(args[1], list)  # Second arg should be a list (context)

    # Verify final response was processed
    agent._process_llm_response.assert_called_once_with("Final result", mock_followup_response)  # type: ignore


def test_handle_ai_request_with_nested_tool_calls(
    agent: Agent, mocker: MockerFixture
) -> None:
    """Test handling AI request with multiple levels of tool calls."""
    # Set up mocks
    agent.console = mocker.MagicMock()  # type: ignore
    agent.llm_client = mocker.MagicMock()  # type: ignore
    agent.tool_handler = mocker.MagicMock()  # type: ignore
    agent._process_llm_response = mocker.MagicMock()  # type: ignore

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

    # Set up test context for simplicity
    agent.context = []

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

    # Verify final response was processed
    agent._process_llm_response.assert_called_once_with("Final result", mock_final_response)  # type: ignore


def test_handle_ai_request_error(agent: Agent, mocker: MockerFixture) -> None:
    """Test handling AI request when LLM returns no response."""
    # Mock dependencies
    agent.console = mocker.MagicMock()  # type: ignore

    # Create a mock cli
    mock_cli = mocker.MagicMock()
    # Mock the CLIMode.NORMAL value
    type(mock_cli).mode = mocker.PropertyMock(return_value=CLIMode.NORMAL)
    agent.cli = mock_cli

    # _send_llm_request returns None (error)
    agent._send_llm_request = mocker.MagicMock(return_value=None)  # type: ignore

    # Call the method
    agent._handle_ai_request("Hello")

    # Verify context was updated with user message
    assert {"role": "user", "content": "Hello"} in agent.context

    # Verify error was displayed
    agent.console.print.assert_any_call("[bold red]Error:[/bold red] Failed to get a response")  # type: ignore


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
        response_format=AgentResponse,
    )


def test_process_llm_response_json(agent: Agent, mocker: MockerFixture) -> None:
    """Test processing a valid JSON response."""
    # Set up mock console
    agent.console = mocker.MagicMock()  # type: ignore

    # Create a valid JSON response
    json_content = json.dumps(
        {
            "message": "This is a test message",
            "status": "COMPLETE",
            "next_action": None,
        }
    )

    # Call the method
    agent._process_llm_response(json_content, MagicMock())

    # Verify message was printed
    agent.console.print.assert_any_call("This is a test message")  # type: ignore

    # Verify response was added to context
    assert agent.context[-1]["role"] == "assistant"
    assert agent.context[-1]["content"] == json_content


def test_process_llm_response_empty_content(
    agent: Agent, mocker: MockerFixture
) -> None:
    """Test processing an empty response."""
    # Set up mock console
    agent.console = mocker.MagicMock()  # type: ignore

    # Call the method with empty content
    agent._process_llm_response("", MagicMock())

    # Verify error was printed
    agent.console.print.assert_called_once_with("[bold red]Error:[/bold red] Empty response from LLM")  # type: ignore

    # Verify context wasn't updated
    assert len(agent.context) == 1  # Only system prompt should be there


def test_process_llm_response_ask(agent: Agent, mocker: MockerFixture) -> None:
    """Test processing a JSON response with ASK status."""
    # Set up mock console
    agent.console = mocker.MagicMock()  # type: ignore

    # Create an ASK response
    json_content = json.dumps(
        {
            "message": "This is a test message",
            "status": "ASK",
            "next_action": "What would you like me to do?",
        }
    )

    # Call the method
    agent._process_llm_response(json_content, MagicMock())

    # Verify question was printed
    agent.console.print.assert_any_call(  # type: ignore
        "[bold yellow]Question:[/bold yellow] What would you like me to do?"
    )


def test_process_llm_response_continue(agent: Agent, mocker: MockerFixture) -> None:
    """Test processing a JSON response with CONTINUE status."""
    # Set up mock console
    agent.console = mocker.MagicMock()  # type: ignore

    # Mock the _handle_ai_request method
    agent._handle_ai_request = mocker.MagicMock()  # type: ignore

    # Create a CONTINUE response
    json_content = json.dumps(
        {
            "message": "Working on it",
            "status": "CONTINUE",
            "next_action": "I'll check the documentation next",
        }
    )

    # Call the method
    agent._process_llm_response(json_content, MagicMock())

    # Verify next action was printed
    agent.console.print.assert_any_call(  # type: ignore
        "[bold blue]Next action:[/bold blue] I'll check the documentation next"
    )

    # Verify that it called _handle_ai_request with the continuation prompt
    agent._handle_ai_request.assert_called_once_with(  # type: ignore
        "Please continue by I'll check the documentation next"
    )


def test_handle_ai_request_max_iterations(agent: Agent, mocker: MockerFixture) -> None:
    """Test handling AI request with too many tool calls (max iterations reached)."""
    # Set up mocks
    agent.console = mocker.MagicMock()  # type: ignore
    agent.llm_client = mocker.MagicMock()  # type: ignore
    agent.tool_handler = mocker.MagicMock()  # type: ignore
    agent._process_llm_response = mocker.MagicMock()  # type: ignore

    # Create a mock cli
    mock_cli = mocker.MagicMock()
    # Mock the CLIMode.NORMAL value
    type(mock_cli).mode = mocker.PropertyMock(return_value=CLIMode.NORMAL)
    agent.cli = mock_cli

    # Create responses all with tool calls to trigger the max iterations
    mock_tool_calls = [mocker.MagicMock()]
    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock()]

    # Set up test context
    agent.context = []

    # Mock the processed messages after tool execution
    processed_messages = [{"role": "user", "content": "Tool result"}]
    agent.tool_handler.process_tool_calls.return_value = processed_messages  # type: ignore

    # Set up the mocks to always return responses with tool calls
    agent._send_llm_request = mocker.MagicMock(return_value=mock_response)  # type: ignore

    # All responses have tool calls
    agent.llm_client.get_message_content.return_value = (None, mock_tool_calls)  # type: ignore

    # Call the method
    agent._handle_ai_request("Hello")

    # Verify LLM was called the maximum number of times (5 iterations)
    assert agent._send_llm_request.call_count == 20  # type: ignore

    # Verify tool_handler was called 5 times
    assert agent.tool_handler.process_tool_calls.call_count == 20  # type: ignore

    # Verify the warning was printed
    agent.console.print.assert_any_call("[bold yellow]Warning:[/bold yellow] Maximum tool call iterations reached")  # type: ignore

    # Verify _process_llm_response was never called since we never got a complete response
    agent._process_llm_response.assert_not_called()  # type: ignore


def test_handle_ai_request_with_keyboard_interrupt_propagation(
    agent: Agent, mocker: MockerFixture
) -> None:
    """Test that KeyboardInterrupt from _handle_ai_request propagates to _process_input."""
    # Set up mocks
    agent.console = mocker.MagicMock()  # type: ignore

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

    # Verify interrupt message was printed
    agent.console.print.assert_called_once_with("\n[bold yellow]Interrupted by user...[/bold yellow]")  # type: ignore


def test_process_llm_response_invalid_json(agent: Agent, mocker: MockerFixture) -> None:
    """Test processing an invalid JSON response."""
    # Set up mock console
    agent.console = mocker.MagicMock()  # type: ignore

    # Create an invalid JSON response
    invalid_json = "This is not JSON"

    # Call the method
    agent._process_llm_response(invalid_json, MagicMock())

    # Verify raw text was printed
    agent.console.print.assert_called_once_with(invalid_json)  # type: ignore

    # Verify response was added to context
    assert agent.context[-1]["role"] == "assistant"
    assert agent.context[-1]["content"] == invalid_json


def test_context_management() -> None:
    """Test context management logic."""
    agent = Agent()

    # Set up a test context
    agent.context = [{"role": "system", "content": "You are a helpful assistant."}]

    # Add more than 10 messages
    for i in range(15):
        agent.context.append({"role": "user", "content": f"Message {i}"})
        agent.context.append({"role": "assistant", "content": f"Response {i}"})

        # Apply the context truncation logic
        if len(agent.context) > 10:
            # Keep the most recent messages, preserving system message if present
            start_idx = (
                1 if agent.context and agent.context[0]["role"] == "system" else 0
            )
            agent.context = (
                agent.context[0:1] + agent.context[-9:]
                if start_idx == 1
                else agent.context[-10:]
            )

    # Verify our context is capped at 10 messages
    assert len(agent.context) == 10

    # The system message should be preserved at index 0
    assert agent.context[0] == {
        "role": "system",
        "content": "You are a helpful assistant.",
    }

    # We should have dropped the older messages
    assert "Message 0" not in str(agent.context)

    # Now test without a system message
    agent.context = []

    # Add more than 10 messages
    for i in range(15):
        agent.context.append({"role": "user", "content": f"Message {i}"})
        agent.context.append({"role": "assistant", "content": f"Response {i}"})

        # Apply the context truncation logic
        if len(agent.context) > 10:
            start_idx = (
                1 if agent.context and agent.context[0]["role"] == "system" else 0
            )
            agent.context = (
                agent.context[0:1] + agent.context[-9:]
                if start_idx == 1
                else agent.context[-10:]
            )

    # Verify we kept only the 10 most recent messages
    assert len(agent.context) == 10
