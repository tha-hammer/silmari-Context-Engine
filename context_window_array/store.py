"""Central context store for managing addressable context entries."""

from typing import Optional, Union
from context_window_array.models import ContextEntry, EntryType
from context_window_array.exceptions import ContextCompressedError


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
        self._id_counter: int = 0

    def _generate_id(self) -> str:
        """Generate a unique entry ID."""
        self._id_counter += 1
        return f"ctx_{self._id_counter:06d}"

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

    def remove(
        self,
        entry_id: str,
        return_entry: bool = False
    ) -> Union[bool, Optional[ContextEntry]]:
        """Remove an entry from the store.

        Args:
            entry_id: ID of entry to remove
            return_entry: If True, return the removed entry instead of bool

        Returns:
            If return_entry=False: True if entry was removed, False if not found
            If return_entry=True: The removed entry, or None if not found
        """
        if entry_id not in self._entries:
            return None if return_entry else False

        entry = self._entries.pop(entry_id)
        return entry if return_entry else True

    def remove_multiple(self, entry_ids: list[str]) -> int:
        """Remove multiple entries from the store.

        Args:
            entry_ids: List of entry IDs to remove

        Returns:
            Number of entries actually removed
        """
        removed = 0
        for entry_id in entry_ids:
            if entry_id in self._entries:
                del self._entries[entry_id]
                removed += 1
        return removed

    def clear(self) -> None:
        """Remove all entries from the store."""
        self._entries.clear()

    def compress(self, entry_id: str) -> bool:
        """Compress an entry by ID, removing content and retaining summary.

        Args:
            entry_id: ID of entry to compress

        Returns:
            True if entry was found (and compressed or already compressed),
            False if entry not found

        Raises:
            ValueError: If entry has no summary
        """
        entry = self.get(entry_id)
        if entry is None:
            return False
        entry.compress()
        return True

    def compress_multiple(self, entry_ids: list[str]) -> int:
        """Compress multiple entries.

        Args:
            entry_ids: List of entry IDs to compress

        Returns:
            Number of entries successfully compressed
        """
        compressed = 0
        for entry_id in entry_ids:
            entry = self.get(entry_id)
            if entry is not None and entry.can_compress():
                entry.compress()
                compressed += 1
        return compressed

    def get_content(self, entry_id: str) -> Optional[str]:
        """Get content of an entry.

        Args:
            entry_id: ID of entry

        Returns:
            Content string, or None if entry not found

        Raises:
            ContextCompressedError: If entry is compressed
        """
        entry = self.get(entry_id)
        if entry is None:
            return None
        return entry.get_content()

    def get_summary(self, entry_id: str) -> Optional[str]:
        """Get summary of an entry.

        Args:
            entry_id: ID of entry

        Returns:
            Summary string, or None if entry not found
        """
        entry = self.get(entry_id)
        if entry is None:
            return None
        return entry.summary

    def get_compressed(self) -> list[ContextEntry]:
        """Get all compressed entries.

        Returns:
            List of compressed entries
        """
        return [e for e in self._entries.values() if e.compressed]

    def get_uncompressed(self) -> list[ContextEntry]:
        """Get all uncompressed entries.

        Returns:
            List of uncompressed entries
        """
        return [e for e in self._entries.values() if not e.compressed]

    def add_command_result(
        self,
        command: str,
        result: str,
        summary: str,
        source: str = "bash",
        keep_command: bool = False,
        ttl: Optional[int] = None,
    ) -> str:
        """Add a command result, optionally discarding the command.

        This implements the command/result separation pattern from RLM:
        commands can be removed from context while their results are retained.

        Args:
            command: The command that was executed
            result: The output/result of the command
            summary: Summary of the result for compressed view
            source: Source identifier (default: "bash")
            keep_command: If True, store command entry; if False, discard
            ttl: Time-to-live for the result entry

        Returns:
            ID of the result entry
        """
        command_id = None

        if keep_command:
            # Create command entry (not searchable)
            command_id = self._generate_id()
            command_entry = ContextEntry(
                id=command_id,
                entry_type=EntryType.COMMAND,
                source=source,
                content=command,
                summary=f"Executed: {command[:50]}..." if len(command) > 50 else f"Executed: {command}",
                searchable=False,  # Commands not searchable
            )
            self.add(command_entry)

        # Create result entry
        result_id = self._generate_id()
        result_entry = ContextEntry(
            id=result_id,
            entry_type=EntryType.COMMAND_RESULT,
            source=source,
            content=result,
            summary=summary,
            parent_id=command_id,
            searchable=True,
            ttl=ttl,
        )
        self.add(result_entry)

        return result_id

    def process_ttl(self) -> int:
        """Decrement TTL for all entries that have TTL set.

        Returns:
            Number of entries whose TTL was decremented
        """
        decremented = 0
        for entry in self._entries.values():
            if entry.ttl is not None and entry.ttl > 0:
                entry.decrement_ttl()
                decremented += 1
        return decremented

    def cleanup_expired(self) -> int:
        """Remove all expired entries (TTL = 0).

        Returns:
            Number of entries removed
        """
        expired_ids = [e.id for e in self._entries.values() if e.is_expired()]
        for entry_id in expired_ids:
            del self._entries[entry_id]
        return len(expired_ids)

    def get_expired(self) -> list[ContextEntry]:
        """Get all expired entries (TTL = 0).

        Returns:
            List of expired entries
        """
        return [e for e in self._entries.values() if e.is_expired()]

    def get_expiring_soon(self, threshold: int = 2) -> list[ContextEntry]:
        """Get entries that will expire soon.

        Args:
            threshold: TTL threshold (entries with TTL <= threshold)

        Returns:
            List of entries expiring soon
        """
        return [
            e for e in self._entries.values()
            if e.ttl is not None and e.ttl <= threshold
        ]

    def process_turn(self) -> dict[str, int]:
        """Process a conversation turn: decrement TTLs and cleanup expired.

        This should be called at the end of each conversation turn.

        Returns:
            Dictionary with 'decremented' and 'removed' counts
        """
        decremented = self.process_ttl()
        removed = self.cleanup_expired()
        return {"decremented": decremented, "removed": removed}

    def extend_ttl(self, entry_id: str, additional: int) -> bool:
        """Extend an entry's TTL.

        Args:
            entry_id: ID of entry to extend
            additional: Number of turns to add to TTL

        Returns:
            True if entry found and TTL extended, False if not found
        """
        entry = self.get(entry_id)
        if entry is None:
            return False

        if entry.ttl is None:
            entry.set_ttl(additional)
        else:
            entry.set_ttl(entry.ttl + additional)
        return True
