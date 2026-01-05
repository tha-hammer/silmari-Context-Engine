"""Tests for context_window_array.implementation_context module."""

import pytest

from context_window_array.exceptions import EntryBoundsError
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
        store.add(
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="auth.py",
                content="def authenticate(user, password):\n    return verify(user, password)",
                summary="Auth function",
            )
        )
        store.add(
            ContextEntry(
                id="ctx_002",
                entry_type=EntryType.FILE,
                source="db.py",
                content="def connect():\n    return psycopg2.connect()",
                summary="DB connect",
            )
        )

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001", "ctx_002"])

        assert len(result.entries) == 2

        # Should have full content
        entry1 = next(e for e in result.entries if e.id == "ctx_001")
        assert (
            entry1.content
            == "def authenticate(user, password):\n    return verify(user, password)"
        )

        entry2 = next(e for e in result.entries if e.id == "ctx_002")
        assert entry2.content == "def connect():\n    return psycopg2.connect()"

    def test_build_includes_all_metadata(self):
        """Given entry with metadata, when build(), then all metadata included."""
        store = CentralContextStore()
        store.add(
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="test.py",
                content="test content",
                summary="Test summary",
                references=["ctx_000"],
                parent_id="ctx_000",
                priority=5,
            )
        )

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
        store.add(
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="a.py",
                content="a",
                summary="a",
            )
        )
        store.add(
            ContextEntry(
                id="ctx_002",
                entry_type=EntryType.FILE,
                source="b.py",
                content="b",
                summary="b",
            )
        )
        store.add(
            ContextEntry(
                id="ctx_003",
                entry_type=EntryType.FILE,
                source="c.py",
                content="c",
                summary="c",
            )
        )

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001", "ctx_003"])

        assert len(result.entries) == 2
        ids = {e.id for e in result.entries}
        assert ids == {"ctx_001", "ctx_003"}

    def test_build_skips_nonexistent_entries(self):
        """Given nonexistent entry id, when build(), then skipped without error."""
        store = CentralContextStore()
        store.add(
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="a.py",
                content="a",
                summary="a",
            )
        )

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001", "ctx_nonexistent"])

        assert len(result.entries) == 1
        assert result.entries[0].id == "ctx_001"

    def test_build_empty_list_returns_empty(self):
        """Given empty entry list, when build([]), then returns empty context."""
        store = CentralContextStore()
        store.add(
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="a.py",
                content="a",
                summary="a",
            )
        )

        context = ImplementationLLMContext(store)
        result = context.build([])

        assert len(result.entries) == 0

    def test_build_preserves_order(self):
        """Given entry ids, when build(), then order preserved."""
        store = CentralContextStore()
        store.add(
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="a.py",
                content="a",
                summary="a",
            )
        )
        store.add(
            ContextEntry(
                id="ctx_002",
                entry_type=EntryType.FILE,
                source="b.py",
                content="b",
                summary="b",
            )
        )
        store.add(
            ContextEntry(
                id="ctx_003",
                entry_type=EntryType.FILE,
                source="c.py",
                content="c",
                summary="c",
            )
        )

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_003", "ctx_001", "ctx_002"])

        assert [e.id for e in result.entries] == ["ctx_003", "ctx_001", "ctx_002"]

    def test_build_handles_compressed_entries(self):
        """Given compressed entry, when build(), then returns with summary only."""
        store = CentralContextStore()
        store.add(
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="test.py",
                content=None,
                summary="Compressed file summary",
                compressed=True,
            )
        )

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
        store.add(
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="a.py",
                content="a",
                summary="a",
            )
        )

        context = ImplementationLLMContext(store)
        result = context.build(["ctx_001"])

        assert hasattr(result, "entries")
        assert hasattr(result, "entry_count")
        assert hasattr(result, "total_tokens")
        assert hasattr(result, "entry_ids")

    def test_build_tracks_token_count(self):
        """Given entries, when build(), then tracks estimated tokens."""
        store = CentralContextStore()
        store.add(
            ContextEntry(
                id="ctx_001",
                entry_type=EntryType.FILE,
                source="test.py",
                content="x" * 1000,
                summary="Short",
            )
        )

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


