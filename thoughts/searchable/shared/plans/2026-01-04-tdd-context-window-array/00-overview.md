# Context Window Array Architecture - TDD Implementation Plan

**Epic**: `silmari-Context-Engine-jhxw`

## Overview

This plan implements the **Hierarchical Context Array Architecture** for separating working and implementation LLMs with addressable context. Based on research synthesizing RLM (Recursive Language Models) and CodeAct patterns.

**Source Research**: `thoughts/searchable/shared/research/2026-01-04-context-window-array-architecture.md`

## Goals

1. Create addressable context entries with unique IDs
2. Implement central store with CRUD, search, and compression
3. Separate working LLM context (summaries only) from implementation LLM context (full content)
4. Enable command/result separation (remove commands, retain results)
5. Enforce <200 entry bounds for implementation contexts
6. Support TTL-based entry expiration

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CENTRAL CONTEXT STORE                                │
│  entries: Dict[str, ContextEntry]                                           │
│  search_index: VectorSearchIndex (numpy cosine similarity)                  │
│                                                                             │
│  Operations: add(), get(), remove(), search(), compress(), expand()         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│     WORKING LLM CONTEXT         │  │   IMPLEMENTATION LLM CONTEXT    │
│  - Summaries only               │  │   - Full content                │
│  - Task index                   │  │   - Bounded to <200 entries     │
│  - Search interface             │  │   - Scoped to single task       │
└─────────────────────────────────┘  └─────────────────────────────────┘
```

## Project Structure (Isolated from Existing Code)

```
context_window_array/
├── __init__.py
├── models.py                   # ContextEntry, EntryType enum
├── store.py                    # CentralContextStore
├── search_index.py             # VectorSearchIndex (numpy cosine)
├── working_context.py          # WorkingLLMContext
├── implementation_context.py   # ImplementationLLMContext
├── batching.py                 # Task batching utilities
├── exceptions.py               # Custom exceptions
└── tests/
    ├── __init__.py
    ├── conftest.py             # Shared fixtures
    ├── test_models.py          # Phases 01-06
    ├── test_store.py           # Phases 07-11
    ├── test_search.py          # Phases 12-14
    ├── test_working_context.py # Phases 15-16
    ├── test_implementation_context.py  # Phases 17-19
    └── test_batching.py        # Phases 20-21
```

## Dependencies

- Python 3.12+
- numpy (for cosine similarity)
- pytest (testing)
- hypothesis (property-based testing)

No imports from existing `planning_pipeline/` code.

## Implementation Phases

| Phase | Behavior | File | Test File | Beads ID | Status |
|-------|----------|------|-----------|----------|--------|
| 01 | EntryType Enum | models.py | test_models.py | `9e1g` | **DONE** |
| 02 | ContextEntry Creation | models.py | test_models.py | `vl1r` | **DONE** |
| 03 | ContextEntry Validation | models.py | test_models.py | `2xqn` | **DONE** |
| 04 | ContextEntry Serialization | models.py | test_models.py | `9wdr` | **DONE** |
| 05 | ContextEntry TTL | models.py | test_models.py | `nj1n` | |
| 06 | ContextEntry Compression | models.py | test_models.py | `tj49` | |
| 07 | Store Add/Get | store.py | test_store.py | `pzi4` | |
| 08 | Store Remove | store.py | test_store.py | `nb09` | |
| 09 | Store Compression | store.py | test_store.py | `i5i2` | |
| 10 | Command/Result Separation | store.py | test_store.py | `gvee` | |
| 11 | Store TTL Processing | store.py | test_store.py | `43cq` | |
| 12 | Search Index Add | search_index.py | test_search.py | `xjv5` | |
| 13 | Search Query | search_index.py | test_search.py | `cym8` | |
| 14 | Search Returns Summaries | search_index.py | test_search.py | `qji6` | |
| 15 | Working Context Build | working_context.py | test_working_context.py | `emwg` | |
| 16 | Working Context Search | working_context.py | test_working_context.py | `h2eo` | |
| 17 | Implementation Context Build | implementation_context.py | test_implementation_context.py | `nw9t` | |
| 18 | Entry Bounds Validation | implementation_context.py | test_implementation_context.py | `2dd4` | |
| 19 | Context Request | implementation_context.py | test_implementation_context.py | `2m3r` | |
| 20 | Batch Creation | batching.py | test_batching.py | `27rc` | |
| 21 | Batch Execution | batching.py | test_batching.py | `hnr9` | |

> **Note**: Beads IDs are short-form. Full ID format: `silmari-Context-Engine-{id}`
> Use `bd show {id}` to view details, `bd update {id} --status=in_progress` to claim work.

## Test Commands

```bash
# Run all tests
pytest context_window_array/tests/ -v

# Run specific phase
pytest context_window_array/tests/test_models.py -v -k "test_entry_type"

# Run with coverage
pytest context_window_array/tests/ --cov=context_window_array --cov-report=term-missing

# Skip slow tests
pytest context_window_array/tests/ -v -m "not slow"
```

## Success Criteria

**Automated:**
- [ ] All 21 phases have passing tests
- [ ] 100% test coverage on core modules
- [ ] Property-based tests for serialization round-trips
- [ ] Type checking passes (mypy)

**Manual:**
- [ ] Working LLM context contains only summaries
- [ ] Implementation LLM context bounded to <200 entries
- [ ] Commands can be removed while results retained
- [ ] Search returns relevant entries by semantic similarity

## References

- Research: `thoughts/searchable/shared/research/2026-01-04-context-window-array-architecture.md`
- RLM Paper: https://alexzhang13.github.io/blog/2025/rlm/
- CodeAct Paper: https://arxiv.org/abs/2402.01030
- Existing patterns: `planning_pipeline/models.py` (for dataclass patterns)
