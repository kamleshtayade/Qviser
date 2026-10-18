"""Portfolio helpers built on top of the Dhan API."""

import logging
from collections import defaultdict

from dhanhq import dhanhq

logger = logging.getLogger(__name__)

# Dhan reports an empty portfolio as a failure with this error code.
NO_HOLDINGS_ERROR_CODE = "DH-1111"


def fetch_holdings(dhan: dhanhq) -> list[dict]:
    """Return all holdings across exchanges; an empty list if there are none."""
    response = dhan.get_holdings()
    if response.get("status") == "success":
        return response.get("data") or []

    remarks = response.get("remarks")
    if isinstance(remarks, dict) and remarks.get("error_code") == NO_HOLDINGS_ERROR_CODE:
        return []
    raise RuntimeError(f"Failed to fetch holdings: {remarks}")


def group_holdings_by_exchange(holdings: list[dict]) -> dict[str, list[dict]]:
    """Group holdings by their exchange field (e.g. NSE, BSE, ALL)."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for holding in holdings:
        grouped[holding.get("exchange") or "UNKNOWN"].append(holding)
    return dict(grouped)


def log_holdings_by_exchange(grouped: dict[str, list[dict]]) -> None:
    if not grouped:
        logger.info("No holdings available")
        return
    for exchange, holdings in sorted(grouped.items()):
        logger.info("%s: %d holding(s)", exchange, len(holdings))
        for h in holdings:
            logger.info(
                "  %s qty=%s avg_cost=%s",
                h.get("tradingSymbol"),
                h.get("totalQty"),
                h.get("avgCostPrice"),
            )
