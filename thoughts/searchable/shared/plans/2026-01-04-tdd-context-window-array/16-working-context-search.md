# Phase 16: Working Context Search Integration

## Behavior

Integrate search capabilities into working LLM context for semantic retrieval.

### Test Specification

**Given**: Working context with store
**When**: search(query)
**Then**: Returns relevant entries ranked by similarity

**Given**: Working context
**When**: search(query, max_results=5)
**Then**: Returns at most 5 entries

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_working_context.py`

```python
class TestWorkingContextSearch:
    """Behavior 16: Working context search integration."""

    def test_search_returns_relevant_entries(self):
        """Given store with entries, when search(query), then returns relevant entries."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="authenticate user login password session token",
            summary="User authentication module",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="database postgresql connect query",
            summary="Database connection module",
        ))
        store.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.FILE,
            source="api.py",
            content="http request handler endpoint",
            summary="API handler",
        ))

        context = WorkingLLMContext(store)
        results = context.search("user authentication login")

        assert len(results) > 0
        # Auth module should be most relevant
        assert results[0].id == "ctx_001"

    def test_search_returns_summary_views(self):
        """Given search results, then they are summary views (no content)."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="full content here",
            summary="Test summary",
        ))

        context = WorkingLLMContext(store)
        results = context.search("test")

        assert len(results) > 0
        assert results[0].content is None
        assert results[0].summary == "Test summary"

    def test_search_max_results(self):
        """Given many entries, when search(query, max_results=3), then at most 3 returned."""
        store = CentralContextStore()
        for i in range(10):
            store.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"python code module {i}",
                summary=f"Module {i}",
            ))

        context = WorkingLLMContext(store)
        results = context.search("python module", max_results=3)

        assert len(results) <= 3

    def test_search_with_type_filter(self):
        """Given mixed entries, when search with entry_types filter, then only those types."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="python code",
            summary="Python file",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.TASK,
            source="orchestrator",
            content="task about python",
            summary="Python task",
        ))

        context = WorkingLLMContext(store)
        results = context.search("python", entry_types=[EntryType.FILE])

        assert all(r.entry_type == EntryType.FILE for r in results)

    def test_search_empty_query_returns_empty(self):
        """Given working context, when search(''), then returns empty list."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="content",
            summary="summary",
        ))

        context = WorkingLLMContext(store)
        results = context.search("")

        assert results == []

    def test_search_results_have_score(self):
        """Given search results, then each has a similarity score."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="python code",
            summary="Python file",
        ))

        context = WorkingLLMContext(store)
        results = context.search("python")

        assert len(results) > 0
        assert hasattr(results[0], 'score')
        assert 0 <= results[0].score <= 1

    def test_search_with_min_score(self):
        """Given entries, when search with min_score, then only high scores returned."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="exact.py",
            content="exact match python code",
            summary="Exact match",
        ))
        store.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="unrelated.py",
            content="cooking recipes food",
            summary="Cooking",
        ))

        context = WorkingLLMContext(store)
        results = context.search("python code", min_score=0.3)

        assert all(r.score >= 0.3 for r in results)

    def test_search_results_include_metadata(self):
        """Given search results, then include all entry metadata."""
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

        context = WorkingLLMContext(store)
        results = context.search("test")

        assert len(results) > 0
        result = results[0]
        assert result.id == "ctx_001"
        assert result.entry_type == EntryType.FILE
        assert result.source == "test.py"
        assert result.references == ["ctx_000"]
        assert result.parent_id == "ctx_000"

    def test_search_compressed_entries(self):
        """Given compressed entries, when search, then searchable by summary."""
        store = CentralContextStore()
        store.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,  # Compressed
            summary="Python testing utilities and helpers",
            compressed=True,
        ))

        context = WorkingLLMContext(store)
        results = context.search("python testing")

        assert len(results) > 0
        assert results[0].id == "ctx_001"
        assert results[0].compressed is True
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_working_context.py::TestWorkingContextSearch -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/working_context.py` (add search method)

```python
@dataclass
class SearchResultView:
    """Search result for working LLM context.

    Contains summary view plus similarity score.
    """
    id: str
    entry_type: EntryType
    source: str
    summary: Optional[str]
    content: None = None  # Always None for working context
    score: float = 0.0
    references: list[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    compressed: bool = False


class WorkingLLMContext:
    # ... existing __init__ and build methods ...

    def search(
        self,
        query: str,
        max_results: int = 10,
        entry_types: Optional[list[EntryType]] = None,
        min_score: float = 0.0,
    ) -> list[SearchResultView]:
        """Search for relevant entries.

        Returns summary views ranked by similarity.

        Args:
            query: Search query text
            max_results: Maximum number of results
            entry_types: Optional filter by entry types
            min_score: Minimum similarity score

        Returns:
            List of SearchResultView ranked by similarity
        """
        if not query or not query.strip():
            return []

        # Use store's search method
        store_results = self._store.search(
            query=query,
            max_results=max_results,
            entry_types=entry_types,
            min_score=min_score,
            include_content=False,  # Never include content for working LLM
        )

        # Convert to SearchResultView
        return [
            SearchResultView(
                id=r.entry_id,
                entry_type=r.entry_type,
                source=r.source,
                summary=r.summary,
                content=None,
                score=r.score,
                references=r.references,
                parent_id=r.parent_id,
                compressed=r.compressed,
            )
            for r in store_results
        ]
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_working_context.py::TestWorkingContextSearch -v
```

### 🔵 Refactor: Improve Code

Consider caching search results for repeated queries.

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): AttributeError for search method
- [ ] Test passes (Green): All 9 tests pass
- [ ] `search()` returns relevant entries
- [ ] `search()` respects max_results
- [ ] `search()` filters by entry type
- [ ] `search()` filters by min_score
- [ ] Results are SearchResultView (no content)
- [ ] Compressed entries searchable by summary

**Manual:**
- [ ] Search results useful for orchestration decisions
- [ ] Performance acceptable for large stores
