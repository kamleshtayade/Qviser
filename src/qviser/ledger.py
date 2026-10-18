"""Ledger report helpers built on top of the Dhan API (GET /v2/ledger)."""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from dhanhq import dhanhq
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

# Dhan returns voucher dates like "Oct 16, 2026".
VOUCHER_DATE_FORMAT = "%b %d, %Y"

# Summary rows Dhan mixes into the ledger; they are balances, not transactions.
OPENING_BALANCE = "OPENING BALANCE"
CLOSING_BALANCE = "CLOSING BALANCE"


class LedgerEntry(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    voucher_date: date = Field(alias="voucherdate")
    voucher_number: str = Field(default="", alias="vouchernumber")
    description: str = Field(default="", alias="voucherdesc")
    narration: str = ""
    exchange: str = ""
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    running_balance: Decimal = Field(default=Decimal("0"), alias="runbal")

    @field_validator("voucher_date", mode="before")
    @classmethod
    def _parse_voucher_date(cls, value: object) -> object:
        if isinstance(value, str):
            return datetime.strptime(value, VOUCHER_DATE_FORMAT).date()
        return value

    @field_validator("debit", "credit", "running_balance", mode="before")
    @classmethod
    def _parse_amount(cls, value: object) -> object:
        # Amounts arrive as strings, sometimes empty or with thousands separators.
        if value is None or value == "":
            return Decimal("0")
        if isinstance(value, str):
            return value.replace(",", "")
        return value

    @property
    def is_balance_row(self) -> bool:
        return self.description.strip().upper() in (OPENING_BALANCE, CLOSING_BALANCE)


def fetch_ledger(dhan: dhanhq, from_date: date, to_date: date) -> list[LedgerEntry]:
    """Return ledger entries between from_date and to_date (inclusive)."""
    response = dhan.ledger_report(from_date.isoformat(), to_date.isoformat())
    if response.get("status") != "success":
        raise RuntimeError(f"Failed to fetch ledger: {response.get('remarks')}")
    return [LedgerEntry.model_validate(raw) for raw in response.get("data") or []]


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
