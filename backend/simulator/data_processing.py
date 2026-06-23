"""Backwards-compatible facade for simulator business logic.

Implementation lives in ``simulator.processing.*``. Import from here or from
the subpackage — both expose the same public names used by views and reports.
"""

from .processing import *  # noqa: F403
from .processing import __all__  # noqa: F401
