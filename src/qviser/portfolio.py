"""Portfolio helpers built on top of the Dhan API."""

import logging
from collections import defaultdict
from decimal import Decimal

from dhanhq import dhanhq
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# Dhan reports an empty portfolio as a failure with this error code.
NO_HOLDINGS_ERROR_CODE = "DH-1111"


class Holding(BaseModel):
    # Dhan may send ids as numbers; accept them for the str fields.
    model_config = ConfigDict(frozen=True, populate_by_name=True, coerce_numbers_to_str=True)

    exchange: str = "UNKNOWN"
    trading_symbol: str = Field(default="", alias="tradingSymbol")
    security_id: str = Field(default="", alias="securityId")
    isin: str = ""
    total_qty: int = Field(default=0, alias="totalQty")
    available_qty: int = Field(default=0, alias="availableQty")
    avg_cost_price: Decimal = Field(default=Decimal("0"), alias="avgCostPrice")


def fetch_holdings(dhan: dhanhq) -> list[Holding]:
    """Return all holdings across exchanges; an empty list if there are none."""
    response = dhan.get_holdings()
    if response.get("status") == "success":
        return [Holding.model_validate(raw) for raw in response.get("data") or []]

    remarks = response.get("remarks")
    if isinstance(remarks, dict) and remarks.get("error_code") == NO_HOLDINGS_ERROR_CODE:
        return []
    raise RuntimeError(f"Failed to fetch holdings: {remarks}")


def group_holdings_by_exchange(holdings: list[Holding]) -> dict[str, list[Holding]]:
    """Group holdings by their exchange (e.g. NSE, BSE, ALL)."""
    grouped: dict[str, list[Holding]] = defaultdict(list)
    for holding in holdings:
        grouped[holding.exchange or "UNKNOWN"].append(holding)
    return dict(grouped)


def log_holdings_by_exchange(grouped: dict[str, list[Holding]]) -> None:
    if not grouped:
        logger.info("No holdings available")
        return
    for exchange, holdings in sorted(grouped.items()):
        logger.info("%s: %d holding(s)", exchange, len(holdings))
        for h in holdings:
            logger.info(
                "  %s qty=%s avg_cost=%s", h.trading_symbol, h.total_qty, h.avg_cost_price
            )
