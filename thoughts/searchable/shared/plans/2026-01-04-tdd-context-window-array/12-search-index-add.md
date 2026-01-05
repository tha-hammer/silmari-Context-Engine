# Phase 12: Search Index Add

## Behavior

Implement vector search index with numpy cosine similarity for adding entries.

### Test Specification

**Given**: Entry with content
**When**: index.add(entry)
**Then**: Entry is searchable

**Given**: Entry with summary only (compressed)
**When**: index.add(entry)
**Then**: Summary is indexed

---

## TDD Cycle

### 🔴 Red: Write Failing Test

**File**: `context_window_array/tests/test_search.py`

```python
"""Tests for context_window_array.search_index module."""

import pytest
import numpy as np
from context_window_array.models import ContextEntry, EntryType
from context_window_array.search_index import VectorSearchIndex


class TestSearchIndexAdd:
    """Behavior 12: Search index add operations."""

    def test_add_entry_with_content(self):
        """Given entry with content, when add(entry), then entry is indexed."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="def hello_world(): print('Hello, World!')",
            summary="Hello world function",
        )

        index.add(entry)

        assert index.contains("ctx_001")
        assert len(index) == 1

    def test_add_entry_with_summary_only(self):
        """Given compressed entry (summary only), when add(entry), then summary indexed."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content=None,
            summary="Hello world function",
            compressed=True,
        )

        index.add(entry)

        assert index.contains("ctx_001")

    def test_add_multiple_entries(self):
        """Given multiple entries, when add each, then all indexed."""
        index = VectorSearchIndex()
        entries = [
            ContextEntry(id="ctx_001", entry_type=EntryType.FILE, source="a.py", content="auth code", summary="auth"),
            ContextEntry(id="ctx_002", entry_type=EntryType.FILE, source="b.py", content="database code", summary="db"),
            ContextEntry(id="ctx_003", entry_type=EntryType.FILE, source="c.py", content="api code", summary="api"),
        ]

        for entry in entries:
            index.add(entry)

        assert len(index) == 3
        assert index.contains("ctx_001")
        assert index.contains("ctx_002")
        assert index.contains("ctx_003")

    def test_add_duplicate_raises_error(self):
        """Given entry already indexed, when add same id, then raises ValueError."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )
        index.add(entry)

        with pytest.raises(ValueError, match="already exists"):
            index.add(entry)

    def test_add_non_searchable_skipped(self):
        """Given entry with searchable=False, when add(entry), then not indexed."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.COMMAND,
            source="bash",
            content="ls -la",
            summary="list files",
            searchable=False,
        )

        index.add(entry)

        # Entry tracked but marked as non-searchable
        assert not index.contains("ctx_001")
        assert len(index) == 0

    def test_add_returns_entry_id(self):
        """Given entry, when add(entry), then returns entry id."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )

        result = index.add(entry)

        assert result == "ctx_001"

    def test_remove_entry(self):
        """Given indexed entry, when remove(id), then no longer searchable."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="test",
            summary="test",
        )
        index.add(entry)
        assert index.contains("ctx_001")

        index.remove("ctx_001")

        assert not index.contains("ctx_001")
        assert len(index) == 0

    def test_remove_nonexistent_is_noop(self):
        """Given nonexistent id, when remove(id), then no error."""
        index = VectorSearchIndex()

        # Should not raise
        index.remove("nonexistent")

    def test_update_entry(self):
        """Given indexed entry, when update(new_entry), then new content indexed."""
        index = VectorSearchIndex()
        entry1 = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="original content",
            summary="original",
        )
        index.add(entry1)

        entry2 = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="updated content about authentication",
            summary="updated",
        )
        index.update(entry2)

        assert index.contains("ctx_001")
        # The vector should be updated (we'll verify via search in later tests)

    def test_get_vector(self):
        """Given indexed entry, when get_vector(id), then returns numpy array."""
        index = VectorSearchIndex()
        entry = ContextEntry(
            id="ctx_001",
            entry_type=EntryType.FILE,
            source="test.py",
            content="machine learning neural network",
            summary="ml code",
        )
        index.add(entry)

        vector = index.get_vector("ctx_001")

        assert isinstance(vector, np.ndarray)
        assert len(vector) > 0

    def test_get_vector_nonexistent_returns_none(self):
        """Given nonexistent id, when get_vector(id), then returns None."""
        index = VectorSearchIndex()

        vector = index.get_vector("nonexistent")

        assert vector is None
```

**Run test (should fail):**
```bash
pytest context_window_array/tests/test_search.py::TestSearchIndexAdd -v
```

### 🟢 Green: Minimal Implementation

**File**: `context_window_array/search_index.py`

