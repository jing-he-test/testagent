"""Unit tests for the greeting functionality (REQ-01)."""
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
async def test_first_message_triggers_greeting(agent):
    """Agent should produce a greeting on the first message."""
    mock_result = {"messages": [MagicMock(content="Hello! Welcome! How can I help you today?")]}

    with patch("agent.create_agent") as mock_create:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = mock_result
        mock_create.return_value = mock_graph

        response = await agent.invoke("Hello!", "ctx-001")

    assert response.status == "completed"
    assert len(response.message) > 0


@pytest.mark.asyncio
async def test_stream_yields_processing_then_response(agent):
    """Stream should first yield a processing status then the final response."""
    mock_result = {"messages": [MagicMock(content="Hi there! Great to meet you!")]}

    with patch("agent.create_agent") as mock_create:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = mock_result
        mock_create.return_value = mock_graph

        chunks = []
        async for chunk in agent.stream("Hi!", "ctx-002"):
            chunks.append(chunk)

    assert chunks[0]["is_task_complete"] is False
    assert chunks[0]["content"] == "Processing..."
    assert chunks[-1]["is_task_complete"] is True
    assert len(chunks[-1]["content"]) > 0


@pytest.mark.asyncio
async def test_greeting_increments_turn_counter(agent):
    """Conversation turn counter should increment on each message."""
    mock_result = {"messages": [MagicMock(content="Hello!")]}

    with patch("agent.create_agent") as mock_create:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = mock_result
        mock_create.return_value = mock_graph

        await agent.invoke("Hello!", "ctx-003")

    assert agent._conversation_turns.get("ctx-003", 0) == 1
