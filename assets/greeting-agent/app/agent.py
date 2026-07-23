import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_litellm import ChatLiteLLM
from opentelemetry import trace
from langgraph.checkpoint.memory import MemorySaver
from sap_cloud_sdk.agent_decorators import agent_config, agent_model, prompt_section

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

FAREWELL_KEYWORDS = ["bye", "goodbye", "see you", "farewell", "take care", "good night", "later", "cya"]


@agent_model(
    key="config.model",
    label="LLM Model",
    description="The language model powering this agent",
)
def get_model_name() -> str:
    return "sap/anthropic--claude-4.5-sonnet"


@agent_config(
    key="config.temperature",
    label="LLM Temperature",
    description="Controls randomness of responses (0.0 = deterministic, 1.0 = creative)",
)
def get_temperature() -> float:
    return 0.7


@prompt_section(
    key="prompts.system",
    label="System Prompt",
    description="The full system prompt defining the agent's role and behavior",
    validation={"format": "markdown", "max_length": 5000},
)
def get_system_prompt() -> str:
    return (
        "You are a friendly greeting agent. Your job is to:\n"
        "1. Welcome users warmly when they first say hello.\n"
        "2. Engage in simple, friendly conversation.\n"
        "3. Recognize when a user says goodbye and close the conversation gracefully with a warm farewell.\n\n"
        "IMPORTANT: Never fabricate or invent information. Only handle greetings and basic "
        "conversational messages. If asked about out-of-scope topics, politely redirect the "
        "conversation back to greetings and general pleasantries."
    )


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


def _is_farewell(query: str) -> bool:
    """Check if the user's message contains a farewell intent."""
    lower = query.lower()
    return any(kw in lower for kw in FAREWELL_KEYWORDS)


class SampleAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.llm = ChatLiteLLM(model=get_model_name(), temperature=get_temperature())
        self._checkpointer = MemorySaver()
        self._summarization_middleware = SummarizationMiddleware(
            model=self.llm,
            trigger=("tokens", 100_000),
            keep=("messages", 4),
        )
        self._conversation_turns: dict[str, int] = {}

    async def _run_agent(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> str:
        """Core agent logic with milestone instrumentation."""

        # Determine if this is the first message in the conversation
        turn = self._conversation_turns.get(context_id, 0)
        self._conversation_turns[context_id] = turn + 1

        # M1: User Initiates Conversation
        with tracer.start_as_current_span("greeting-agent.m1.user-initiated"):
            if turn == 0:
                logger.info("M1.achieved: user initiated conversation")
            else:
                logger.debug("M1.achieved: user initiated conversation (follow-up turn %d)", turn + 1)

        system_prompt = get_system_prompt()
        if not tools:
            system_prompt += "\n\nNote: No tools are available. Respond conversationally."

        graph = create_agent(
            self.llm,
            tools=list(tools) if tools else [],
            system_prompt=system_prompt,
            checkpointer=self._checkpointer,
            middleware=[self._summarization_middleware],
        )
        config = {"configurable": {"thread_id": context_id}}
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=query)]}, config
        )
        response = result["messages"][-1].content

        # M2: Agent Greets User (first turn only)
        if turn == 0:
            with tracer.start_as_current_span("greeting-agent.m2.greeting-sent"):
                logger.info("M2.achieved: greeting sent to user")

        # M3: Conversation Continues (follow-up turns)
        if turn > 0 and not _is_farewell(query):
            with tracer.start_as_current_span("greeting-agent.m3.conversation-continued"):
                logger.info("M3.achieved: follow-up conversation handled")

        # M4: Session Ends
        if _is_farewell(query):
            with tracer.start_as_current_span("greeting-agent.m4.session-ended"):
                logger.info("M4.achieved: conversation closed gracefully")
                # Clean up conversation turn counter
                self._conversation_turns.pop(context_id, None)

        return response

    async def stream(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream agent responses."""
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing...",
        }

        try:
            response = await self._run_agent(query, context_id, tools=tools)
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": response,
            }
        except Exception:
            logger.exception("Agent stream() failed")
            logger.warning("M1.missed: no initial message received")
            logger.warning("M2.missed: greeting was not delivered")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": "I encountered an error while processing your request. Please try again.",
            }

    async def invoke(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AgentResponse:
        """Invoke agent and return final response."""
        last: dict = {}
        async for chunk in self.stream(query, context_id, tools=tools):
            last = chunk
        if last.get("is_task_complete"):
            return AgentResponse(status="completed", message=last["content"])
        if last.get("require_user_input"):
            return AgentResponse(status="input_required", message=last["content"])
        return AgentResponse(
            status="error", message=last.get("content", "Unknown error")
        )
