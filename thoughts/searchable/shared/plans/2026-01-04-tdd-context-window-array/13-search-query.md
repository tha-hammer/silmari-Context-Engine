# Phase 13: Search Query

## Behavior

Implement search query using cosine similarity to find relevant entries.

### Test Specification

**Given**: Indexed entries
**When**: search(query)
**Then**: Returns relevant entries ranked by similarity

**Given**: Indexed entries
**When**: search(query, max_results=5)
**Then**: Returns at most 5 entries

**Given**: Indexed entries
**When**: search(query, entry_types=["file"])
**Then**: Returns only file entries

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_search.py`

```python
class TestSearchQuery:
    """Behavior 13: Search query operations."""

    def test_search_finds_relevant_entry(self):
        """Given indexed entries, when search(query), then finds relevant entry."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="def authenticate_user(username, password): verify credentials and return token",
            summary="User authentication",
        ))
        index.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="db.py",
            content="def connect_database(): establish connection to postgresql",
            summary="Database connection",
        ))
        index.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.FILE,
            source="api.py",
            content="def handle_request(): process incoming http request",
            summary="API handler",
        ))

        results = index.search("authenticate user login password")

        assert len(results) > 0
        # auth.py should be most relevant
        assert results[0].entry_id == "ctx_001"

    def test_search_returns_ranked_results(self):
        """Given indexed entries, when search(query), then results ranked by similarity."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="a.py",
            content="machine learning neural network deep learning",
            summary="ML code",
        ))
        index.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="b.py",
            content="simple function hello world",
            summary="Hello",
        ))
        index.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.FILE,
            source="c.py",
            content="machine learning model training",
            summary="ML training",
        ))

        results = index.search("machine learning")

        # Both ML entries should be in top results
        top_ids = [r.entry_id for r in results[:2]]
        assert "ctx_001" in top_ids
        assert "ctx_003" in top_ids

    def test_search_max_results(self):
        """Given many entries, when search(query, max_results=2), then returns at most 2."""
        index = VectorSearchIndex()
        for i in range(10):
            index.add(ContextEntry(
                id=f"ctx_{i:03d}",
                entry_type=EntryType.FILE,
                source=f"file{i}.py",
                content=f"python code function {i}",
                summary=f"Code {i}",
            ))

        results = index.search("python code", max_results=2)

        assert len(results) <= 2

    def test_search_empty_query_returns_empty(self):
        """Given indexed entries, when search(''), then returns empty list."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary="test",
        ))

        results = index.search("")

        assert results == []

    def test_search_no_matches_returns_empty(self):
        """Given indexed entries, when search(unrelated query), then returns empty or low scores."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="auth.py",
            content="authentication login password",
            summary="Auth",
        ))

        results = index.search("quantum physics thermodynamics")

        # Should return empty or very low similarity results
        assert len(results) == 0 or all(r.score < 0.1 for r in results)

    def test_search_result_has_score(self):
        """Given search results, then each result has a similarity score."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="python programming code",
            summary="Code",
        ))

        results = index.search("python code")

        assert len(results) > 0
        assert hasattr(results[0], 'score')
        assert 0 <= results[0].score <= 1

    def test_search_result_has_entry_id(self):
        """Given search results, then each result has entry_id."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test content",
            summary="test",
        ))

        results = index.search("test")

        assert len(results) > 0
        assert results[0].entry_id == "ctx_001"

    def test_search_filter_by_entry_type(self):
        """Given mixed entries, when search with entry_types filter, then only those types returned."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="python code file",
            summary="Python file",
        ))
        index.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.COMMAND_RESULT,
            source="bash",
            content="python script output",
            summary="Command output",
        ))
        index.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.FILE,
            source="test2.py",
            content="more python code",
            summary="More Python",
        ))

        # Need to store entry types for filtering
        results = index.search("python", entry_types=[EntryType.FILE])

        assert all(r.entry_type == EntryType.FILE for r in results)
        assert len(results) == 2

    def test_search_filter_multiple_types(self):
        """Given mixed entries, when search with multiple entry_types, then all matching types returned."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="code file",
            summary="File",
        ))
        index.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.COMMAND_RESULT,
            source="bash",
            content="command output",
            summary="Output",
        ))
        index.add(ContextEntry(
            id="ctx_003",
            entry_type=EntryType.TASK,
            source="orchestrator",
            content="task description",
            summary="Task",
        ))

        results = index.search("code output task", entry_types=[EntryType.FILE, EntryType.COMMAND_RESULT])

        result_types = {r.entry_type for r in results}
        assert EntryType.TASK not in result_types

    def test_search_with_threshold(self):
        """Given indexed entries, when search with min_score threshold, then only high scores returned."""
        index = VectorSearchIndex()
        index.add(ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="exact match python programming",
            summary="Exact",
        ))
        index.add(ContextEntry(
            id="ctx_002",
            entry_type=EntryType.FILE,
            source="other.py",
            content="unrelated content about cooking recipes",
            summary="Cooking",
        ))

        results = index.search("python programming", min_score=0.3)

        # Should only return the relevant entry
        assert all(r.score >= 0.3 for r in results)

    def test_search_empty_index_returns_empty(self):
        """Given empty index, when search(query), then returns empty list."""
        index = VectorSearchIndex()

        results = index.search("any query")

        assert results == []
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_search.py::TestSearchQuery -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/search_index.py` (add search result dataclass and search method)

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchResult:
    """Result from a search query.

    Attributes:
        entry_id: ID of the matching entry
        score: Cosine similarity score (0-1)
        entry_type: Type of the entry (for filtering)
    """
    entry_id: str
    score: float
    entry_type: EntryType


class VectorSearchIndex:
    def __init__(self):
        """Initialize empty search index."""
        self._entry_texts: dict[str, str] = {}
        self._entry_types: dict[str, EntryType] = {}  # Track entry types for filtering
        self._vocabulary: set[str] = set()
        self._term_to_idx: dict[str, int] = {}
        self._vectors: dict[str, np.ndarray] = {}
        self._needs_rebuild: bool = False

    # ... existing methods (update add() to store entry_type) ...

    def add(self, entry: ContextEntry) -> str:
        """Add an entry to the search index."""
        if not entry.searchable:
            return entry.id

        if entry.id in self._entry_texts:
            raise ValueError(f"Entry with id '{entry.id}' already exists in index")

        text = self._get_text_for_entry(entry)
        self._entry_texts[entry.id] = text
        self._entry_types[entry.id] = entry.entry_type  # Store type

        # Add new terms to vocabulary
        new_terms = set(self._tokenize(text)) - self._vocabulary
        if new_terms:
            self._vocabulary.update(new_terms)
            self._term_to_idx = {term: idx for idx, term in enumerate(sorted(self._vocabulary))}
            self._needs_rebuild = True

        if not self._needs_rebuild:
            self._vectors[entry.id] = self._compute_vector(text)
        else:
            self._rebuild_vectors()

        return entry.id

    def remove(self, entry_id: str) -> None:
        """Remove an entry from the index."""
        if entry_id in self._entry_texts:
            del self._entry_texts[entry_id]
        if entry_id in self._entry_types:
            del self._entry_types[entry_id]
        if entry_id in self._vectors:
            del self._vectors[entry_id]

    def search(
        self,
        query: str,
        max_results: int = 10,
        entry_types: Optional[list[EntryType]] = None,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        """Search for entries matching the query.

        Args:
            query: Search query text
            max_results: Maximum number of results to return
            entry_types: Optional list of entry types to filter by
            min_score: Minimum similarity score (0-1)

        Returns:
            List of SearchResult objects ranked by similarity score
        """
        if not query or not query.strip():
            return []

        if not self._vectors:
            return []

        # Ensure vectors are up to date
        if self._needs_rebuild:
            self._rebuild_vectors()

        # Compute query vector
        query_vector = self._compute_vector(query)
        if np.linalg.norm(query_vector) == 0:
            return []

        # Compute similarities
        results = []
        for entry_id, entry_vector in self._vectors.items():
            # Filter by entry type if specified
            if entry_types and self._entry_types.get(entry_id) not in entry_types:
                continue

            # Cosine similarity (vectors are already normalized)
            similarity = float(np.dot(query_vector, entry_vector))

            if similarity >= min_score:
                results.append(SearchResult(
                    entry_id=entry_id,
                    score=similarity,
                    entry_type=self._entry_types[entry_id],
                ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)

        # Limit results
        return results[:max_results]
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_search.py::TestSearchQuery -v
```

### 🔵 Refactor: Improve Code

Consider adding IDF weighting for better relevance scoring.

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): AttributeError for search
- [ ] Test passes (Green): All 11 tests pass
- [ ] `search()` returns ranked results by similarity
- [ ] `search()` respects max_results
- [ ] `search()` filters by entry_types
- [ ] `search()` filters by min_score
- [ ] SearchResult contains entry_id, score, entry_type

**Manual:**
- [ ] Relevant entries appear first in results
- [ ] Similarity scores are reasonable (0-1 range)
