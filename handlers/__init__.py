"""Task handlers for background worker."""

from .infobit_extraction import handle_infobit_extraction
from .evaluation import handle_evaluation
from .generation import handle_generation
from .requirement_extraction import handle_requirement_extraction

__all__ = [
    "handle_infobit_extraction",
    "handle_evaluation",
    "handle_generation",
    "handle_requirement_extraction"
]
