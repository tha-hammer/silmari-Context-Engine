"""Tests for Context Window Array integration.

Phase 04: CWA Integration
Tests all 15 behaviors for the CWAIntegration class.
"""

import pytest
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from context_window_array import (
    CentralContextStore,
    EntryType,
    TaskSpec,
    TaskBatch,
)


class TestCWAInitialization:
    """Behavior 1: Initialize CWA Store."""

    def test_creates_central_store(self):
        """Given new instance, creates CentralContextStore."""
        cwa = CWAIntegration()

        assert isinstance(cwa.store, CentralContextStore)

    def test_store_starts_empty(self):
        """Given new instance, store has no entries."""
        cwa = CWAIntegration()

        assert len(cwa.store) == 0

    def test_creates_working_context(self):
        """Given new instance, working context available."""
        cwa = CWAIntegration()

        assert cwa.working_ctx is not None

    def test_creates_impl_context(self):
        """Given new instance, implementation context available."""
        cwa = CWAIntegration()

        assert cwa.impl_ctx is not None

    def test_custom_max_impl_entries(self):
        """Given custom max entries, implementation context respects it."""
        cwa = CWAIntegration(max_impl_entries=50)

        bounds_info = cwa.impl_ctx.get_bounds_info()
        assert bounds_info["max_entries"] == 50


