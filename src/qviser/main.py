import logging

from dhanhq import DhanContext, dhanhq

from qviser.config import get_settings, setup_logging
from qviser.portfolio import fetch_holdings, group_holdings_by_exchange, log_holdings_by_exchange

logger = logging.getLogger(__name__)


def main():
    settings = get_settings()
    setup_logging(settings.log_level)

    context = DhanContext(settings.dhan_client_id, settings.dhan_access_token)
    dhan = dhanhq(context)

    # Get fund limits
    funds = dhan.get_fund_limits()
    logger.info("Funds: %s", funds)

    # Get holdings, categorised by exchange
    holdings = fetch_holdings(dhan)
    log_holdings_by_exchange(group_holdings_by_exchange(holdings))

if __name__ == "__main__":
    main()
