"""Ledger report helpers built on top of the Dhan API (GET /v2/ledger)."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from dhanhq import dhanhq

logger = logging.getLogger(__name__)

# Dhan returns voucher dates like "Oct 16, 2026".
VOUCHER_DATE_FORMAT = "%b %d, %Y"

# Summary rows Dhan mixes into the ledger; they are balances, not transactions.
OPENING_BALANCE = "OPENING BALANCE"
CLOSING_BALANCE = "CLOSING BALANCE"


@dataclass(frozen=True)
class LedgerEntry:
    voucher_date: date
    voucher_number: str
    description: str
    narration: str
    exchange: str
    debit: Decimal
    credit: Decimal
    running_balance: Decimal

    @classmethod
    def from_api(cls, raw: dict) -> "LedgerEntry":
        return cls(
            voucher_date=datetime.strptime(raw["voucherdate"], VOUCHER_DATE_FORMAT).date(),
            voucher_number=raw.get("vouchernumber", ""),
            description=raw.get("voucherdesc", ""),
            narration=raw.get("narration", ""),
            exchange=raw.get("exchange", ""),
            debit=_to_decimal(raw.get("debit")),
            credit=_to_decimal(raw.get("credit")),
            running_balance=_to_decimal(raw.get("runbal")),
        )

    @property
    def is_balance_row(self) -> bool:
        return self.description.strip().upper() in (OPENING_BALANCE, CLOSING_BALANCE)


def _to_decimal(value: str | None) -> Decimal:
    # Amounts arrive as strings, sometimes with thousands separators.
    return Decimal(str(value or "0").replace(",", ""))


def fetch_ledger(dhan: dhanhq, from_date: date, to_date: date) -> list[LedgerEntry]:
    """Return ledger entries between from_date and to_date (inclusive)."""
    response = dhan.ledger_report(from_date.isoformat(), to_date.isoformat())
    if response.get("status") != "success":
        raise RuntimeError(f"Failed to fetch ledger: {response.get('remarks')}")
    return [LedgerEntry.from_api(raw) for raw in response.get("data") or []]


def fetch_recent_ledger(dhan: dhanhq, days: int = 30) -> list[LedgerEntry]:
    """Return ledger entries for the last `days` days up to today."""
    today = date.today()
    return fetch_ledger(dhan, today - timedelta(days=days), today)


def _balance(entries: list[LedgerEntry], label: str) -> Decimal | None:
    for e in entries:
        if e.description.strip().upper() == label:
            # Dhan reports the balance amount in the credit/debit column.
            return e.credit - e.debit
    return None


def log_ledger(entries: list[LedgerEntry]) -> None:
    transactions = sorted(
        (e for e in entries if not e.is_balance_row), key=lambda e: e.voucher_date
    )
    if not transactions:
        logger.info("No ledger transactions in this period")
        return
    for e in transactions:
        logger.info(
            "%s %-30s debit=%10s credit=%10s balance=%10s",
            e.voucher_date.isoformat(),
            e.description[:30],
            e.debit,
            e.credit,
            e.running_balance,
        )
    total_debit = sum((e.debit for e in transactions), Decimal("0"))
    total_credit = sum((e.credit for e in transactions), Decimal("0"))
    logger.info(
        "Ledger: %d transactions, total debit=%s, total credit=%s, net=%s",
        len(transactions),
        total_debit,
        total_credit,
        total_credit - total_debit,
    )
    logger.info(
        "Opening balance=%s, closing balance=%s",
        _balance(entries, OPENING_BALANCE),
        _balance(entries, CLOSING_BALANCE),
    )
