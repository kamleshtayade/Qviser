import logging

from dhanhq import DhanContext, dhanhq

from qviser.config import get_settings, setup_logging
from qviser.ledger import fetch_recent_ledger, log_ledger
from qviser.portfolio import fetch_holdings, group_holdings_by_exchange, log_holdings_by_exchange
from qviser.token_manager import ensure_fresh_token

logger = logging.getLogger(__name__)


def main():
    settings = get_settings()
    setup_logging(settings.log_level)

    access_token = ensure_fresh_token(settings)
    context = DhanContext(settings.dhan_client_id, access_token)
    dhan = dhanhq(context)

    # Get fund limits
    funds = dhan.get_fund_limits()
    logger.info("Funds: %s", funds)

    # Get holdings, categorised by exchange
    holdings = fetch_holdings(dhan)
    log_holdings_by_exchange(group_holdings_by_exchange(holdings))

    # Get ledger report for the last 30 days
    log_ledger(fetch_recent_ledger(dhan, days=30))

if __name__ == "__main__":
    main()
