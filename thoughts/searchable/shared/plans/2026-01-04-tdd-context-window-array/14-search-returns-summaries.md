# Phase 14: Search Returns Summaries

## Behavior

Integrate search index with store to return entries with summaries (not full content).

### Test Specification

**Given**: Indexed entries
**When**: search(query)
**Then**: Returns entries with summaries (not full content by default)

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_search.py`

```python
from context_window_array.store import CentralContextStore


class TestSearchReturnsSummaries:
    """Behavior 14: Search returns summaries, not full content."""

    def test_store_search_returns_summary_view(self):
        """Given store with entries, when search(), then returns summary views."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="large_file.py",
            content="def function1(): pass\ndef function2(): pass\n" * 100,  # Large content
            summary="Module with 200 function definitions",
        ))

        results = store.search("function definitions")

        assert len(results) > 0
        result = results[0]
        # Result should have summary, not full content
        assert result.summary == "Module with 200 function definitions"
        assert result.content is None  # Content not included by default

    def test_store_search_can_include_content(self):
        """Given store, when search(include_content=True), then content included."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def test(): pass",
            summary="Test function",
        ))

        results = store.search("test function", include_content=True)

        assert len(results) > 0
        result = results[0]
        assert result.content == "def test(): pass"
        assert result.summary == "Test function"

    def test_store_search_compressed_entry(self):
        """Given compressed entry, when search(), then summary returned."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Compressed file summary",
            compressed=True,
        ))

        results = store.search("compressed file")

        assert len(results) > 0
        result = results[0]
        assert result.summary == "Compressed file summary"
        assert result.content is None
        assert result.compressed is True

    def test_store_search_integrates_with_index(self):
        """Given store with index, when search(), then uses vector search."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="authenticate user login password session",
            summary="Authentication module",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="database postgresql connect query",
            summary="Database module",
        ))

        results = store.search("user authentication login")

        assert len(results) > 0
        # Auth entry should be most relevant
        assert results[0].entry_id == "ctx_001"

    def test_store_search_result_has_all_metadata(self):
        """Given search result, then includes all entry metadata."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary="Test summary",
            references=["ctx_000"],
            parent_id="ctx_000",
        ))

        results = store.search("test")

        assert len(results) > 0
        result = results[0]
        assert result.entry_id == "ctx_001"
        assert result.entry_type == EntryType.FILE
        assert result.source == "test.py"
        assert result.summary == "Test summary"
        assert result.references == ["ctx_000"]
        assert result.parent_id == "ctx_000"
        assert hasattr(result, 'score')

    def test_store_search_respects_searchable_flag(self):
        """Given non-searchable entry, when search(), then not in results."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.COMMAND,
            source="bash",
            content="ls -la",
            summary="List files",
            searchable=False,
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="test.py",
            content="list of items",
            summary="List handler",
            searchable=True,
        ))

        results = store.search("list")

        result_ids = [r.entry_id for r in results]
        assert "ctx_001" not in result_ids
        assert "ctx_002" in result_ids

    def test_store_search_filter_by_type(self):
        """Given mixed entries, when search with type filter, then only matching types."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="code file",
            summary="Code file",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.TASK_RESULT,
            source="orchestrator",
            content="task completed code written",
            summary="Task done",
        ))

        results = store.search("code", entry_types=[EntryType.FILE])

        assert all(r.entry_type == EntryType.FILE for r in results)

    def test_store_expand_search_result(self):
        """Given search result, when expand(id), then get full content."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="Full content here with lots of details",
            summary="Brief summary",
        ))

        # Search returns summary view
        results = store.search("content details")
        assert len(results) > 0
        assert results[0].content is None

        # Expand to get full content
        full_entry = store.get("ctx_001")
        assert full_entry.content == "Full content here with lots of details"

    def test_store_search_max_results(self):
        """Given many entries, when search with max_results, then limited."""
        store = CentralContextStore()
        for i in range(20):
            store.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"python code module {i}",
                summary=f"Module {i}",
            ))

        results = store.search("python module", max_results=5)

        assert len(results) <= 5

    def test_store_search_empty_returns_empty(self):
        """Given store, when search(''), then returns empty list."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="content",
            summary="summary",
        ))

        results = store.search("")

        assert results == []
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_search.py::TestSearchReturnsSummaries -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/search_index.py` (add StoreSearchResult)

```python
@dataclass
class StoreSearchResult:
    """Search result with entry metadata.

    This is the result returned from CentralContextStore.search(),
    containing summary view of entries (not full content by default).
    """
    entry_id: str
    entry_type: EntryType
    source: str
    summary: Optional[str]
    content: Optional[str]  # None by default, populated if include_content=True
    score: float
    references: list[str]
    parent_id: Optional[str]
    compressed: bool
```

**File**: `context_window_array/store.py` (add search integration)

```python
from context_window_array.search_index import VectorSearchIndex, StoreSearchResult


class CentralContextStore:
    def __init__(self):
        """Initialize empty context store."""
        self._entries: dict[str, ContextEntry] = {}
        self._id_counter: int = 0
        self._search_index: VectorSearchIndex = VectorSearchIndex()

    def add(self, entry: ContextEntry) -> str:
        """Add an entry to the store."""
        if entry.id in self._entries:
            raise ValueError(f"Entry with id '{entry.id}' already exists")
        self._entries[entry.id] = entry

        # Index for search if searchable
        if entry.searchable:
            self._search_index.add(entry)

        return entry.id

    def remove(
        self,
        entry_id: str,
        return_entry: bool = False
    ) -> Union[bool, Optional[ContextEntry]]:
        """Remove an entry from the store."""
        if entry_id not in self._entries:
            return None if return_entry else False

        entry = self._entries.pop(entry_id)
        self._search_index.remove(entry_id)
        return entry if return_entry else True

    # ... other existing methods ...

    def search(
        self,
        query: str,
        max_results: int = 10,
        entry_types: Optional[list[EntryType]] = None,
        min_score: float = 0.0,
        include_content: bool = False,
    ) -> list[StoreSearchResult]:
        """Search for entries matching the query.

        Returns summary views of entries by default (not full content).

        Args:
            query: Search query text
            max_results: Maximum number of results
            entry_types: Optional filter by entry types
            min_score: Minimum similarity score
            include_content: If True, include full content in results

        Returns:
            List of StoreSearchResult objects ranked by similarity
        """
        # Use the search index
        index_results = self._search_index.search(
            query=query,
            max_results=max_results,
            entry_types=entry_types,
            min_score=min_score,
        )

        # Convert to StoreSearchResult with entry metadata
        results = []
        for index_result in index_results:
            entry = self._entries.get(index_result.entry_id)
            if entry is None:
                continue

            results.append(StoreSearchResult(
                entry_id=entry.id,
                entry_type=entry.entry_type,
                source=entry.source,
                summary=entry.summary,
                content=entry.content if include_content else None,
                score=index_result.score,
                references=entry.references,
                parent_id=entry.parent_id,
                compressed=entry.compressed,
            ))

        return results
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_search.py::TestSearchReturnsSummaries -v
```

### 🔵 Refactor: Improve Code

Update `__init__.py` exports:

```python
from context_window_array.search_index import VectorSearchIndex, SearchResult, StoreSearchResult

__all__ = [
    "ContextEntry",
    "EntryType",
    "CentralContextStore",
    "VectorSearchIndex",
    "SearchResult",
    "StoreSearchResult",
    "ContextCompressedError",
    "ContextWindowArrayError",
]
```

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): AttributeError or missing search on store
- [ ] Test passes (Green): All 10 tests pass
- [ ] Store.search() returns StoreSearchResult with summaries
- [ ] include_content=True includes full content
- [ ] Compressed entries show summary
- [ ] Non-searchable entries excluded
- [ ] Type filtering works

**Manual:**
- [ ] Search results are memory-efficient (summaries only)
- [ ] Full content retrievable via store.get()