class TestStoreResearchEntry:
    """Behavior 2: Store Research Entry."""

    def test_creates_file_entry(self):
        """Given research content, creates FILE entry."""
        cwa = CWAIntegration()

        entry_id = cwa.store_research(
            path="thoughts/research/2026-01-05-topic.md",
            content="# Research\n\nFindings...",
            summary="Research on topic X"
        )

        entry = cwa.store.get(entry_id)
        assert entry is not None
        assert entry.entry_type == EntryType.FILE

    def test_stores_content_and_summary(self):
        """Given content and summary, stores both."""
        cwa = CWAIntegration()

        entry_id = cwa.store_research(
            path="research.md",
            content="Full content here",
            summary="Brief summary"
        )

        entry = cwa.store.get(entry_id)
        assert entry.content == "Full content here"
        assert entry.summary == "Brief summary"
        assert entry.source == "research.md"

    def test_returns_unique_id(self):
        """Given multiple calls, returns unique IDs."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("r1.md", "c1", "s1")
        id2 = cwa.store_research("r2.md", "c2", "s2")

        assert id1 != id2

    def test_entry_is_searchable(self):
        """Given research entry, it is searchable by default."""
        cwa = CWAIntegration()

        entry_id = cwa.store_research("doc.md", "content", "summary")

        entry = cwa.store.get(entry_id)
        assert entry.searchable is True


class TestStoreRequirementEntry:
    """Behavior 3: Store Requirement Entry."""

    def test_creates_task_entry(self):
        """Given requirement, creates TASK entry."""
        cwa = CWAIntegration()

        entry_id = cwa.store_requirement(
            req_id="REQ-001",
            description="Implement user login",
            summary="Login requirement"
        )

        entry = cwa.store.get(entry_id)
        assert entry.entry_type == EntryType.TASK

    def test_has_ttl(self):
        """Given requirement, entry has TTL."""
        cwa = CWAIntegration()

        entry_id = cwa.store_requirement(
            req_id="REQ-001",
            description="Implement feature",
            summary="Feature req",
            ttl=10
        )

        entry = cwa.store.get(entry_id)
        assert entry.ttl == 10

    def test_default_ttl(self):
        """Given no TTL specified, uses default."""
        cwa = CWAIntegration()

        entry_id = cwa.store_requirement(
            req_id="REQ-001",
            description="Implement feature",
            summary="Feature req"
        )

        entry = cwa.store.get(entry_id)
        assert entry.ttl is not None
        assert entry.ttl == cwa.DEFAULT_REQUIREMENT_TTL

    def test_stores_req_id_in_source(self):
        """Given req_id, stores it in source field."""
        cwa = CWAIntegration()

        entry_id = cwa.store_requirement(
            req_id="REQ-001",
            description="desc",
            summary="sum"
        )

        entry = cwa.store.get(entry_id)
        assert "REQ-001" in entry.source


class TestStorePlanEntry:
    """Behavior 4: Store Plan Entry."""

    def test_creates_file_entry_for_plan(self):
        """Given plan content, creates FILE entry."""
        cwa = CWAIntegration()

        entry_id = cwa.store_plan(
            path="plans/2026-01-05-tdd-feature.md",
            content="# TDD Plan\n\n## Behaviors...",
            summary="TDD plan for feature X"
        )

        entry = cwa.store.get(entry_id)
        assert entry.entry_type == EntryType.FILE
        assert "plans/" in entry.source

    def test_stores_content_and_summary(self):
        """Given content and summary, stores both."""
        cwa = CWAIntegration()

        entry_id = cwa.store_plan(
            path="plans/test.md",
            content="Full plan content",
            summary="Plan summary"
        )

        entry = cwa.store.get(entry_id)
        assert entry.content == "Full plan content"
        assert entry.summary == "Plan summary"


class TestSearchContext:
    """Behavior 5: Search Context."""

    def test_finds_relevant_entries(self):
        """Given query, returns matching entries."""
        cwa = CWAIntegration()

        # Add entries
        cwa.store_research("auth.md", "Authentication flow docs", "Auth system research")
        cwa.store_research("db.md", "Database schema docs", "Database research")

        results = cwa.search("authentication login", max_results=5)

        assert len(results) > 0
        # First result should be auth-related
        assert any("auth" in r.summary.lower() for r in results)

    def test_respects_max_results(self):
        """Given max_results, limits output."""
        cwa = CWAIntegration()

        for i in range(10):
            cwa.store_research(f"doc{i}.md", f"Content {i}", f"Summary {i}")

        results = cwa.search("content", max_results=3)

        assert len(results) <= 3

    def test_returns_empty_for_no_entries(self):
        """Given no entries, returns empty list."""
        cwa = CWAIntegration()

        results = cwa.search("query", max_results=5)

        assert results == []

    def test_returns_empty_for_empty_query(self):
        """Given empty query, returns empty list."""
        cwa = CWAIntegration()
        cwa.store_research("doc.md", "content", "summary")

        results = cwa.search("", max_results=5)

        assert results == []


class TestBuildWorkingContext:
    """Behavior 6: Build Working LLM Context."""

    def test_returns_all_entries_as_summaries(self):
        """Given entries, returns summaries only."""
        cwa = CWAIntegration()

        cwa.store_research("doc1.md", "Full content 1", "Summary 1")
        cwa.store_research("doc2.md", "Full content 2", "Summary 2")

        context = cwa.build_working_context()

        assert context.total_count == 2
        for entry_view in context.entries:
            assert entry_view.content is None
            assert entry_view.summary is not None

    def test_empty_store_returns_empty_context(self):
        """Given empty store, returns empty context."""
        cwa = CWAIntegration()

        context = cwa.build_working_context()

        assert context.total_count == 0
        assert context.entries == []


class TestBuildImplementationContext:
    """Behavior 7: Build Implementation Context."""

    def test_returns_full_content(self):
        """Given entry IDs, returns full content."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Full content here", "Summary")

        context = cwa.build_impl_context([id1])

        assert context.entry_count == 1
        for entry in context.entries:
            assert entry.content == "Full content here"

    def test_bounded_to_max_entries(self):
        """Given too many IDs, raises error."""
        cwa = CWAIntegration(max_impl_entries=5)

        entry_ids = []
        for i in range(10):
            entry_ids.append(cwa.store_research(f"doc{i}.md", f"Content {i}", f"Sum {i}"))

        # Should raise ValueError
        with pytest.raises(ValueError):
            cwa.build_impl_context(entry_ids)

    def test_validates_bounds_before_build(self):
        """Given entry IDs, can validate bounds."""
        cwa = CWAIntegration(max_impl_entries=5)

        entry_ids = [cwa.store_research(f"d{i}.md", f"c{i}", f"s{i}") for i in range(3)]

        assert cwa.validate_impl_bounds(entry_ids) is True

        # Now add more entries and check again
        more_ids = [cwa.store_research(f"e{i}.md", f"c{i}", f"s{i}") for i in range(10)]
        assert cwa.validate_impl_bounds(more_ids) is False


class TestContextManager:
    """Behavior 8: Context Manager for Entries."""

    def test_request_provides_context(self):
        """Given entry IDs, context manager provides context."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Content", "Summary")

        with cwa.request_entries([id1]) as context:
            assert context.entry_count == 1

    def test_entries_active_during_context(self):
        """Given context manager, entries are marked active."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Content", "Summary")

        with cwa.request_entries([id1]) as _context:
            assert cwa.impl_ctx.is_in_use(id1)

    def test_releases_on_exit(self):
        """Given context manager, releases entries after block."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Content", "Summary")

        with cwa.request_entries([id1]) as _context:
            pass

        # After context manager, entries should be released
        assert not cwa.impl_ctx.is_in_use(id1)

    def test_releases_on_exception(self):
        """Given exception in block, still releases entries."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Content", "Summary")

        try:
            with cwa.request_entries([id1]) as _context:
                raise ValueError("Test error")
        except ValueError:
            pass

        # Entries should still be released
        assert not cwa.impl_ctx.is_in_use(id1)


