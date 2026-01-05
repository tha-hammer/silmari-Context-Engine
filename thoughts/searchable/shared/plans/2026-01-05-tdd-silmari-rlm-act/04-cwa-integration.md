# Phase 04: Context Window Array Integration TDD Plan

## Overview

Integrate the Context Window Array (CWA) into the silmari-rlm-act pipeline for context management. This enables semantic search, entry lifecycle management, and bounded context for implementation LLMs.

## Reference

See: `thoughts/searchable/shared/docs/2026-01-05-how-to-use-context-window-array.md`

## Testable Behaviors

### Behavior 1: Initialize CWA Store
**Given**: Pipeline startup
**When**: Creating CWAIntegration
**Then**: CentralContextStore is initialized

### Behavior 2: Store Research Entry
**Given**: Research document content
**When**: Calling store_research(path, content, summary)
**Then**: FILE entry created with unique ID

### Behavior 3: Store Requirement Entry
**Given**: Requirement from decomposition
**When**: Calling store_requirement(req)
**Then**: TASK entry created with TTL

### Behavior 4: Store Plan Entry
**Given**: TDD plan document
**When**: Calling store_plan(path, content, summary)
**Then**: FILE entry created and indexed

### Behavior 5: Search Context
**Given**: Store with multiple entries
**When**: Calling search(query, max_results)
**Then**: Returns relevant entries by similarity

### Behavior 6: Build Working LLM Context
**Given**: Entries in store
**When**: Calling build_working_context()
**Then**: Returns summaries only, all entries

### Behavior 7: Build Implementation Context
**Given**: Specific entry IDs
**When**: Calling build_impl_context(entry_ids)
**Then**: Returns full content, bounded to <200

### Behavior 8: Context Manager for Entries
**Given**: Entry IDs to use
**When**: Using request() context manager
**Then**: Entries released after block

### Behavior 9: Process Turn (TTL Management)
**Given**: Entries with TTL
**When**: Calling process_turn()
**Then**: TTL decremented, expired removed

### Behavior 10: Compress Old Entries
**Given**: Old entries with full content
**When**: Calling compress_entries(entry_ids)
**Then**: Content removed, summary kept

### Behavior 11: Get Expiring Entries
**Given**: Entries with low TTL
**When**: Calling get_expiring_soon(threshold=2)
**Then**: Returns entries expiring within threshold

### Behavior 12: Store Command Result
**Given**: Command execution result
**When**: Calling store_command_result(cmd, result, summary)
**Then**: COMMAND_RESULT entry created

### Behavior 13: Task Batching
**Given**: Tasks with entry requirements
**When**: Calling create_batches(tasks)
**Then**: Returns batches respecting <200 limit

### Behavior 14: Execute Batch
**Given**: Task batch
**When**: Calling execute_batch(batch, handler)
**Then**: Executes with proper context lifecycle

### Behavior 15: Get Entries by Type
**Given**: Mixed entry types in store
**When**: Calling get_by_type(EntryType.TASK)
**Then**: Returns only TASK entries

---

## TDD Cycle: Behavior 1 - Initialize CWA Store

### Test Specification
**Given**: New CWAIntegration instance
**When**: Accessing the store property
**Then**: Returns CentralContextStore instance

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_cwa_integration.py`
```python
import pytest
from silmari_rlm_act.context.cwa_integration import CWAIntegration
from context_window_array import CentralContextStore


class TestCWAInitialization:
    """Behavior 1: Initialize CWA Store."""

    def test_creates_central_store(self):
        """Given new instance, creates CentralContextStore."""
        cwa = CWAIntegration()

        assert isinstance(cwa.store, CentralContextStore)

    def test_store_starts_empty(self):
        """Given new instance, store has no entries."""
        cwa = CWAIntegration()

        assert cwa.store.count() == 0

    def test_creates_working_context(self):
        """Given new instance, working context available."""
        cwa = CWAIntegration()

        assert cwa.working_ctx is not None
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/context/cwa_integration.py`
```python
"""Context Window Array integration for pipeline."""

