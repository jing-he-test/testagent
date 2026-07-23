"""Unit tests for follow-up conversation handling (REQ-02)."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from agent import SampleAgent


@pytest.fixture
def agent():
    return SampleAgent()


@pytest.mark.asyncio
async def test_follow_up_message_handled(agent):
    """Agent should respond to follow-up messages after greeting."""
    mock_result = {"messages": [MagicMock(content="I'm doing great, thanks for asking!")]}

    with patch("agent.create_agent") as mock_create:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = mock_result
        mock_create.return_value = mock_graph

        # Simulate first turn
        agent._conversation_turns["ctx-010"] = 1

        response = await agent.invoke("How are you?", "ctx-010")

    assert response.status == "completed"
    assert len(response.message) > 0


@pytest.mark.asyncio
async def test_multiple_turns_tracked(agent):
    """Multiple conversation turns should be tracked per context."""
    mock_result = {"messages": [MagicMock(content="Sure, happy to chat!")]}

    with patch("agent.create_agent") as mock_create:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = mock_result
        mock_create.return_value = mock_graph

        await agent.invoke("Hello!", "ctx-multi")
        await agent.invoke("How are you?", "ctx-multi")
        await agent.invoke("What's the weather like?", "ctx-multi")

    assert agent._conversation_turns.get("ctx-multi", 0) == 3


@pytest.mark.asyncio
async def test_error_returns_error_response(agent):
    """When an error occurs, agent should return an error response gracefully."""
    with patch("agent.create_agent") as mock_create:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = RuntimeError("LLM unavailable")
        mock_create.return_value = mock_graph

        response = await agent.invoke("Hello!", "ctx-err")

    assert response.status == "completed"
    assert "error" in response.message.lower()
