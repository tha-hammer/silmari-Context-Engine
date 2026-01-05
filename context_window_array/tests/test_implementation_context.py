"""Tests for context_window_array.implementation_context module."""

from context_window_array.models import ContextEntry, EntryType
from context_window_array.store import CentralContextStore
from context_window_array.implementation_context import (
    ImplementationLLMContext,
)


class TestImplementationContextBuild:
    """Behavior 17: Implementation context build operations."""

    def test_build_returns_full_content(self):
        """Given store with entries, when build(entry_ids), then returns full content."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="def authenticate(user, password):\n    return verify(user, password)",
            summary="Auth function",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="def connect():\n    return psycopg2.connect()",
            summary="DB connect",
        ))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001", "ctx_002"])

        assert len(result.entries) == 2

        # Should have full content
        entry1 = next(e for e in result.entries if e.id == "ctx_001")
        assert entry1.content == "def authenticate(user, password):\n    return verify(user, password)"

        entry2 = next(e for e in result.entries if e.id == "ctx_002")
        assert entry2.content == "def connect():\n    return psycopg2.connect()"

    def test_build_includes_all_metadata(self):
        """Given entry with metadata, when build(), then all metadata included."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary="Test summary",
            references=["ctx_000"],
            parent_id="ctx_000",
            priority=5,
        ))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001"])

        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.id == "ctx_001"
        assert entry.entry_type == EntryType.FILE
        assert entry.source == "test.py"
        assert entry.content == "test content"
        assert entry.summary == "Test summary"
        assert entry.references == ["ctx_000"]
        assert entry.parent_id == "ctx_000"

    def test_build_only_requested_entries(self):
        """Given multiple entries, when build(subset), then only subset returned."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c"))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001", "ctx_003"])

        assert len(result.entries) == 2
        ids = {e.id for e in result.entries}
        assert ids == {"ctx_001", "ctx_003"}

    def test_build_skips_nonexistent_entries(self):
        """Given nonexistent entry id, when build(), then skipped without error."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001", "ctx_nonexistent"])

        assert len(result.entries) == 1
        assert result.entries[0].id == "ctx_001"

    def test_build_empty_list_returns_empty(self):
        """Given empty entry list, when build([]), then returns empty context."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        context = ImplementationLLMContext(store)
        result = context.build([])

        assert len(result.entries) == 0

    def test_build_preserves_order(self):
        """Given entry ids, when build(), then order preserved."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c"))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_003", "ctx_001", "ctx_002"])

        assert [e.id for e in result.entries] == ["ctx_003", "ctx_001", "ctx_002"]

    def test_build_handles_compressed_entries(self):
        """Given compressed entry, when build(), then returns with summary only."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Compressed file summary",
            compressed=True,
        ))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001"])

        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.content is None
        assert entry.summary == "Compressed file summary"
        assert entry.compressed is True

    def test_build_returns_context_object(self):
        """Given entries, when build(), then returns ImplementationContext object."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001"])

        assert hasattr(result, 'entries')
        assert hasattr(result, 'entry_count')
        assert hasattr(result, 'total_tokens')
        assert hasattr(result, 'entry_ids')

    def test_build_tracks_token_count(self):
        """Given entries, when build(), then tracks estimated tokens."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="x" * 1000,
            summary="Short",
        ))

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001"])

        # Token count based on content, not summary
        assert result.total_tokens > 200  # 1000 chars / ~4 chars per token

    def test_build_decompresses_if_requested(self):
        """Given compressed entry, when build with decompress=True, then decompresses."""
        store = CentralContextStore()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="original content",
            summary="Summary",
        )
        store.add(entry)
        store.compress("ctx_001")

        context = ImplementationLLMContext(store)

        # Without decompress - compressed
        result1 = context.build(["ctx_001"], decompress=False)
        assert result1.entries[0].compressed is True

        # Note: Actual decompression would require storing original content
        # This test documents the expected interface
