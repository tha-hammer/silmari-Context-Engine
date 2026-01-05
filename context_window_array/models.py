"""Core data models for context window array architecture.

This module provides dataclasses and enums for representing context entries
in an addressable array structure.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


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