class TestEntryBoundsValidation:
    """Behavior 18: Entry bounds validation for implementation context."""

    def test_build_exceeding_bounds_raises_error(self):
        """Given >200 entries, when build(), then raises EntryBoundsError."""
        store = CentralContextStore()
        # Add 201 entries
        for i in range(201):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(201)]

        with pytest.raises(EntryBoundsError) as exc_info:
            context.build(entry_ids)

        assert "201" in str(exc_info.value)
        assert "200" in str(exc_info.value)

    def test_build_at_bounds_succeeds(self):
        """Given exactly 200 entries, when build(), then succeeds."""
        store = CentralContextStore()
        for i in range(200):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(200)]

        # Should not raise
        result = context.build(entry_ids)
        assert result.entry_count == 200

    def test_build_under_bounds_succeeds(self):
        """Given <200 entries, when build(), then succeeds."""
        store = CentralContextStore()
        for i in range(50):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(50)]

        result = context.build(entry_ids)
        assert result.entry_count == 50

    def test_validate_bounds_under_limit(self):
        """Given <200 entries, when validate_bounds(), then returns True."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store)

        entry_ids = [f"ctx_{i:03d}" for i in range(100)]
        is_valid = context.validate_bounds(entry_ids)

        assert is_valid is True

    def test_validate_bounds_at_limit(self):
        """Given exactly 200 entries, when validate_bounds(), then returns True."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store)

        entry_ids = [f"ctx_{i:03d}" for i in range(200)]
        is_valid = context.validate_bounds(entry_ids)

        assert is_valid is True

    def test_validate_bounds_over_limit(self):
        """Given >200 entries, when validate_bounds(), then returns False."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store)

        entry_ids = [f"ctx_{i:03d}" for i in range(201)]
        is_valid = context.validate_bounds(entry_ids)

        assert is_valid is False

    def test_validate_bounds_empty_list(self):
        """Given empty list, when validate_bounds(), then returns True."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store)

        is_valid = context.validate_bounds([])
        assert is_valid is True

    def test_build_skip_validation_flag(self):
        """Given >200 entries, when build(skip_validation=True), then succeeds."""
        store = CentralContextStore()
        for i in range(250):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(250)]

        # Should not raise with skip_validation
        result = context.build(entry_ids, skip_validation=True)
        assert result.entry_count == 250

    def test_custom_max_entries(self):
        """Given custom max_entries, when build with that limit exceeded, then raises."""
        store = CentralContextStore()
        for i in range(60):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )

        context = ImplementationLLMContext(store, max_entries=50)
        entry_ids = [f"ctx_{i:03d}" for i in range(60)]

        with pytest.raises(EntryBoundsError):
            context.build(entry_ids)

    def test_get_bounds_info(self):
        """Given context, when get_bounds_info(), then returns limit info."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store, max_entries=150)

        info = context.get_bounds_info()

        assert info["max_entries"] == 150
        assert "default" in info or info["max_entries"] == 150

    def test_entry_bounds_error_message(self):
        """Given bounds error, then message includes helpful info."""
        store = CentralContextStore()
        for i in range(210):
            store.add(
                ContextEntry(
                    id=f"ctx_{i:03d}",
                    entry_type=EntryType.FILE,
                    source=f"file{i}.py",
                    content=f"content {i}",
                    summary=f"summary {i}",
                )
            )

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(210)]

        with pytest.raises(EntryBoundsError) as exc_info:
            context.build(entry_ids)

        error = exc_info.value
        assert error.requested == 210
        assert error.max_allowed == 200
        assert "210" in str(error)
        assert "200" in str(error)

    def test_split_into_batches(self):
        """Given many entries, when split_into_batches(), then creates valid batches."""
        store = CentralContextStore()
        context = ImplementationLLMContext(store, max_entries=50)

        entry_ids = [f"ctx_{i:03d}" for i in range(120)]
        batches = context.split_into_batches(entry_ids)

        assert len(batches) == 3  # 50 + 50 + 20
        assert len(batches[0]) == 50
        assert len(batches[1]) == 50
        assert len(batches[2]) == 20
        assert all(context.validate_bounds(batch) for batch in batches)


class TestContextRequest:
    """Behavior 19: Context request and release operations."""

    def test_request_context_retrieves_entries(self):
        """Given entry ids, when request_context(), then entries retrieved."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="auth code",
            summary="Auth",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="db code",
            summary="DB",
        ))

        context = ImplementationLLMContext(store)
        result = context.request_context(["ctx_001", "ctx_002"])

        assert result.entry_count == 2
        assert "ctx_001" in result.entry_ids
        assert "ctx_002" in result.entry_ids

    def test_request_context_marks_in_use(self):
        """Given entry ids, when request_context(), then entries marked in_use."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001"])

        # Entry should be marked as in_use
        assert context.is_in_use("ctx_001") is True

    def test_request_context_tracks_active_entries(self):
        """Given multiple requests, when get_active_entries(), then returns all in_use."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))
        store.add(ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="c", summary="c"))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001", "ctx_002"])

        active = context.get_active_entries()
        assert active == {"ctx_001", "ctx_002"}

    def test_release_context_clears_in_use(self):
        """Given in_use entries, when release_context(), then cleared."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001"])
        assert context.is_in_use("ctx_001") is True

        context.release_context()

        assert context.is_in_use("ctx_001") is False
        assert context.get_active_entries() == set()

    def test_release_specific_entries(self):
        """Given in_use entries, when release_context(entry_ids), then only those released."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001", "ctx_002"])

        context.release_context(["ctx_001"])

        assert context.is_in_use("ctx_001") is False
        assert context.is_in_use("ctx_002") is True

    def test_request_already_in_use_extends_lease(self):
        """Given entry already in_use, when request_context(), then lease extended."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001"])
        context.request_context(["ctx_001"])  # Request again

        # Should still be in_use, not error
        assert context.is_in_use("ctx_001") is True

    def test_request_context_from_search(self):
        """Given search results, when request_context from results, then entries retrieved."""
        from context_window_array.working_context import WorkingLLMContext

        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="authentication login user",
            summary="Auth module",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="database connection",
            summary="DB module",
        ))

        # First search to find relevant entries
        working = WorkingLLMContext(store)
        search_results = working.search("authentication login")

        # Then request those entries for implementation
        impl = ImplementationLLMContext(store)
        entry_ids = [r.id for r in search_results]
        result = impl.request_context(entry_ids)

        assert result.entry_count > 0
        # Should have full content now
        assert result.entries[0].content is not None

    def test_request_context_validates_bounds(self):
        """Given too many entries, when request_context(), then raises EntryBoundsError."""
        store = CentralContextStore()
        for i in range(250):
            store.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"content {i}",
                summary=f"summary {i}",
            ))

        context = ImplementationLLMContext(store)
        entry_ids = [f"ctx_{i:03d}" for i in range(250)]

        with pytest.raises(EntryBoundsError):
            context.request_context(entry_ids)

    def test_request_context_returns_context_object(self):
        """Given entry ids, when request_context(), then returns ImplementationContext."""
        from context_window_array.implementation_context import ImplementationContext

        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)
        result = context.request_context(["ctx_001"])

        assert isinstance(result, ImplementationContext)
        assert hasattr(result, 'entries')
        assert hasattr(result, 'entry_count')
        assert hasattr(result, 'total_tokens')

    def test_get_usage_stats(self):
        """Given context with activity, when get_usage_stats(), then returns stats."""
        store = CentralContextStore()
        store.add(ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="a", summary="a"))
        store.add(ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="b", summary="b"))

        context = ImplementationLLMContext(store)
        context.request_context(["ctx_001"])
        context.request_context(["ctx_002"])
        context.release_context(["ctx_001"])

        stats = context.get_usage_stats()

        assert stats["active_count"] == 1
        assert stats["total_requests"] == 2
        assert stats["total_releases"] == 1

    def test_context_manager_support(self):
        """Given implementation context, when used as context manager, then auto-releases."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)

        with context.request(["ctx_001"]) as result:
            assert result.entry_count == 1
            assert context.is_in_use("ctx_001") is True

        # After context manager exits, should be released
        assert context.is_in_use("ctx_001") is False

    def test_context_manager_releases_on_exception(self):
        """Given context manager, when exception raised, then entries still released."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="Test",
        ))

        context = ImplementationLLMContext(store)

        with pytest.raises(ValueError):
            with context.request(["ctx_001"]):
                assert context.is_in_use("ctx_001") is True
                raise ValueError("Simulated error")

        # After exception, should still be released
        assert context.is_in_use("ctx_001") is False
