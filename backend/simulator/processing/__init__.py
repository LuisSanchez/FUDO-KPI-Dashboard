"""
Domain processing layer (SOLID: SRP).

Business logic lives in simulator.data_processing today; this package is the
target home. data_processing re-exports public API for backward compatibility.
New code should import from simulator.processing when modules are fully split.
"""

from simulator.processing.constants import IVA_FACTOR, UBER_COMMISSION_RATE

__all__ = ["UBER_COMMISSION_RATE", "IVA_FACTOR"]