from typing import Optional
from context_window_array import (
    CentralContextStore,
    ContextEntry,
    EntryType,
)
from context_window_array.working_context import WorkingLLMContext
from context_window_array.implementation_context import ImplementationLLMContext


class CWAIntegration:
    """Manages Context Window Array for pipeline phases."""

    def __init__(self, max_impl_entries: int = 200):
        """Initialize CWA integration.

        Args:
            max_impl_entries: Maximum entries for implementation context
        """
        self._store = CentralContextStore()
        self._working_ctx = WorkingLLMContext(self._store)
        self._impl_ctx = ImplementationLLMContext(self._store, max_entries=max_impl_entries)
        self._entry_counter = 0

    @property
    def store(self) -> CentralContextStore:
        """Get the central context store."""
        return self._store

    @property
    def working_ctx(self) -> WorkingLLMContext:
        """Get working LLM context (summaries only)."""
        return self._working_ctx

    @property
    def impl_ctx(self) -> ImplementationLLMContext:
        """Get implementation LLM context (full content)."""
        return self._impl_ctx

    def _next_id(self, prefix: str = "ctx") -> str:
        """Generate next unique entry ID."""
        self._entry_counter += 1
        return f"{prefix}_{self._entry_counter:04d}"
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_cwa_integration.py::TestCWAInitialization -v`

---

## TDD Cycle: Behavior 2 - Store Research Entry

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_cwa_integration.py`
```python
from context_window_array import EntryType


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
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/context/cwa_integration.py`
```python
class CWAIntegration:
    # ... existing code ...

    def store_research(
        self,
        path: str,
        content: str,
        summary: str
    ) -> str:
        """Store research document as FILE entry.

        Args:
            path: Path to research document
            content: Full document content
            summary: Brief summary for working LLM

        Returns:
            Entry ID
        """
        entry_id = self._next_id("research")
        entry = ContextEntry(
            id=entry_id,
            entry_type=EntryType.FILE,
            source=path,
            content=content,
            summary=summary,
        )
        self._store.add(entry)
        return entry_id
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_cwa_integration.py::TestStoreResearchEntry -v`

---

