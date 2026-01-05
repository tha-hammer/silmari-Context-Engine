"""Custom exceptions for context window array module."""


class ContextWindowArrayError(Exception):
    """Base exception for context window array module."""

    pass


class ContextCompressedError(ContextWindowArrayError):
    """Raised when attempting to access content of a compressed entry."""

    def __init__(self, entry_id: str):
        self.entry_id = entry_id
        super().__init__(f"Entry {entry_id} is compressed; content is not available")
