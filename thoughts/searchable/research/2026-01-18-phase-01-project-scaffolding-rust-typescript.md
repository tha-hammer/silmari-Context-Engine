---
date: "2026-01-18T15:05:13-05:00"
researcher: "Claude (Opus 4.5)"
git_commit: "7997182a465d44a14109826b7d931278f8c56590"
branch: "cli-wrapper-restore"
repository: "tha-hammer/silmari-Context-Engine"
topic: "Phase 1 Project Scaffolding - Rust for FileOps and TypeScript for LLMOps"
tags: [research, codebase, rust, typescript, architecture, phase-01, silmari-chain-map]
status: complete
last_updated: "2026-01-18"
last_updated_by: "Claude (Opus 4.5)"
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   PHASE 1 PROJECT SCAFFOLDING RESEARCH                                     │
│   Rust for FileOps, TypeScript for LLMOps Architecture Review              │
│                                                                             │
│   Status: COMPLETE                                                          │
│   Date: 2026-01-18                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Phase 1 Project Scaffolding - Rust for FileOps and TypeScript for LLMOps

**Date**: 2026-01-18T15:05:13-05:00  
**Researcher**: Claude (Opus 4.5)  
**Git Commit**: 7997182a465d44a14109826b7d931278f8c56590  
**Branch**: cli-wrapper-restore  
**Repository**: tha-hammer/silmari-Context-Engine

## 📚 Research Question

Review the Phase 1 Project Scaffolding plan and analyze how to split responsibilities between **Rust for FileOps** and **TypeScript for LLMOps** in the context of the Staged Context Pipeline with Function Chain Map implementation.

## 📊 Summary

The Phase 1 plan (`thoughts/searchable/plans/2026-01-18-phase-01-project-scaffolding.md`) currently specifies a **TypeScript-only** implementation for the `silmari-chain-map` module. The user's request to use **Rust for FileOps** and **TypeScript for LLMOps** represents an architectural evolution that splits the workload between:

| Layer | Language | Responsibilities |
|-------|----------|------------------|
| **FileOps** | Rust | AST parsing (tree-sitter), file I/O, hashing, git operations, SQLite database |
| **LLMOps** | TypeScript | Haiku annotation service, DO annotation generation, CWA integration |

This split aligns with the plan's **Deterministic/Stochastic Split** philosophy - Rust handles all deterministic operations while TypeScript manages the stochastic LLM interactions.

---

## 🎯 Detailed Findings

### 📁 Current Codebase Structure

The existing codebase uses multiple languages:

| Language | Location | Purpose |
|----------|----------|---------|
| **Python** | `silmari_rlm_act/`, `planning_pipeline/`, `context_window_array/` | Main CLI, pipeline orchestration, CWA store |
| **Go** | `go/` (67 files) | Context engine CLI, planning pipeline, execution utilities |
| **TypeScript** | None currently | Planned for `silmari-chain-map` |
| **Rust** | None currently | Proposed for FileOps |

### 📋 What Phase 1 Currently Specifies

The plan defines a TypeScript-only `silmari-chain-map/` module with:

```
silmari-chain-map/
├── package.json
├── tsconfig.json
├── db/
│   └── schema.sql
└── src/
    ├── model/
    │   ├── types.ts      # Core types: NodeId, ChainId, contracts
    │   ├── node.ts       # FunctionNode interface
    │   ├── chain.ts      # Chain interface
    │   └── chain-map.ts  # ChainMap class (in-memory operations)
    └── db/
        ├── connection.ts # SQLite connection manager
        └── repository.ts # ChainMapRepository for persistence
```

**Key Components**:

1. **Data Models** (`src/model/types.ts`):
   - `NodeId`, `ChainId`, `BodyHash`, `GitCommit` type aliases
   - `InContract`, `OutContract`, `DoAnnotation` interfaces
   - Error classes: `ParseError`, `AnnotationError`, `DatabaseError`

2. **FunctionNode** (`src/model/node.ts`):
   - Represents a function with IN:DO:OUT contracts
   - Contains: id, name, file, line/byte ranges, contracts, calls array, body hash

