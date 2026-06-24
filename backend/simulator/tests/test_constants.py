"""Regression guards for business constants."""
from simulator.data_processing import UBER_COMMISSION_RATE


def test_uber_commission_rate_is_25_percent():
    """Uber Eats net effective commission (IVA recoverable) must stay at 25%."""
    assert UBER_COMMISSION_RATE == 0.25
