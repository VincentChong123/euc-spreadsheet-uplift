"""HDB resale price tool via data.gov.sg legacy CKAN API."""

import json
import logging
from typing import Optional

import httpx
from pydantic_ai import Agent

logger = logging.getLogger(__name__)

_BASE_URL = "https://data.gov.sg/api/action/datastore_search"
_RESOURCE_ID = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
_TIMEOUT = 10.0


async def fetch_hdb_resale_prices(
    town: Optional[str] = None,
    flat_type: Optional[str] = None,
    limit: int = 10,
) -> dict:
    limit = min(limit, 100)
    filters: dict = {}
    if town:
        filters["town"] = town.upper()
    if flat_type:
        filters["flat_type"] = flat_type.upper()

    params: dict = {"resource_id": _RESOURCE_ID, "limit": limit}
    if filters:
        params["filters"] = json.dumps(filters)

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(_BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("success"):
        logger.warning("HDB CKAN API returned success=false: %s", data)
        return {"records": [], "total": 0, "filters_applied": filters}

    result = data.get("result", {})
    records = [
        {
            "month": r.get("month"),
            "town": r.get("town"),
            "flat_type": r.get("flat_type"),
            "storey_range": r.get("storey_range"),
            "floor_area_sqm": r.get("floor_area_sqm"),
            "resale_price": r.get("resale_price"),
        }
        for r in result.get("records", [])
    ]

    logger.debug(
        "HDB resale fetched: %d records (total=%s), filters=%s",
        len(records), result.get("total"), filters,
    )
    return {"records": records, "total": result.get("total", 0), "filters_applied": filters}


def register(agent: Agent) -> None:
    @agent.tool_plain
    async def hdb_resale_prices(
        town: Optional[str] = None,
        flat_type: Optional[str] = None,
        limit: int = 10,
    ) -> dict:
        """Get recent HDB resale flat transaction prices in Singapore.

        Args:
            town: Town name, e.g. "WOODLANDS", "TAMPINES", "ANG MO KIO".
            flat_type: Flat type, e.g. "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE".
            limit: Number of records to return (default 10, max 100).
        """
        return await fetch_hdb_resale_prices(town=town, flat_type=flat_type, limit=limit)
