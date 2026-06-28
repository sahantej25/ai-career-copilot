"""Request-scoped context for guardrail audit trails (no PII in logs)."""
from contextvars import ContextVar

current_user_id: ContextVar[str | None] = ContextVar("guardrail_user_id", default=None)
current_agent: ContextVar[str | None] = ContextVar("guardrail_agent", default=None)


def set_guardrail_context(*, user_id: str | None = None, agent: str | None = None) -> None:
    if user_id is not None:
        current_user_id.set(user_id)
    if agent is not None:
        current_agent.set(agent)


def clear_guardrail_context() -> None:
    current_user_id.set(None)
    current_agent.set(None)
