"""Context Window Array Architecture.

Provides addressable context management for separating working and
implementation LLMs.
"""

from context_window_array.exceptions import ContextCompressedError, ContextWindowArrayError
from context_window_array.models import ContextEntry, EntryType

__all__ = [
    "ContextEntry",
    "EntryType",
    "ContextCompressedError",
    "ContextWindowArrayError",
]
