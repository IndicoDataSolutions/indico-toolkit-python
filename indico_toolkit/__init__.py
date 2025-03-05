"""A package to support Indico IPA development"""

from .client import create_client
from .errors import (
    ToolkitAuthError,
    ToolkitError,
    ToolkitInputError,
    ToolkitInstantiationError,
    ToolkitPopulationError,
    ToolkitStaggeredLoopError,
    ToolkitStatusError,
)

__all__ = (
    "create_client",
    "ToolkitAuthError",
    "ToolkitError",
    "ToolkitInputError",
    "ToolkitInstantiationError",
    "ToolkitPopulationError",
    "ToolkitStaggeredLoopError",
    "ToolkitStatusError",
)
__version__ = "6.14.0"
