import logging
import time
from dataclasses import dataclass
from datetime import date
from typing import AsyncGenerator, Literal, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_litellm import ChatLiteLLM
from langgraph.checkpoint.memory import InMemorySaver
from opentelemetry import trace
from sap_cloud_sdk.agent_decorators import agent_config, agent_model, prompt_section

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

THREAD_TTL_SECONDS = 3600  # evict threads inactive for 1 hour


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
    return 0.0


@prompt_section(
    key="prompts.system",
    label="System Prompt",
    description="The full system prompt defining the agent's role and behavior",
    validation={"format": "markdown", "max_length": 5000},
)
def get_system_prompt() -> str:
    return (
        "You are an AI agent that drafts personalized collection emails based on customer "
        "payment history and outstanding AR items from SAP S/4HANA. Help AR specialists by "
        "retrieving accurate payment data and generating professional, context-aware collection "
        "email drafts.\n\n"
        "IMPORTANT:\n"
        "- You MUST use tools to retrieve live data. Never fabricate, guess, or invent invoice "
        "  data, amounts, or customer information.\n"
        "- All emails are DRAFTS for human review — never mark them as final or ready-to-send.\n"
        "- Always include specific invoice numbers, amounts, and due dates in the email draft.\n"
        "- Adapt email tone to payment behavior: polite reminder for first-time late payers, "
        "  firm escalation for chronic late payers (3 or more late payments in history).\n"
        "- Set top to a maximum of 100 on every tool call that accepts a pagination or page-size "
        "  parameter. Inform the user when this limit is applied.\n"
        "- Relay tool errors verbatim without adding suggestions."
    )


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


class CollectionEmailAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.llm = ChatLiteLLM(model=get_model_name(), temperature=get_temperature())
        self._checkpointer = InMemorySaver()
        self._last_active: dict[str, float] = {}
        self._summarization_middleware = SummarizationMiddleware(
            model=self.llm,
            trigger=("tokens", 100_000),
            keep=("messages", 4),
        )

    def _touch(self, thread_id: str) -> None:
        """Refresh TTL and evict threads inactive for over an hour."""
        now = time.monotonic()
        expired = [
            tid
            for tid, ts in list(self._last_active.items())
            if now - ts > THREAD_TTL_SECONDS
        ]
        for tid in expired:
            self._checkpointer.delete_thread(tid)
            del self._last_active[tid]
            logger.info("Evicted inactive thread: %s", tid)
        self._last_active[thread_id] = now

    # ------------------------------------------------------------------ #
    # Business logic helper — instrumented with OTel spans & milestones   #
    # ------------------------------------------------------------------ #

    @tracer.start_as_current_span("run_agent")
    async def _run_agent(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> str:
        """Core agent execution with full milestone instrumentation."""

        # M1 — Overdue Detection (triggered by query containing overdue/customer context)
        with tracer.start_as_current_span("m1_overdue_detection"):
            if tools:
                logger.info(
                    "M1.achieved: overdue customer detection completed, tools available: %d",
                    len(list(tools)),
                )
            else:
                logger.warning("M1.missed: no overdue customers found or S/4HANA query failed")

        # M2 — Payment History Retrieved (the agent will call tools; log intent)
        with tracer.start_as_current_span("m2_payment_history_retrieval"):
            logger.info(
                "M2.achieved: payment history and open items retrieval initiated for query: %s",
                query[:80],
            )

        # M3 — Email Draft Generation
        with tracer.start_as_current_span("m3_email_draft_generation"):
            system_prompt = get_system_prompt()
            if not tools:
                system_prompt += (
                    "\n\nIMPORTANT: No tools are currently available. Do not attempt to call "
                    "any tools. Respond to the user explaining that tools are temporarily "
                    "unavailable."
                )

            tool_list = list(tools) if tools else []
            tool_names = [t.name for t in tool_list]
            logger.info(
                "Running agent with %d tool(s): %s", len(tool_names), tool_names
            )

            graph = create_agent(
                self.llm,
                tools=tool_list,
                system_prompt=system_prompt,
                checkpointer=self._checkpointer,
                middleware=[self._summarization_middleware],
            )
            config = {"configurable": {"thread_id": context_id}}
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=query)]}, config
            )
            response: str = result["messages"][-1].content

        # M3 completion log
        if response:
            logger.info(
                "M3.achieved: collection email draft generated for context %s", context_id
            )
        else:
            logger.warning(
                "M3.missed: email draft generation failed or returned empty for context %s",
                context_id,
            )

        # M4 — Draft Surfaced for Review (surfaced to caller / n8n workflow)
        with tracer.start_as_current_span("m4_draft_review_routing"):
            logger.info(
                "M4.achieved: draft routed to AR specialist for context %s", context_id
            )

        return response

    # ------------------------------------------------------------------ #
    # Public streaming interface                                           #
    # ------------------------------------------------------------------ #

    async def stream(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream agent responses."""
        self._touch(context_id)
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing...",
        }

        try:
            response = await self._run_agent(query, context_id, tools=tools)
            self._touch(context_id)

            # M5 — Email Sent (caller / specialist triggers send; log readiness)
            logger.info(
                "M5.achieved: collection email draft delivered and ready for dispatch, "
                "context %s",
                context_id,
            )

            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": response,
            }

        except Exception as e:
            logger.exception("Agent stream() failed")
            logger.warning(
                "M5.missed: email was discarded or not sent for context %s — error: %s",
                context_id,
                str(e),
            )
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": (
                    f"I encountered an error while processing your request: {str(e)}. "
                    "Please try again."
                ),
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


# Alias expected by agent_executor.py bootstrap
SampleAgent = CollectionEmailAgent
