"""MAS Exchange Rates (End of Period – Daily) tool.

Requires API key passed at registration time from settings.
"""

import json
import logging
from typing import Optional, Union

import httpx
from pydantic_ai import Agent

logger = logging.getLogger(__name__)

_BASE_URL = (
    "https://eservices.mas.gov.sg/apimg-gw/server"
    "/monthly_statistical_bulletin_non610ora"
    "/exchange_rates_end_of_period_daily"
    "/views/exchange_rates_end_of_period_daily"
)
_TIMEOUT = 10.0

_CURRENCY_FIELDS = {
    "USD": "usd_sgd", "EUR": "eur_sgd", "GBP": "gbp_sgd",
    "AUD": "aud_sgd", "CAD": "cad_sgd", "NZD": "nzd_sgd", "CHF": "chf_sgd",
    "JPY": "jpy_sgd_100", "CNY": "cny_sgd_100", "HKD": "hkd_sgd_100",
    "INR": "inr_sgd_100", "IDR": "idr_sgd_100", "KRW": "krw_sgd_100",
    "MYR": "myr_sgd_100", "PHP": "php_sgd_100", "THB": "thb_sgd_100",
    "TWD": "twd_sgd_100", "SAR": "sar_sgd_100", "QAR": "qar_sgd_100",
    "AED": "aed_sgd_100", "VND": "vnd_sgd_100",
}
_PER_100 = {k for k, v in _CURRENCY_FIELDS.items() if v.endswith("_100")}

# Fixed answer template for rate questions. Edit here to change the wording the
# model uses everywhere. Placeholders: {amount} {code} {rate} {date}.
# The tool renders this per currency and returns it as `summary`; the system
# instruction tells the model to reuse these sentences verbatim.
_RATE_SENTENCE = "As of {date}, {amount} {code} = {rate} SGD (MAS interbank mid-rate)."


def _render_sentence(code: str, rate: str, date: Optional[str]) -> str:
    amount = 100 if code in _PER_100 else 1
    return _RATE_SENTENCE.format(amount=amount, code=code, rate=rate, date=date or "the latest date")


async def fetch_mas_forex_rates(
    api_key: str,
    currencies: Optional[Union[list[str], str]] = None,
    date: Optional[str] = None,
    rows: int = 5,
) -> dict:
    # Some models pass list args as a JSON string — coerce to list
    if isinstance(currencies, str):
        try:
            currencies = json.loads(currencies)
        except (ValueError, TypeError):
            currencies = [currencies]
    rows = min(rows, 30)
    params: dict = {"$count": rows, "$orderby": "end_of_day DESC"}
    if date:
        params["end_of_day"] = date

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(_BASE_URL, params=params, headers={"keyid": api_key})
        resp.raise_for_status()
        data = resp.json()

    elements = data.get("elements", [])
    logger.debug(
        "MAS forex raw response: keys=%s, elements=%d, first_record_fields=%s",
        list(data.keys()),
        len(elements),
        list(elements[0].keys()) if elements else [],
    )

    selected = {c.upper() for c in currencies} if currencies else set(_CURRENCY_FIELDS)
    result_rows = []
    matched_any = False
    for rec in elements:
        row: dict = {"date": rec.get("end_of_day")}
        for code in sorted(selected):
            field = _CURRENCY_FIELDS.get(code)
            if field and field in rec:
                row[code] = {
                    "sgd_rate": rec[field],
                    "unit": "per 100 units" if code in _PER_100 else "per unit",
                }
                matched_any = True
        result_rows.append(row)

    if elements and not matched_any:
        # Rows came back but no currency field matched — the API schema likely
        # changed (field names) or the requested codes are unsupported. This is
        # the "placeholder values" symptom seen downstream.
        logger.warning(
            "MAS forex: %d record(s) returned but no currency field matched. "
            "requested=%s known_fields=%s actual_record_fields=%s",
            len(elements), selected, sorted(_CURRENCY_FIELDS.values()),
            list(elements[0].keys()),
        )

    # Pre-rendered sentences for the latest row — the model reuses these verbatim.
    summary = []
    if result_rows:
        latest = result_rows[0]
        latest_date = latest.get("date")
        for code in sorted(selected):
            entry = latest.get(code)
            if entry:
                summary.append(_render_sentence(code, entry["sgd_rate"], latest_date))

    logger.debug("MAS forex fetched: %d rows, currencies=%s", len(result_rows), selected)
    return {
        "summary": summary,
        "rates": result_rows,
        "note": "Rates are average interbank mid-rates from Thomson Reuters via MAS.",
    }


def register(agent: Agent, api_key: str) -> None:
    if not api_key:
        logger.info("MAS_FOREX_EOD_API_KEY not set — mas_forex_rates tool not registered")
        return

    @agent.tool_plain
    async def mas_forex_rates(
        currencies: Optional[Union[list[str], str]] = None,
        date: Optional[str] = None,
        rows: int = 5,
    ) -> dict:
        """Get SGD exchange rates published by MAS.

        Args:
            currencies: List of currency codes, e.g. ["USD", "EUR", "MYR"].
                        Supported: USD EUR GBP AUD CAD NZD CHF JPY CNY HKD INR
                                   IDR KRW MYR PHP THB TWD SAR QAR AED VND.
                        Leave empty to return all currencies.
            date: Filter by date YYYY-MM-DD. Leave empty for latest available.
            rows: Number of daily rows to return (default 5).
        """
        return await fetch_mas_forex_rates(api_key=api_key, currencies=currencies, date=date, rows=rows)