3. **Chain** (`src/model/chain.ts`):
   - Represents an operation's data flow
   - Contains: entry node, all node IDs, trace metadata

4. **ChainMap** (`src/model/chain-map.ts`):
   - Central data structure with reverse index for invalidation
   - Methods: add/get nodes, add/get chains, invalidation, queries

5. **Repository** (`src/db/repository.ts`):
   - SQLite persistence layer
   - Load/save full ChainMap or individual nodes/chains

---

### 🦀 Proposed Rust FileOps Layer

Based on the plan's deterministic/stochastic split, Rust should handle:

| Component | Current Plan Location | Rust Responsibility |
|-----------|----------------------|---------------------|
| Tree-sitter parsing | Phase 2: `src/parser/tree-sitter.ts` | AST parsing, function extraction |
| Function extraction | Phase 2: `src/parser/extractor.ts` | Extract IN/OUT contracts, call sites |
| Call graph building | Phase 2: `src/parser/call-graph.ts` | Build edges, trace chains (BFS) |
| Body hashing | Phase 2: `hashBody()` | SHA256[:16] of function bodies |
| Git diff | Phase 4: `src/git/diff.ts` | File change detection, invalidation |
| SQLite operations | Phase 1: `src/db/` | All database I/O |
| File I/O | Various phases | Read source files, write cache |

**Rust FileOps Crate Structure**:

```
silmari-chain-map-core/
├── Cargo.toml
├── src/
│   ├── lib.rs
│   ├── models/
│   │   ├── mod.rs
│   │   ├── node.rs       # FunctionNode struct
│   │   ├── chain.rs      # Chain struct
│   │   └── types.rs      # NodeId, BodyHash, contracts
│   ├── parser/
│   │   ├── mod.rs
│   │   ├── tree_sitter.rs # tree-sitter bindings
│   │   ├── extractor.rs   # Function extraction
│   │   └── call_graph.rs  # Call graph construction
│   ├── db/
│   │   ├── mod.rs
│   │   ├── connection.rs  # SQLite with rusqlite
│   │   └── repository.rs  # CRUD operations
│   └── git/
│       ├── mod.rs
│       └── diff.rs        # Git diff parsing
```

**Key Rust Crates**:

| Crate | Purpose |
|-------|---------|
| `tree-sitter` | AST parsing |
| `tree-sitter-typescript` | TypeScript grammar |
| `rusqlite` | SQLite database |
| `sha2` | Body hashing |
| `git2` or shell exec | Git operations |
| `napi-rs` | Node.js bindings for TypeScript interop |

---

### 📘 TypeScript LLMOps Layer

TypeScript handles all stochastic (LLM) operations:

| Component | Plan Location | TypeScript Responsibility |
|-----------|---------------|---------------------------|
| Haiku client | Phase 3: `src/annotator/haiku-client.ts` | Claude API calls |
| Annotation cache | Phase 3: `src/annotator/cache.ts` | Cache lookup/store (via Rust FFI) |
| Batch annotator | Phase 3: `src/annotator/batch.ts` | Parallel annotation, progress |
| Context pipeline | Phase 5: `src/pipeline/` | 4-stage Trace/Review/Revise/Generate |
| CWA integration | Phase 6: `src/cwa/` | Sync with CWA Central Context Store |
| CLI | Phase 7: `src/cli/` | Commander.js commands |

**TypeScript LLMOps Structure**:

```
silmari-chain-map/
├── package.json
├── tsconfig.json
└── src/
    ├── index.ts          # Main exports
    ├── native/
    │   └── bindings.ts   # Rust bindings via napi-rs
    ├── annotator/
    │   ├── provider.ts   # AnnotationProvider interface
    │   ├── haiku-client.ts # Claude Haiku client
    │   ├── cache.ts      # Uses Rust DB via bindings
    │   └── batch.ts      # Collect-Then-Apply pattern
    ├── pipeline/
    │   ├── trace.ts      # Stage 1: uses Rust chain tracer
    │   ├── review.ts     # Stage 2: contract validation
    │   ├── revise.ts     # Stage 3: gap filling
    │   └── generate.ts   # Stage 4: context construction
    ├── cwa/
    │   └── sync.ts       # CWA integration
    └── cli/
        └── index.ts      # Commander.js CLI
```

