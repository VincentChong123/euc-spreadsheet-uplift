"""Current date/time tool — local, no network, no key.

Removes the LLM's dependency on guessing "today" from training data.

Timezone resolution, in order:
  1. Explicit IANA name from the prompt  (e.g. "Asia/Tokyo")
  2. A bare city/country alias the LLM often passes ("Tokyo", "London")
  3. The deployment default (``settings.default_timezone``, Singapore)
The returned ``timezone`` field always states which zone was actually used, so
the model and the audit trail can confirm the request was honoured.
"""

import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic_ai import Agent

from app.config import settings

logger = logging.getLogger(__name__)

# LLMs frequently pass a bare city/country instead of the IANA name. Map the
# common ones; anything unmapped still gets tried verbatim against zoneinfo.
_ALIASES = {
    "singapore": "Asia/Singapore",
    "tokyo": "Asia/Tokyo",
    "japan": "Asia/Tokyo",
    "hong kong": "Asia/Hong_Kong",
    "shanghai": "Asia/Shanghai",
    "china": "Asia/Shanghai",
    "kuala lumpur": "Asia/Kuala_Lumpur",
    "malaysia": "Asia/Kuala_Lumpur",
    "jakarta": "Asia/Jakarta",
    "bangkok": "Asia/Bangkok",
    "mumbai": "Asia/Kolkata",
    "india": "Asia/Kolkata",
    "dubai": "Asia/Dubai",
    "london": "Europe/London",
    "uk": "Europe/London",
    "paris": "Europe/Paris",
    "frankfurt": "Europe/Berlin",
    "new york": "America/New_York",
    "nyc": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "san francisco": "America/Los_Angeles",
    "sydney": "Australia/Sydney",
    "utc": "UTC",
    "gmt": "UTC",
}


def _resolve_zone(timezone: Optional[str]) -> tuple[ZoneInfo, str]:
    """Resolve a user-supplied timezone/city to a ZoneInfo + its IANA name.

    Falls back to the deployment default when nothing usable is given.
    """
    default = settings.default_timezone
    if not timezone or not timezone.strip():
        return ZoneInfo(default), default

    candidate = _ALIASES.get(timezone.strip().lower(), timezone.strip())
    try:
        return ZoneInfo(candidate), candidate
    except (ZoneInfoNotFoundError, ValueError):
        logger.warning("Unknown timezone %r — falling back to %s", timezone, default)
        return ZoneInfo(default), default


def fetch_current_datetime(timezone: Optional[str] = None) -> dict:
    tz, tz_name = _resolve_zone(timezone)
    now = datetime.now(tz)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "iso": now.isoformat(),
        "weekday": now.strftime("%A"),
        "timezone": tz_name,
    }


def register(agent: Agent) -> None:
    @agent.tool_plain
    async def current_datetime(timezone: Optional[str] = None) -> dict:
        """Get the current date and time. Use this whenever the task depends on
        "today", "now", the current year, or the day of the week — never guess
        the date yourself.

        Args:
            timezone: The location to report time for. Pass an IANA name
                      ("Asia/Tokyo", "Europe/London", "UTC") when the user names
                      a city or country. Leave empty for the user's local time
                      (Singapore). The response's "timezone" field confirms which
                      zone was used.
        """
        return fetch_current_datetime(timezone=timezone)