## TDD Cycle: Behavior 3 - Store Requirement Entry

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_cwa_integration.py`
```python
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
        assert entry.ttl is not None  # Has some default
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/context/cwa_integration.py`
```python
class CWAIntegration:
    # ... existing code ...

    DEFAULT_REQUIREMENT_TTL = 20  # Turns until requirement expires

    def store_requirement(
        self,
        req_id: str,
        description: str,
        summary: str,
        ttl: Optional[int] = None
    ) -> str:
        """Store requirement as TASK entry.

        Args:
            req_id: Requirement ID from decomposition
            description: Full requirement description
            summary: Brief summary
            ttl: Time-to-live in turns (default: 20)

        Returns:
            Entry ID
        """
        entry_id = self._next_id("req")
        entry = ContextEntry(
            id=entry_id,
            entry_type=EntryType.TASK,
            source=f"requirement:{req_id}",
            content=description,
            summary=summary,
            ttl=ttl or self.DEFAULT_REQUIREMENT_TTL,
        )
        self._store.add(entry)
        return entry_id
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_cwa_integration.py::TestStoreRequirementEntry -v`

---

## TDD Cycle: Behavior 4-5 - Store Plan and Search

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_cwa_integration.py`
```python
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

    def test_returns_empty_for_no_match(self):
        """Given no matching entries, returns empty."""
        cwa = CWAIntegration()

        cwa.store_research("doc.md", "Unrelated content", "Unrelated summary")

        results = cwa.search("xyz123nonexistent", max_results=5)

        assert len(results) == 0 or all(r.score < 0.1 for r in results)
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/context/cwa_integration.py`
```python
from context_window_array import StoreSearchResult


class CWAIntegration:
    # ... existing code ...

    def store_plan(
        self,
        path: str,
        content: str,
        summary: str
    ) -> str:
        """Store TDD plan document as FILE entry.

        Args:
            path: Path to plan document
            content: Full plan content
            summary: Brief summary

        Returns:
            Entry ID
        """
        entry_id = self._next_id("plan")
        entry = ContextEntry(
            id=entry_id,
            entry_type=EntryType.FILE,
            source=path,
            content=content,
            summary=summary,
        )
        self._store.add(entry)
        return entry_id

    def search(
        self,
        query: str,
        max_results: int = 10,
        min_score: float = 0.1
    ) -> list[StoreSearchResult]:
        """Search for relevant context entries.

        Args:
            query: Search query
            max_results: Maximum results to return
            min_score: Minimum similarity score

        Returns:
            List of search results with scores
        """
        return self._store.search(
            query=query,
            max_results=max_results,
            min_score=min_score,
        )
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_cwa_integration.py::TestStorePlanEntry -v`
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_cwa_integration.py::TestSearchContext -v`

---

## TDD Cycle: Behavior 6-7 - Build Contexts

### 🔴 Red: Write Failing Tests

**File**: `silmari-rlm-act/tests/test_cwa_integration.py`
```python
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
        """Given too many IDs, respects max limit."""
        cwa = CWAIntegration(max_impl_entries=5)

        entry_ids = []
        for i in range(10):
            entry_ids.append(cwa.store_research(f"doc{i}.md", f"Content {i}", f"Sum {i}"))

        # Should raise or truncate
        with pytest.raises(ValueError):
            cwa.build_impl_context(entry_ids)

    def test_validates_bounds_before_build(self):
        """Given entry IDs, can validate bounds."""
        cwa = CWAIntegration(max_impl_entries=5)

        entry_ids = [cwa.store_research(f"d{i}.md", f"c{i}", f"s{i}") for i in range(3)]

        assert cwa.validate_impl_bounds(entry_ids) is True

        many_ids = [cwa.store_research(f"d{i}.md", f"c{i}", f"s{i}") for i in range(10)]
        assert cwa.validate_impl_bounds(many_ids) is False
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/context/cwa_integration.py`
```python
class CWAIntegration:
    # ... existing code ...

    def build_working_context(self):
        """Build context for working LLM (summaries only).

        Returns:
            WorkingContext with all entries as summaries
        """
        return self._working_ctx.build()

    def build_impl_context(self, entry_ids: list[str]):
        """Build context for implementation LLM (full content).

        Args:
            entry_ids: List of entry IDs to include

        Returns:
            ImplementationContext with full content

        Raises:
            ValueError: If entry count exceeds max_entries
        """
        if not self._impl_ctx.validate_bounds(entry_ids):
            raise ValueError(
                f"Entry count {len(entry_ids)} exceeds max "
                f"{self._impl_ctx.max_entries}"
            )
        return self._impl_ctx.build(entry_ids)

    def validate_impl_bounds(self, entry_ids: list[str]) -> bool:
        """Check if entry IDs fit within implementation limit.

        Args:
            entry_ids: Entry IDs to check

        Returns:
            True if within bounds
        """
        return self._impl_ctx.validate_bounds(entry_ids)
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_cwa_integration.py::TestBuildWorkingContext -v`
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_cwa_integration.py::TestBuildImplementationContext -v`

---

## TDD Cycle: Behavior 8 - Context Manager

### 🔴 Red: Write Failing Test

**File**: `silmari-rlm-act/tests/test_cwa_integration.py`
```python
class TestContextManager:
    """Behavior 8: Context Manager for Entries."""

    def test_request_provides_context(self):
        """Given entry IDs, context manager provides context."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Content", "Summary")

        with cwa.request_entries([id1]) as context:
            assert context.entry_count == 1

    def test_releases_on_exit(self):
        """Given context manager, releases entries after block."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Content", "Summary")

        with cwa.request_entries([id1]) as context:
            pass  # Entries in use

        # After context manager, entries should be released
        # (Implementation may track "in use" status)

    def test_releases_on_exception(self):
        """Given exception in block, still releases entries."""
        cwa = CWAIntegration()

        id1 = cwa.store_research("doc.md", "Content", "Summary")

        try:
            with cwa.request_entries([id1]) as context:
                raise ValueError("Test error")
        except ValueError:
            pass

        # Entries should still be released
```