---

### 🔗 Rust-TypeScript Integration Pattern

The plan's architecture naturally supports a **Rust core with TypeScript wrapper** pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                    TypeScript (LLMOps)                       │
│  • Haiku annotation                                          │
│  • Batch processing with progress                            │
│  • CLI commands                                              │
│  • CWA sync                                                  │
├─────────────────────────────────────────────────────────────┤
│                    napi-rs Bindings                          │
│  • Exposes Rust functions to Node.js                        │
│  • Zero-copy where possible                                  │
├─────────────────────────────────────────────────────────────┤
│                    Rust (FileOps)                            │
│  • Tree-sitter parsing                                       │
│  • Function extraction                                       │
│  • SQLite operations                                         │
│  • Git diff detection                                        │
│  • Chain tracing (BFS)                                      │
└─────────────────────────────────────────────────────────────┘
```

**Integration Points**:

| Rust Exports | TypeScript Calls |
|--------------|------------------|
| `parse_file(path)` → `ExtractedFunction[]` | Before annotation |
| `load_chain_map()` → `ChainMap` | On CLI startup |
| `save_node(node)` | After annotation |
| `trace_chain(entry)` → `NodeId[]` | Pipeline Stage 1 |
| `get_changed_files(commit)` → `string[]` | Invalidation |
| `hash_body(body)` → `BodyHash` | Cache key generation |

---

### 📊 Alignment with Plan Phases

| Phase | Current Plan | With Rust/TS Split |
|-------|--------------|-------------------|
| **Phase 1** | TypeScript data models + SQLite schema | Rust: models, schema, repository. TS: type definitions (mirrors) |
| **Phase 2** | TypeScript tree-sitter | Rust: all parsing + extraction |
| **Phase 3** | TypeScript Haiku + cache | TS: Haiku client, batch. Rust: cache storage |
| **Phase 4** | TypeScript git diff | Rust: git diff parsing |
| **Phase 5** | TypeScript pipeline | TS: pipeline orchestration. Rust: trace/data fetching |
| **Phase 6** | TypeScript CWA sync | TS: CWA integration (existing Python CWA) |
| **Phase 7** | TypeScript CLI | TS: CLI commands calling Rust core |

---

### 🏗️ Existing Go Infrastructure

The codebase has significant Go infrastructure in `go/internal/`:

| Module | Files | Purpose |
|--------|-------|---------|
| `cli/` | 11 files | CLI root, flags, subcommands |
| `planning/` | 25 files | Pipeline, steps, decomposition, Claude runner |
| `exec/` | 9 files | Runner, git, beads, buildtools |
| `concurrent/` | 7 files | Rate limiting, signal handling, worker pools |
| `models/` | 3 files | Context entry, entry types |
| `fs/` | 3 files | Path utilities, time handling |
| `jsonutil/` | 2 files | JSON helpers |

The Go code provides:
- Full planning pipeline (`internal/planning/pipeline.go`)
- Claude execution (`internal/exec/claude.go`)
- Git operations (`internal/exec/git.go`)
- Beads issue tracking (`internal/exec/beads.go`)

**Consideration**: The Rust FileOps layer could potentially integrate with or replace parts of the Go infrastructure for file operations, while maintaining the Go CLI as-is for the existing pipeline.

---

### 📋 SQLite Schema (From Plan)

The Phase 1 schema in `db/schema.sql`:

```sql
-- Function Nodes
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,           -- "file::name::startByte"
    name TEXT NOT NULL,
    file TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    start_byte INTEGER NOT NULL,
    end_byte INTEGER NOT NULL,
    in_contract_json TEXT NOT NULL,
    out_contract_json TEXT NOT NULL,
    do_annotation_json TEXT,       -- nullable until annotated
    calls_json TEXT NOT NULL DEFAULT '[]',
    body_hash TEXT NOT NULL,
    last_valid_commit TEXT NOT NULL,
    is_stale INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Chains
CREATE TABLE chains (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    entry_node_id TEXT NOT NULL,
    traced_at_commit TEXT NOT NULL,
    traced_at TEXT NOT NULL,
    is_stale INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (entry_node_id) REFERENCES nodes(id)
);

