"""Custom exceptions for context window array module."""


class ContextWindowArrayError(Exception):
    """Base exception for context window array module."""

    pass


class ContextCompressedError(ContextWindowArrayError):
    """Raised when attempting to access content of a compressed entry."""

    def __init__(self, entry_id: str):
        self.entry_id = entry_id
        super().__init__(f"Entry {entry_id} is compressed; content is not available")


class EntryBoundsError(ContextWindowArrayError):
    """Raised when entry count exceeds allowed bounds.

    Attributes:
        requested: Number of entries requested
        max_allowed: Maximum entries allowed
    """

    def __init__(self, requested: int, max_allowed: int):
        self.requested = requested
        self.max_allowed = max_allowed
        super().__init__(
            f"Entry count {requested} exceeds maximum allowed {max_allowed}. "
            f"Consider splitting into batches or using skip_validation=True."
        )
