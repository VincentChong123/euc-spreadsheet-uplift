"""Tool registry — registers all agent tools onto a pydantic-ai Agent.

To add a new tool:
  1. Create tools/<name>.py with a ``register(agent, **kwargs)`` function.
  2. Add a call to it below. simple_agent.py never changes.
"""

from pydantic_ai import Agent

from app.agents.tools import datetime_now, hdb_resale, mas_forex, weather
from app.config import settings


def register_all(agent: Agent) -> None:
    datetime_now.register(agent)
    weather.register(agent)
    hdb_resale.register(agent)
    mas_forex.register(agent, api_key=settings.mas_forex_eod_api_key)
