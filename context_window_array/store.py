"""Central context store for managing addressable context entries."""

from typing import Optional
from context_window_array.models import ContextEntry, EntryType


class CentralContextStore:
    """Addressable context store with CRUD operations.

    Stores context entries by ID and provides operations for
    adding, retrieving, removing, and querying entries.

    Attributes:
        entries: Dictionary mapping entry IDs to ContextEntry objects
    """

    def __init__(self):
        """Initialize empty context store."""
        self._entries: dict[str, ContextEntry] = {}

    def add(self, entry: ContextEntry) -> str:
        """Add an entry to the store.

        Args:
            entry: ContextEntry to add

        Returns:
            The entry's ID

        Raises:
            ValueError: If an entry with the same ID already exists
        """
        if entry.id in self._entries:
            raise ValueError(f"Entry with id '{entry.id}' already exists")
        self._entries[entry.id] = entry
        return entry.id

    def get(self, entry_id: str) -> Optional[ContextEntry]:
        """Get an entry by ID.

        Args:
            entry_id: ID of entry to retrieve

        Returns:
            ContextEntry if found, None otherwise
        """
        return self._entries.get(entry_id)

    def contains(self, entry_id: str) -> bool:
        """Check if store contains an entry with the given ID.

        Args:
            entry_id: ID to check

        Returns:
            True if entry exists, False otherwise
        """
        return entry_id in self._entries

    def get_all(self) -> list[ContextEntry]:
        """Get all entries in the store.

        Returns:
            List of all ContextEntry objects
        """
        return list(self._entries.values())

    def get_by_type(self, entry_type: EntryType) -> list[ContextEntry]:
        """Get all entries of a specific type.

        Args:
            entry_type: EntryType to filter by

        Returns:
            List of entries matching the type
        """
        return [e for e in self._entries.values() if e.entry_type == entry_type]

    def __len__(self) -> int:
        """Return the number of entries in the store."""
        return len(self._entries)
