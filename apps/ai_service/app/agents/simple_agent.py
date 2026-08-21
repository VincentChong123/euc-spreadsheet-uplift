import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.providers.openai import OpenAIProvider

from pydantic_ai import Agent
from app.config import LLM_PROVIDER, LLM_MODEL, LLM_BASE_URL, OPENROUTER_FALLBACK_MODELS, settings
from app.agents.tools import register_all
from app.request_context import current_request_id, next_attempt

_INSTRUCTION_FILE = Path(__file__).parent.parent.parent / "system_instruction.md"
_SYSTEM_INSTRUCTION = _INSTRUCTION_FILE.read_text(encoding="utf-8").strip()

# Talk OpenAI-format to the api_gateway egress route. The gateway injects the
# real provider key; ai_service stays key-less. Provider/model/base_url are all
# resolved in config.py from LLM_PROVIDER (single source of truth).
# Pydantic-AI requires a non-empty api_key even though the gateway handles auth.


async def _propagate_trace_headers(request: httpx.Request) -> None:
    """Stamp the originating Sheet request_id + per-attempt counter on egress.

    Fires once per physical outbound POST — so every 429 retry and FallbackModel
    model-swap re-reads the same context-bound request_id (gateway preserves it
    instead of minting a fresh uuid) while ``x-request-attempt`` increments so
    each attempt stays distinguishable. See app/request_context.py.
    """
    rid = current_request_id()
    if rid:
        request.headers["x-request-id"] = rid
        request.headers["x-request-attempt"] = f"{next_attempt():02d}"


openai_provider = OpenAIProvider(
    base_url=LLM_BASE_URL,
    api_key="dummy_key",
    http_client=httpx.AsyncClient(event_hooks={"request": [_propagate_trace_headers]}),
)


def _make_model(model_name: str) -> OpenAIChatModel:
    return OpenAIChatModel(model_name=model_name, provider=openai_provider)


# Use FallbackModel when on openrouter with no explicit model override — rotates
# through high-confidence tool-calling models: Gemma 4 → Qwen3 → gpt-oss-20b.
# A single explicit LLM_MODEL in .env bypasses the fallback chain.
if LLM_PROVIDER == "openrouter" and not settings.llm_model:
    _models = [_make_model(m) for m in OPENROUTER_FALLBACK_MODELS]
    active_model = FallbackModel(*_models)
    logger.info(
        "OpenRouter fallback chain active: %s",
        " → ".join(OPENROUTER_FALLBACK_MODELS),
    )
else:
    active_model = _make_model(LLM_MODEL)
    logger.info("Single model active: %s", LLM_MODEL)

agent = Agent(
    model=active_model,
    # retries=1 — on 429/5xx pydantic-ai retries the same model before FallbackModel
    # kicks in. Keep low so FallbackModel moves to the next model quickly.
    retries=1,
)

# Emit OpenTelemetry spans for each model request and tool call (e.g.
# mas_forex_rates), nested under the routes.py "AI_Generation_Run" span. Logfire
# exports these to the local Jaeger backend (infrastructure/logfire/docker-compose.yaml).
# `instrument` is a property in pydantic-ai 1.106 — the constructor kwarg is deprecated.
agent.instrument = True

register_all(agent)


async def generate_summary(prompt: str, context: str) -> str:
    """Run the pydantic-ai agent and return a plain-text summary.

    Constructs a single prompt string from the system instruction loaded from
    ``system_instruction.md``, the caller-supplied context, and the task
    prompt, then delegates to the module-level ``agent``. The call is non-streaming — suitable for the
    synchronous Google Sheets response model.

    Args:
        prompt: The user's task instruction (e.g. "Summarise Q3 results").
        context: Supporting text the model may reference (e.g. cell contents).

    Returns:
        Stripped plain-text response from the LLM.

    Raises:
        Exception: Any exception raised by pydantic-ai is propagated to the
            caller; ``routes.py`` catches these and returns
            ``ErrorKey.UPSTREAM_FAILURE``.
    """
    full_prompt = (
        f"{_SYSTEM_INSTRUCTION}\n\n"
        f"Context:\n{context}\n\n"
        f"Task:\n{prompt}\n\n"
        f"Remember to show your Thinking steps before the Summary."
    )

    # Run the agent (Non-streaming, perfect for Sheets!)
    result = await agent.run(full_prompt)

    return result.output.strip()


# # TODO
# # FUTURE V2 ASYNC SCHEMA (Do not use this yet)
# class SheetPromptAsyncRequest(BaseModel):
#     prompt: str
#     context: str = ""
#     target_sheet: str  # e.g., "Ringisho"
#     target_cell: str  # e.g., "G1"