class TestProcessTurn:
    """Behavior 9: Process Turn (TTL Management)."""

    def test_decrements_ttl(self):
        """Given entries with TTL, decrements on process_turn."""
        cwa = CWAIntegration()
        entry_id = cwa.store_requirement("R1", "desc", "sum", ttl=5)

        cwa.process_turn()

        entry = cwa.store.get(entry_id)
        assert entry.ttl == 4

    def test_removes_expired(self):
        """Given entry with TTL=1, removes after process_turn."""
        cwa = CWAIntegration()
        entry_id = cwa.store_requirement("R1", "desc", "sum", ttl=1)

        cwa.process_turn()

        assert cwa.store.get(entry_id) is None

    def test_returns_stats(self):
        """Given entries, returns stats about TTL processing."""
        cwa = CWAIntegration()
        cwa.store_requirement("R1", "desc1", "sum1", ttl=5)
        cwa.store_requirement("R2", "desc2", "sum2", ttl=1)

        stats = cwa.process_turn()

        assert "decremented" in stats
        assert "removed" in stats


class TestCompressEntries:
    """Behavior 10: Compress Old Entries."""

    def test_removes_content_keeps_summary(self):
        """Given entry, compression removes content but keeps summary."""
        cwa = CWAIntegration()
        entry_id = cwa.store_research("doc.md", "Full content", "Summary")

        cwa.compress_entries([entry_id])

        entry = cwa.store.get(entry_id)
        assert entry.content is None
        assert entry.summary == "Summary"
        assert entry.compressed is True

    def test_compress_multiple(self):
        """Given multiple entries, compresses all."""
        cwa = CWAIntegration()
        id1 = cwa.store_research("doc1.md", "Content 1", "Summary 1")
        id2 = cwa.store_research("doc2.md", "Content 2", "Summary 2")

        compressed = cwa.compress_entries([id1, id2])

        assert compressed == 2
        assert cwa.store.get(id1).compressed is True
        assert cwa.store.get(id2).compressed is True


class TestGetExpiringSoon:
    """Behavior 11: Get Expiring Entries."""

    def test_returns_low_ttl_entries(self):
        """Given entries with various TTLs, returns those expiring soon."""
        cwa = CWAIntegration()
        id1 = cwa.store_requirement("R1", "d1", "s1", ttl=2)
        id2 = cwa.store_requirement("R2", "d2", "s2", ttl=10)

        expiring = cwa.get_expiring_soon(threshold=3)

        assert id1 in [e.id for e in expiring]
        assert id2 not in [e.id for e in expiring]

    def test_default_threshold(self):
        """Given no threshold, uses default of 2."""
        cwa = CWAIntegration()
        id1 = cwa.store_requirement("R1", "d1", "s1", ttl=2)
        id2 = cwa.store_requirement("R2", "d2", "s2", ttl=3)

        expiring = cwa.get_expiring_soon()

        assert id1 in [e.id for e in expiring]
        # ttl=3 > default threshold of 2
        assert id2 not in [e.id for e in expiring]


class TestStoreCommandResult:
    """Behavior 12: Store Command Result."""

    def test_creates_command_result_entry(self):
        """Given command result, creates COMMAND_RESULT entry."""
        cwa = CWAIntegration()

        entry_id = cwa.store_command_result(
            command="pytest tests/",
            result="5 passed",
            summary="All tests pass"
        )

        entry = cwa.store.get(entry_id)
        assert entry.entry_type == EntryType.COMMAND_RESULT

    def test_stores_result_content(self):
        """Given result, stores it as content."""
        cwa = CWAIntegration()

        entry_id = cwa.store_command_result(
            command="ls -la",
            result="file1.py\nfile2.py",
            summary="Listed 2 files"
        )

        entry = cwa.store.get(entry_id)
        assert entry.content == "file1.py\nfile2.py"
        assert entry.summary == "Listed 2 files"

    def test_can_set_ttl(self):
        """Given TTL, command result entry has TTL."""
        cwa = CWAIntegration()

        entry_id = cwa.store_command_result(
            command="cmd",
            result="output",
            summary="summary",
            ttl=5
        )

        entry = cwa.store.get(entry_id)
        assert entry.ttl == 5


