"""Core data models for context window array architecture.

This module provides dataclasses and enums for representing context entries
in an addressable array structure.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EntryType(Enum):
    """Types of context entries in the store.

    Each type represents a different category of context:
    - FILE: File content from codebase
    - COMMAND: Command invocation (can be removed after execution)
    - COMMAND_RESULT: Result of command execution (retained)
    - TASK: Task description for implementation LLM
    - TASK_RESULT: Result from task execution
    - SEARCH_RESULT: Result from search/grep operations
    - SUMMARY: Compressed summary of other entries
    - CONTEXT_REQUEST: Worker request for additional context
    """

    FILE = "file"
    COMMAND = "command"
    COMMAND_RESULT = "command_result"
    TASK = "task"
    TASK_RESULT = "task_result"
    SEARCH_RESULT = "search_result"
    SUMMARY = "summary"
    CONTEXT_REQUEST = "context_request"

    @classmethod
    def from_string(cls, value: str) -> "EntryType":
        """Convert string to EntryType enum.

        Args:
            value: String representation of entry type

        Returns:
            Corresponding EntryType enum value

        Raises:
            ValueError: If value is not a valid entry type
        """
        for entry_type in cls:
            if entry_type.value == value:
                return entry_type
        valid_types = ", ".join(t.value for t in cls)
        raise ValueError(f"Invalid entry type '{value}'. Must be one of: {valid_types}")

    def __str__(self) -> str:
        return self.value


@dataclass
class ContextEntry:
    """Single addressable entry in the context store.

    Represents a piece of context that can be stored, searched, compressed,
    and referenced by ID. Follows the Context Entry Schema from RLM research.

    Attributes:
        id: Unique identifier (format: ctx_XXX)
        entry_type: Type of context entry
        source: Origin (file path, command, task_id)
        content: Full content (can be None if compressed)
        summary: Compressed summary (always present after creation)
        created_at: Creation timestamp (defaults to now)
        references: List of referenced entry IDs
        searchable: Whether to include in search index
        compressed: True if content has been removed
        ttl: Time-to-live in conversation turns (None = no expiry)
        parent_id: ID of parent entry if derived
        derived_from: List of entry IDs this was derived from

    Example:
        >>> entry = ContextEntry(
        ...     id="ctx_001",
        ...     entry_type=EntryType.FILE,
        ...     source="src/main.py",
        ...     content="def main(): pass",
        ...     summary="Main entry point function",
        ... )
        >>> entry.id
        'ctx_001'
    """

    # Required fields
    id: str
    entry_type: EntryType
    source: str
    content: Optional[str]
    summary: Optional[str]

    # Optional fields with defaults
    created_at: datetime = field(default_factory=datetime.now)
    references: list[str] = field(default_factory=list)
    searchable: bool = True
    compressed: bool = False
    ttl: Optional[int] = None
    parent_id: Optional[str] = None
    derived_from: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate entry after initialization."""
        self._validate_id()
        self._validate_source()
        self._validate_content_or_summary()
        self._validate_ttl()
        self._validate_parent_id()
        self._validate_string_lists()

    def _validate_id(self) -> None:
        """Validate id is non-empty."""
        if not self.id or not self.id.strip():
            raise ValueError("id must not be empty")

    def _validate_source(self) -> None:
        """Validate source is non-empty."""
        if not self.source or not self.source.strip():
            raise ValueError("source must not be empty")

    def _validate_content_or_summary(self) -> None:
        """Validate at least one of content or summary is provided."""
        if self.content is None and self.summary is None:
            raise ValueError("At least one of content or summary must be provided")

    def _validate_ttl(self) -> None:
        """Validate TTL is non-negative if provided."""
        if self.ttl is not None and self.ttl < 0:
            raise ValueError("ttl must be non-negative")

    def _validate_parent_id(self) -> None:
        """Validate parent_id type and normalize empty strings to None."""
        if self.parent_id is not None:
            if not isinstance(self.parent_id, str):
                raise TypeError("parent_id must be a string or None")
            # Normalize empty string to None
            if not self.parent_id.strip():
                object.__setattr__(self, "parent_id", None)

    def _validate_string_lists(self) -> None:
        """Validate references and derived_from are lists of strings."""
        if self.references and not all(isinstance(r, str) for r in self.references):
            raise TypeError("references must be list of strings")
        if self.derived_from and not all(isinstance(d, str) for d in self.derived_from):
            raise TypeError("derived_from must be list of strings")

    def to_dict(self) -> dict[str, Any]:
        """Serialize entry to dictionary.

        Returns:
            Dictionary with all fields, datetime as ISO string, enum as string value.
        """
        return {
            "id": self.id,
            "entry_type": self.entry_type.value,
            "source": self.source,
            "content": self.content,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
            "references": self.references,
            "searchable": self.searchable,
            "compressed": self.compressed,
            "ttl": self.ttl,
            "parent_id": self.parent_id,
            "derived_from": self.derived_from,
        }

    def decrement_ttl(self) -> None:
        """Decrement TTL by 1 if set and positive.

        If TTL is None, does nothing (no expiry).
        If TTL is 0, stays at 0.
        """
        if self.ttl is not None and self.ttl > 0:
            object.__setattr__(self, "ttl", self.ttl - 1)

    def is_expired(self) -> bool:
        """Check if entry has expired based on TTL.

        Returns:
            True if TTL is 0, False if TTL is None or positive.
        """
        return self.ttl == 0

    def has_ttl(self) -> bool:
        """Check if entry has a TTL set.

        Returns:
            True if TTL is not None (even if 0), False otherwise.
        """
        return self.ttl is not None

    def set_ttl(self, ttl: Optional[int]) -> None:
        """Set the TTL value.

        Args:
            ttl: New TTL value (None for no expiry, 0+ for turns until expiry)

        Raises:
            ValueError: If ttl is negative
        """
        if ttl is not None and ttl < 0:
            raise ValueError("ttl must be non-negative")
        object.__setattr__(self, "ttl", ttl)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextEntry":
        """Deserialize entry from dictionary.

        Args:
            data: Dictionary with entry fields

        Returns:
            Reconstructed ContextEntry
        """
        # Parse created_at if present
        created_at = None
        if "created_at" in data and data["created_at"]:
            created_at = datetime.fromisoformat(data["created_at"])

        # Parse entry_type from string
        entry_type = EntryType.from_string(data["entry_type"])

        return cls(
            id=data["id"],
            entry_type=entry_type,
            source=data["source"],
            content=data.get("content"),
            summary=data.get("summary"),
            created_at=created_at if created_at else datetime.now(),
            references=data.get("references", []),
            searchable=data.get("searchable", True),
            compressed=data.get("compressed", False),
            ttl=data.get("ttl"),
            parent_id=data.get("parent_id"),
            derived_from=data.get("derived_from", []),
        )