### 🟢 Green: Implement

**File**: `silmari-rlm-act/context/cwa_integration.py`
```python
from contextlib import contextmanager


class CWAIntegration:
    # ... existing code ...

    @contextmanager
    def request_entries(self, entry_ids: list[str]):
        """Context manager for implementation LLM entries.

        Ensures entries are released even on exceptions.

        Args:
            entry_ids: Entry IDs to request

        Yields:
            ImplementationContext with full content
        """
        with self._impl_ctx.request(entry_ids) as context:
            yield context
```

### Success Criteria
**Automated:**
- [ ] Tests pass: `pytest silmari-rlm-act/tests/test_cwa_integration.py::TestContextManager -v`

---

## TDD Cycle: Behavior 9-15 - Remaining Behaviors

### Condensed Test Specifications

**Behavior 9: Process Turn**
```python
def test_decrements_ttl():
    cwa = CWAIntegration()
    entry_id = cwa.store_requirement("R1", "desc", "sum", ttl=5)

    cwa.process_turn()

    entry = cwa.store.get(entry_id)
    assert entry.ttl == 4

def test_removes_expired():
    cwa = CWAIntegration()
    entry_id = cwa.store_requirement("R1", "desc", "sum", ttl=1)

    cwa.process_turn()

    assert cwa.store.get(entry_id) is None
```

**Behavior 10: Compress Entries**
```python
def test_removes_content_keeps_summary():
    cwa = CWAIntegration()
    entry_id = cwa.store_research("doc.md", "Full content", "Summary")

    cwa.compress_entries([entry_id])

    entry = cwa.store.get(entry_id)
    assert entry.content is None or entry.content == ""
    assert entry.summary == "Summary"
```

**Behavior 11: Get Expiring Soon**
```python
def test_returns_low_ttl_entries():
    cwa = CWAIntegration()
    id1 = cwa.store_requirement("R1", "d1", "s1", ttl=2)
    id2 = cwa.store_requirement("R2", "d2", "s2", ttl=10)

    expiring = cwa.get_expiring_soon(threshold=3)

    assert id1 in [e.id for e in expiring]
    assert id2 not in [e.id for e in expiring]
```

**Behavior 12: Store Command Result**
```python
def test_creates_command_result_entry():
    cwa = CWAIntegration()

    entry_id = cwa.store_command_result(
        command="pytest tests/",
        result="5 passed",
        summary="All tests pass"
    )

    entry = cwa.store.get(entry_id)
    assert entry.entry_type == EntryType.COMMAND_RESULT
```

**Behavior 13-14: Task Batching**
```python
def test_creates_batches_under_limit():
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
```

**Behavior 15: Get by Type**
```python
def test_returns_only_matching_type():
    cwa = CWAIntegration()

    cwa.store_research("doc.md", "content", "summary")  # FILE
    req_id = cwa.store_requirement("R1", "desc", "sum")  # TASK

    tasks = cwa.get_by_type(EntryType.TASK)

    assert len(tasks) == 1
    assert tasks[0].id == req_id
```

---

## Success Criteria

**Automated:**
- [ ] All CWA integration tests pass: `pytest silmari-rlm-act/tests/test_cwa_integration.py -v`
- [ ] Type checking passes: `mypy silmari-rlm-act/context/`

**Manual:**
- [ ] Entries searchable by semantic similarity
- [ ] Implementation context respects <200 entry limit
- [ ] TTL management works correctly
- [ ] Compression preserves summaries

## Summary

This phase implements CWA integration with:
- CentralContextStore initialization
- Entry storage for research, requirements, plans, command results
- Semantic search via VectorSearchIndex
- Working LLM context (summaries only)
- Implementation LLM context (full content, <200 entries)
- Context manager for entry lifecycle
- TTL management and compression
- Task batching for large workloads
