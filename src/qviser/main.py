import logging

from dhanhq import DhanContext, dhanhq

from qviser.config import get_settings, setup_logging

logger = logging.getLogger(__name__)


def main():
    settings = get_settings()
    setup_logging(settings.log_level)

    context = DhanContext(settings.dhan_client_id, settings.dhan_access_token)
    dhan = dhanhq(context)
    funds = dhan.get_fund_limits()
    logger.info("Funds: %s", funds)


if __name__ == "__main__":
    main()