class TestCreateBatches:
    """Behavior 13: Task Batching."""

    def test_creates_batches_under_limit(self):
        """Given tasks with entries, creates batches respecting limit."""
        cwa = CWAIntegration()

        # Add entries
        ids = [cwa.store_research(f"d{i}.md", f"c{i}", f"s{i}") for i in range(150)]

        tasks = [
            TaskSpec(id="t1", description="Task 1", required_entry_ids=ids[:50]),
            TaskSpec(id="t2", description="Task 2", required_entry_ids=ids[50:100]),
            TaskSpec(id="t3", description="Task 3", required_entry_ids=ids[100:150]),
        ]

        batches = cwa.create_batches(tasks, max_entries=100)

        assert len(batches) >= 2  # Can't fit all in one batch
        for batch in batches:
            assert batch.entry_count <= 100

    def test_empty_tasks_returns_empty(self):
        """Given no tasks, returns empty list."""
        cwa = CWAIntegration()

        batches = cwa.create_batches([])

        assert batches == []

    def test_uses_default_max_entries(self):
        """Given no max_entries, uses impl_ctx max."""
        cwa = CWAIntegration(max_impl_entries=50)

        ids = [cwa.store_research(f"d{i}.md", f"c{i}", f"s{i}") for i in range(100)]
        tasks = [TaskSpec(id="t1", description="Task 1", required_entry_ids=ids)]

        batches = cwa.create_batches(tasks)

        # Should split because default uses impl_ctx max (50)
        # Single task with 100 entries will exceed limit
        assert len(batches) >= 1


class TestExecuteBatch:
    """Behavior 14: Execute Batch."""

    def test_executes_with_proper_context(self):
        """Given batch, executes handler with context."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Content", "Summary")
        task = TaskSpec(id="t1", description="Test task", required_entry_ids=[id1])
        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[task],
            unique_entry_ids={id1}
        )

        results = []

        def handler(context, tasks):
            results.append(context.entry_count)
            return {"t1": "done"}

        result = cwa.execute_batch(batch, handler)

        assert result.success is True
        assert result.task_results == {"t1": "done"}
        assert results == [1]

    def test_releases_context_after_execution(self):
        """Given batch execution, releases context after."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Content", "Summary")
        task = TaskSpec(id="t1", description="Test task", required_entry_ids=[id1])
        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[task],
            unique_entry_ids={id1}
        )

        def handler(context, tasks):
            # During execution, entries should be active
            assert cwa.impl_ctx.is_in_use(id1)
            return {}

        cwa.execute_batch(batch, handler)

        # After execution, entries should be released
        assert not cwa.impl_ctx.is_in_use(id1)

    def test_handles_handler_exceptions(self):
        """Given handler exception, returns error result."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Content", "Summary")
        task = TaskSpec(id="t1", description="Test task", required_entry_ids=[id1])
        batch = TaskBatch(
            batch_id="batch_001",
            tasks=[task],
            unique_entry_ids={id1}
        )

        def handler(context, tasks):
            raise RuntimeError("Handler failed")

        result = cwa.execute_batch(batch, handler)

        assert result.success is False
        assert result.error is not None


class TestGetByType:
    """Behavior 15: Get Entries by Type."""

    def test_returns_only_matching_type(self):
        """Given mixed types, returns only matching type."""
        cwa = CWAIntegration()

        cwa.store_research("doc.md", "content", "summary")  # FILE
        req_id = cwa.store_requirement("R1", "desc", "sum")  # TASK

        tasks = cwa.get_by_type(EntryType.TASK)

        assert len(tasks) == 1
        assert tasks[0].id == req_id

    def test_returns_empty_for_no_matches(self):
        """Given no matching type, returns empty list."""
        cwa = CWAIntegration()

        cwa.store_research("doc.md", "content", "summary")  # FILE

        tasks = cwa.get_by_type(EntryType.TASK)

        assert tasks == []

    def test_returns_multiple_of_same_type(self):
        """Given multiple entries of same type, returns all."""
        cwa = CWAIntegration()

        cwa.store_research("doc1.md", "c1", "s1")
        cwa.store_research("doc2.md", "c2", "s2")
        cwa.store_research("doc3.md", "c3", "s3")

        files = cwa.get_by_type(EntryType.FILE)

        assert len(files) == 3
