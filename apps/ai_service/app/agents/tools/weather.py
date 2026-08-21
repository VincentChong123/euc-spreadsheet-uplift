"""NEA real-time 2-hour weather forecast tool."""

import logging
from typing import Optional

import httpx
from pydantic_ai import Agent

logger = logging.getLogger(__name__)

_BASE_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
_TIMEOUT = 8.0


async def fetch_weather(area: Optional[str] = None) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(_BASE_URL)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("data", {}).get("items", [])
    if not items:
        return {"forecasts": [], "valid_period": "", "area_queried": area or "all"}

    latest = items[0]
    forecasts_raw = latest.get("forecasts", [])
    if area:
        al = area.lower()
        forecasts = [
            {"area": f["area"], "forecast": f["forecast"]}
            for f in forecasts_raw
            if al in f["area"].lower()
        ]
    else:
        forecasts = [{"area": f["area"], "forecast": f["forecast"]} for f in forecasts_raw]

    logger.debug("NEA weather fetched: %d areas, queried=%s", len(forecasts), area)
    return {
        "forecasts": forecasts,
        "valid_period": latest.get("timestamp", ""),
        "area_queried": area or "all",
    }


def register(agent: Agent) -> None:
    @agent.tool_plain
    async def weather(area: Optional[str] = None) -> dict:
        """Get the current 2-hour weather forecast for a Singapore area from NEA.

        Args:
            area: Area name, e.g. "Woodlands", "Tampines", "Jurong West".
                  Leave empty to get all 47 areas.
        """
        return await fetch_weather(area=area)
