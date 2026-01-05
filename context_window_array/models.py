"""Core data models for context window array architecture.

This module provides dataclasses and enums for representing context entries
in an addressable array structure.
"""

from enum import Enum


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
