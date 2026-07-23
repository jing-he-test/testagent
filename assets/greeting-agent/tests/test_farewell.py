"""Unit tests for farewell/session-close handling (REQ-03)."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from agent import SampleAgent, _is_farewell


@pytest.fixture
def agent():
    return SampleAgent()


def test_is_farewell_detects_bye():
    assert _is_farewell("Bye!") is True


def test_is_farewell_detects_goodbye():
    assert _is_farewell("Goodbye, see you!") is True


def test_is_farewell_detects_see_you():
    assert _is_farewell("See you later") is True


def test_is_farewell_returns_false_for_greeting():
    assert _is_farewell("Hello, how are you?") is False


def test_is_farewell_case_insensitive():
    assert _is_farewell("BYE BYE") is True


@pytest.mark.asyncio
async def test_farewell_clears_turn_counter(agent):
    """Session close (farewell) should clear the conversation turn counter."""
    mock_result = {"messages": [MagicMock(content="Goodbye! Have a great day!")]}

    with patch("agent.create_agent") as mock_create:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = mock_result
        mock_create.return_value = mock_graph

        # Set an existing turn count
        agent._conversation_turns["ctx-bye"] = 3
        await agent.invoke("Goodbye!", "ctx-bye")

    # Turn counter should be cleared after farewell
    assert "ctx-bye" not in agent._conversation_turns


@pytest.mark.asyncio
async def test_farewell_returns_completed_response(agent):
    """Farewell message should produce a completed response."""
    mock_result = {"messages": [MagicMock(content="Take care! Goodbye!")]}

    with patch("agent.create_agent") as mock_create:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = mock_result
        mock_create.return_value = mock_graph

        response = await agent.invoke("Take care, bye!", "ctx-farewell")

    assert response.status == "completed"
    assert len(response.message) > 0