-- Chain-Node Junction
CREATE TABLE chain_nodes (
    chain_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    PRIMARY KEY (chain_id, node_id)
);

-- DO Annotation Cache
CREATE TABLE do_cache (
    body_hash TEXT PRIMARY KEY,
    annotation_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Migrations tracking
CREATE TABLE migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT NOT NULL
);

-- Metadata
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

This schema is fully compatible with Rust's `rusqlite` crate.

---

## 🔗 Code References

- Phase 1 Plan: `thoughts/searchable/plans/2026-01-18-phase-01-project-scaffolding.md`
- Phase 2 Plan: `thoughts/searchable/plans/2026-01-18-phase-02-tree-sitter.md`
- Phase 3 Plan: `thoughts/searchable/plans/2026-01-18-phase-03-do-annotation.md`
- Main Plan: `thoughts/searchable/plans/2026-01-18-staged-context-pipeline-function-chain-map.md`
- Go Pipeline: `go/internal/planning/pipeline.go`
- Go CLI Entry: `go/cmd/context-engine/main.go`
- Python CWA: `context_window_array/`

---

## 🏛️ Architecture Documentation

### Current Implementation Languages

```
silmari-Context-Engine/
├── Python (Primary)
│   ├── silmari_rlm_act/     # Main RLM-Act CLI
│   ├── planning_pipeline/    # Planning orchestration
│   └── context_window_array/ # CWA store
├── Go (Secondary)
│   └── go/                   # Context engine, planning pipeline
└── Planned
    ├── Rust (FileOps)        # silmari-chain-map-core
    └── TypeScript (LLMOps)   # silmari-chain-map
```

### Deterministic/Stochastic Boundary

The plan explicitly defines this boundary:

```
DETERMINISTIC (Rust)           STOCHASTIC (TypeScript)
─────────────────────          ──────────────────────
• File → AST → Functions       • Function body → DO annotation
• Signature → IN contract      • Haiku API calls
• Return type → OUT contract   • Parallel execution
• Call sites → Edge graph      • Progress reporting
• Git diff → Invalidation      • Fallback handling
• Body hash → Cache key        • Rate limit management
```

---

## 📜 Historical Context (from thoughts/)

| Document | Insight |
|----------|---------|
| `thoughts/searchable/plans/2026-01-18-staged-context-pipeline-function-chain-map.md` | Master plan defining 7 phases, 4-stage pipeline, IN:DO:OUT contracts |
| `thoughts/searchable/plans/2026-01-18-staged-context-pipeline-function-chain-map-REVIEW.md` | Review addressing critical issues (persistence, race conditions) |
| `thoughts/searchable/research/2026-01-18-cwa-central-context-store.md` | CWA integration research |

---

## 🔗 Related Research

- `thoughts/searchable/research/2026-01-18-cwa-central-context-store.md` - CWA Central Context Store research

---

## ❓ Open Questions

| Question | Context |
|----------|---------|
| **napi-rs vs N-API directly?** | napi-rs is more ergonomic but adds build complexity |
| **Monorepo structure?** | Should Rust crate and TS package be in same directory or separate? |
| **Go interop?** | Should Rust replace Go file ops or coexist? |
| **Build pipeline?** | How to coordinate Rust build with npm install? |
| **Cross-platform binaries?** | Need to compile Rust for multiple platforms |

---

## ✅ Recommendations Summary

| Aspect | Recommendation |
|--------|----------------|
| **Rust crate name** | `silmari-chain-map-core` |
| **TS package name** | `silmari-chain-map` |
| **Integration method** | napi-rs for Node.js bindings |
| **Build tool** | Cargo for Rust, npm for TS, coordinated via Makefile or just |
| **Location** | New directory at repo root: `silmari-chain-map/` containing both |

This architecture provides:
- **Performance**: Rust for CPU-intensive parsing/hashing
- **Safety**: Rust memory safety for file operations
- **Ergonomics**: TypeScript for LLM integration (rich Anthropic SDK)
- **Maintainability**: Clear separation of concerns
