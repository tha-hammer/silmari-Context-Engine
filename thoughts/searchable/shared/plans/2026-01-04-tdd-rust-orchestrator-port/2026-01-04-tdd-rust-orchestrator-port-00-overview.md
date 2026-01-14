# Rust Orchestrator Port - Phase Overview

## Project Summary

Port the TypeScript orchestrator to Rust, implementing a complete, production-ready session orchestration system with incremental testable behaviors.

**Source**: `silmari-oracle-wui/src/orchestrator/orchestrator.ts`
**Target**: `silmari-oracle/src/orchestrator.rs`

## Implementation Phases

Each phase implements one human-testable behavior. Phases build incrementally on previous work.

### Phase 1: Session Initialization
**File**: [2026-01-04-tdd-rust-orchestrator-port-01-phase-1.md](./2026-01-04-tdd-rust-orchestrator-port-01-phase-1.md)
**Human-Testable Function**: `initialize_session()`
**What It Does**: Creates unique sessions with timestamps and validates workspace paths
**Dependencies**: None
**Blocks**: Phase 2

### Phase 2: State Persistence
**File**: [2026-01-04-tdd-rust-orchestrator-port-02-phase-2.md](./2026-01-04-tdd-rust-orchestrator-port-02-phase-2.md)
**Human-Testable Function**: `persist_to_database()` and `persist_to_cache()`
**What It Does**: Saves session state to memory cache and SQLite database
**Dependencies**: Phase 1
**Blocks**: Phase 3, Phase 8

### Phase 3: Context Building
**File**: [2026-01-04-tdd-rust-orchestrator-port-03-phase-3.md](./2026-01-04-tdd-rust-orchestrator-port-03-phase-3.md)
**Human-Testable Function**: `build_context()`
**What It Does**: Aggregates workspace files, thoughts, git info, and project metadata into context
**Dependencies**: Phase 2, Phase 4, Phase 5, Phase 6, Phase 7
**Blocks**: Phase 8

### Phase 4: Active File Tracking
**File**: [2026-01-04-tdd-rust-orchestrator-port-04-phase-4.md](./2026-01-04-tdd-rust-orchestrator-port-04-phase-4.md)
**Human-Testable Function**: `track_active_files()`
**What It Does**: Reads file contents, excludes binaries, truncates large files
**Dependencies**: None
**Blocks**: Phase 3

### Phase 5: Thought Retrieval
**File**: [2026-01-04-tdd-rust-orchestrator-port-05-phase-5.md](./2026-01-04-tdd-rust-orchestrator-port-05-phase-5.md)
**Human-Testable Function**: `retrieve_thoughts()`
**What It Does**: Finds and categorizes thought documents from thoughts/ directory
**Dependencies**: None
**Blocks**: Phase 3

### Phase 6: Git Information
**File**: [2026-01-04-tdd-rust-orchestrator-port-06-phase-6.md](./2026-01-04-tdd-rust-orchestrator-port-06-phase-6.md)
**Human-Testable Function**: `get_git_info()`
**What It Does**: Extracts git branch, status, commits, and remote tracking info
**Dependencies**: None
**Blocks**: Phase 3

### Phase 7: Project Metadata
**File**: [2026-01-04-tdd-rust-orchestrator-port-07-phase-7.md](./2026-01-04-tdd-rust-orchestrator-port-07-phase-7.md)
**Human-Testable Function**: `extract_project_metadata()`
**What It Does**: Detects project type, name, build system, and dependencies
**Dependencies**: None
**Blocks**: Phase 3

### Phase 8: Session Deduplication
**File**: [2026-01-04-tdd-rust-orchestrator-port-08-phase-8.md](./2026-01-04-tdd-rust-orchestrator-port-08-phase-8.md)
**Human-Testable Function**: `deduplicate_sessions()`
**What It Does**: Identifies duplicate sessions by context hash, generates human-readable names
**Dependencies**: Phase 2, Phase 3
**Blocks**: None

## Dependency Graph

```
Phase 1 (Session Init)
   └─> Phase 2 (State Persistence)
          ├─> Phase 3 (Context Building) ──> Phase 8 (Deduplication)
          └─> Phase 8 (Deduplication)

Phase 4 (Active Files) ──> Phase 3 (Context Building)
Phase 5 (Thoughts) ──────> Phase 3 (Context Building)
Phase 6 (Git Info) ──────> Phase 3 (Context Building)
Phase 7 (Metadata) ──────> Phase 3 (Context Building)
```

## Recommended Implementation Order

1. **Phase 1**: Session Initialization (foundation)
2. **Phase 2**: State Persistence (enables session storage)
3. **Phase 4**: Active File Tracking (independent, feeds into Phase 3)
4. **Phase 5**: Thought Retrieval (independent, feeds into Phase 3)
5. **Phase 6**: Git Information (independent, feeds into Phase 3)
6. **Phase 7**: Project Metadata (independent, feeds into Phase 3)
7. **Phase 3**: Context Building (combines Phase 4-7)
8. **Phase 8**: Session Deduplication (final integration)

## Testing Strategy

- **Framework**: Rust built-in test framework
- **Location**: `silmari-oracle/src/orchestrator.rs` (unit tests in `mod tests`)
- **Integration**: `silmari-oracle/tests/orchestrator_integration.rs`
- **Fixtures**: `silmari-oracle/tests/fixtures/`

## Success Criteria

All 8 phases complete with:
- ✅ All unit tests passing (`cargo test --lib orchestrator::tests`)
- ✅ All integration tests passing (`cargo test --test orchestrator_integration`)
- ✅ Clippy clean (`cargo clippy -- -D warnings`)
- ✅ Formatted (`cargo fmt -- --check`)
- ✅ Each human-testable function verified manually

## Key Files Modified

- `silmari-oracle/src/orchestrator.rs` - Main implementation
- `silmari-oracle/Cargo.toml` - Dependencies (rusqlite, git2, uuid, etc.)
- `silmari-oracle/tests/orchestrator_integration.rs` - Integration tests

## What We're NOT Doing

- UI components or web server integration
- Database schema changes (use existing TypeScript schema)
- Complete API parity with every TypeScript method
- Performance optimization beyond basic best practices
- Comprehensive error recovery strategies
