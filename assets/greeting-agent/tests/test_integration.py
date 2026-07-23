"""Integration test: end-to-end agent flow with mocked LLM."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from agent import SampleAgent


@pytest.mark.asyncio
async def test_full_conversation_flow():
    """Full conversation: greet → follow-up → farewell."""
    agent = SampleAgent()

    responses = [
        {"messages": [MagicMock(content="Hello! Nice to meet you! How can I help?")]},
        {"messages": [MagicMock(content="I'm doing great, thank you for asking!")]},
        {"messages": [MagicMock(content="Goodbye! Have a wonderful day!")]},
    ]
    response_iter = iter(responses)

    with patch("agent.create_agent") as mock_create:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = lambda *args, **kwargs: next(response_iter)
        mock_create.return_value = mock_graph

        ctx = "integration-ctx-001"

        # Turn 1: Greeting
        r1 = await agent.invoke("Hello there!", ctx)
        assert r1.status == "completed"
        assert len(r1.message) > 0

        # Turn 2: Follow-up
        r2 = await agent.invoke("How are you?", ctx)
        assert r2.status == "completed"
        assert len(r2.message) > 0

        # Turn 3: Farewell — should clear conversation
        r3 = await agent.invoke("Goodbye!", ctx)
        assert r3.status == "completed"
        assert ctx not in agent._conversation_turns