```python
"""Vector search index using numpy cosine similarity.

This module provides a simple vector search implementation using
TF-IDF-like term frequency vectors and cosine similarity.
"""

from typing import Optional
import numpy as np
from collections import Counter
import re

from context_window_array.models import ContextEntry


class VectorSearchIndex:
    """Vector search index using TF-IDF and cosine similarity.

    Uses a simple bag-of-words approach with TF-IDF weighting.
    Vectors are computed on-demand for memory efficiency.

    Attributes:
        vocabulary: Set of all terms across indexed documents
        term_to_idx: Mapping from terms to vector indices
        entry_vectors: Dictionary mapping entry IDs to term frequency vectors
    """

    def __init__(self):
        """Initialize empty search index."""
        self._entry_texts: dict[str, str] = {}  # id -> text for indexing
        self._vocabulary: set[str] = set()
        self._term_to_idx: dict[str, int] = {}
        self._vectors: dict[str, np.ndarray] = {}
        self._needs_rebuild: bool = False

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase words."""
        # Simple tokenization: split on non-alphanumeric, lowercase
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
        return words

    def _get_text_for_entry(self, entry: ContextEntry) -> str:
        """Get text to index for an entry."""
        # Prefer content, fall back to summary
        if entry.content:
            return entry.content
        return entry.summary or ""

    def _rebuild_vocabulary(self) -> None:
        """Rebuild vocabulary from all indexed texts."""
        self._vocabulary = set()
        for text in self._entry_texts.values():
            self._vocabulary.update(self._tokenize(text))
        self._term_to_idx = {term: idx for idx, term in enumerate(sorted(self._vocabulary))}
        self._needs_rebuild = False

    def _compute_vector(self, text: str) -> np.ndarray:
        """Compute TF vector for text."""
        if not self._term_to_idx:
            return np.array([])

        tokens = self._tokenize(text)
        counts = Counter(tokens)

        vector = np.zeros(len(self._term_to_idx))
        for term, count in counts.items():
            if term in self._term_to_idx:
                vector[self._term_to_idx[term]] = count

        # Normalize to unit length for cosine similarity
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    def _rebuild_vectors(self) -> None:
        """Rebuild all vectors after vocabulary change."""
        if self._needs_rebuild:
            self._rebuild_vocabulary()

        self._vectors = {}
        for entry_id, text in self._entry_texts.items():
            self._vectors[entry_id] = self._compute_vector(text)

    def add(self, entry: ContextEntry) -> str:
        """Add an entry to the search index.

        Args:
            entry: ContextEntry to index

        Returns:
            Entry ID

        Raises:
            ValueError: If entry with same ID already exists
        """
        if not entry.searchable:
            return entry.id

        if entry.id in self._entry_texts:
            raise ValueError(f"Entry with id '{entry.id}' already exists in index")

        text = self._get_text_for_entry(entry)
        self._entry_texts[entry.id] = text

        # Add new terms to vocabulary
        new_terms = set(self._tokenize(text)) - self._vocabulary
        if new_terms:
            self._vocabulary.update(new_terms)
            self._term_to_idx = {term: idx for idx, term in enumerate(sorted(self._vocabulary))}
            self._needs_rebuild = True

        # Compute vector (will use current vocabulary)
        if not self._needs_rebuild:
            self._vectors[entry.id] = self._compute_vector(text)
        else:
            self._rebuild_vectors()

        return entry.id

    def remove(self, entry_id: str) -> None:
        """Remove an entry from the index.

        Args:
            entry_id: ID of entry to remove
        """
        if entry_id in self._entry_texts:
            del self._entry_texts[entry_id]
        if entry_id in self._vectors:
            del self._vectors[entry_id]

    def update(self, entry: ContextEntry) -> None:
        """Update an entry in the index.

        Args:
            entry: Updated entry
        """
        self.remove(entry.id)
        if entry.searchable:
            # Re-add (will handle duplicate check correctly since we removed first)
            text = self._get_text_for_entry(entry)
            self._entry_texts[entry.id] = text

            new_terms = set(self._tokenize(text)) - self._vocabulary
            if new_terms:
                self._vocabulary.update(new_terms)
                self._term_to_idx = {term: idx for idx, term in enumerate(sorted(self._vocabulary))}
                self._rebuild_vectors()
            else:
                self._vectors[entry.id] = self._compute_vector(text)

    def contains(self, entry_id: str) -> bool:
        """Check if entry is indexed.

        Args:
            entry_id: ID to check

        Returns:
            True if entry is in index
        """
        return entry_id in self._entry_texts

    def get_vector(self, entry_id: str) -> Optional[np.ndarray]:
        """Get the vector for an entry.

        Args:
            entry_id: ID of entry

        Returns:
            Numpy array vector, or None if not found
        """
        return self._vectors.get(entry_id)

    def __len__(self) -> int:
        """Return number of indexed entries."""
        return len(self._entry_texts)
```

**Run test (should pass):**
```bash
pytest context_window_array/tests/test_search.py::TestSearchIndexAdd -v
```

### 🔵 Refactor: Improve Code

Consider lazy vector computation for memory efficiency with large indices.

---

## Success Criteria

**Automated:**
- [ ] Test fails for right reason (Red): ImportError for VectorSearchIndex
- [ ] Test passes (Green): All 11 tests pass
- [ ] `add()` indexes entry content or summary
- [ ] `add()` skips non-searchable entries
- [ ] `remove()` removes from index
- [ ] `update()` updates vector
- [ ] `get_vector()` returns numpy array

**Manual:**
- [ ] Tokenization handles code-like text
- [ ] Vocabulary grows incrementally
