# Plan Review Report: Staged Context Pipeline - Function Chain Map

## Review Summary

| Category | Status | Issues Found |
|----------|--------|--------------|
| Contracts | ⚠️ | 7 issues |
| Interfaces | ⚠️ | 5 issues |
| Promises | ⚠️ | 6 issues |
| Data Models | ⚠️ | 4 issues |
| APIs | ⚠️ | 3 issues |

---

## Contract Review

### Well-Defined:

- ✅ **InContract** - Clear parameter structure with name, type, optional flag, and description
- ✅ **OutContract** - Return type, error types, and async status documented
- ✅ **DoAnnotation** - Well-specified action, side effects, and error conditions
- ✅ **FunctionNode** - Complete field definitions with types
- ✅ **Chain** - Clear entry point and node set semantics
- ✅ **SQLite schema** - Tables have appropriate constraints and foreign keys

### Missing or Unclear:

1. ⚠️ **Missing error contract for `extractFunctions`** (Phase 2)
   - What happens when tree-sitter fails to parse malformed TypeScript?
   - No try/catch or error type specified in the extractor
   - **Impact**: Unhandled parsing errors will crash the pipeline

2. ⚠️ **Missing contract for `HaikuAnnotator.annotate` failures** (Phase 3)
   - What happens on API rate limiting?
   - What happens on network timeout?
   - What happens on invalid response format?
   - **Impact**: Batch annotation will fail ungracefully

3. ⚠️ **Incomplete error contract for `DbConnection`** (Phase 1)
   - No specification for database lock errors (SQLite busy)
   - No specification for disk space exhaustion
   - **Impact**: Production failures won't be handled gracefully

4. ⚠️ **Missing contract boundary between `traceOperation` and `ChainMap`** (Phase 5)
   - How does tracing communicate with the persistent ChainMap?
   - Who owns the nodes—TraceResult or ChainMap?
   - **Impact**: Confusion about state ownership

5. ❌ **No contract for concurrent access to ChainMap** (Phase 1)
   - Plan shows parallel Haiku calls in Phase 3
   - ChainMap uses JavaScript Maps without synchronization
   - **Impact**: Race conditions when parallel annotators update nodes

6. ⚠️ **Missing preconditions for `checkAndInvalidate`** (Phase 4)
   - What if `lastCommit` is an invalid commit SHA?
   - What if `projectPath` doesn't exist?
   - **Impact**: Unclear failure modes

7. ⚠️ **No invariant specified for reverse index consistency** (Phase 1)
   - `nodeToChains` Map must stay in sync with `chains` Map
   - No guarantee this invariant is maintained on node deletion
   - **Impact**: Stale reverse index entries

### Recommendations:

```typescript
// Add explicit error types to src/model/types.ts
export class ParseError extends Error {
  constructor(public file: string, public message: string) {
    super(`Failed to parse ${file}: ${message}`);
  }
}

export class AnnotationError extends Error {
  constructor(
    public bodyHash: BodyHash,
    public cause: 'rate_limit' | 'timeout' | 'parse_error' | 'api_error',
    message: string
  ) {
    super(message);
  }
}

export class DatabaseError extends Error {
  constructor(
    public cause: 'locked' | 'disk_full' | 'corruption',
    message: string
  ) {
    super(message);
  }
}
```

---

## Interface Review

### Well-Defined:

- ✅ **ChainMap class** - Complete public interface with add/get/invalidate operations
- ✅ **AnnotationCache class** - CRUD operations clearly specified
- ✅ **CLI commands** - All subcommands documented with options
- ✅ **WorkingContext interface** - Clear structure for LLM consumption

### Missing or Unclear:

1. ⚠️ **No interface for pluggable annotation providers** (Phase 3)
   - HaikuAnnotator is tightly coupled to Anthropic SDK
   - No abstraction for swapping to local models or other providers
   - **Impact**: Vendor lock-in, harder to test

2. ⚠️ **Missing `ChainMap.serialize()`/`deserialize()` interface** (Phase 1)
   - Plan shows SQLite persistence but ChainMap is in-memory
   - No clear interface for persistence layer
   - **Impact**: Data loss between CLI invocations

3. ❌ **Inconsistent with existing CWA patterns** (Phase 6)
   - CWA uses `ContextEntry` with `EntryType` enum
   - Plan defines `CWAChainEntry` with `entryType: 'CHAIN_MAP'`
   - Should extend existing `EntryType` enum instead of string literal
   - **Impact**: Integration friction with existing CWA code

4. ⚠️ **Missing progress/event interface for pipeline** (Phase 5)
   - Batch annotator has `ProgressCallback`
   - Full pipeline (Trace→Review→Revise→Generate) has no progress interface
   - **Impact**: CLI will appear frozen during long operations

5. ⚠️ **No interface for configuration** (All phases)
   - Database path, concurrency, API keys scattered as function parameters
   - No central configuration object
   - **Impact**: Inconsistent configuration handling

### Recommendations:

```typescript
// Add annotation provider interface
interface AnnotationProvider {
  annotate(body: string, bodyHash: BodyHash): Promise<DoAnnotation>;
  batchAnnotate(items: Array<{body: string; hash: BodyHash}>): Promise<Map<BodyHash, DoAnnotation>>;
}

// Extend existing CWA EntryType (in context_window_array/models.py)
class EntryType(Enum):
    # ... existing types ...
    CHAIN_MAP = "chain_map"  # New type for function chain maps

// Add configuration interface
interface ChainMapConfig {
  dbPath: string;
  projectPath: string;
  annotationConcurrency: number;
  apiKey?: string;
  cacheEnabled: boolean;
}
```

---

## Promise Review

### Well-Defined:

- ✅ **Body hash caching** - Promise to cache indefinitely until body changes
- ✅ **BFS traversal** - Guarantees no infinite loops in recursive calls
- ✅ **Staleness propagation** - Promise to mark all affected chains stale

### Missing or Unclear:

1. ⚠️ **No timeout handling for Haiku API calls** (Phase 3)
   - `HaikuAnnotator.annotate` has no timeout parameter
   - Network calls can hang indefinitely
   - **Impact**: Pipeline hangs on slow/unresponsive API

2. ⚠️ **No cancellation support** (All phases)
   - Long-running operations (annotation, tracing) cannot be cancelled
   - No AbortController integration
   - **Impact**: User must kill process to abort

3. ❌ **No idempotency guarantee for `invalidateNode`** (Phase 1)
   - Calling invalidateNode twice returns different results (first call returns affected chains, second returns empty)
   - **Impact**: Retry logic will behave unexpectedly

4. ⚠️ **No ordering guarantee for parallel annotations** (Phase 3)
   - BatchAnnotator processes in parallel chunks
   - Order of completion is non-deterministic
   - **Impact**: Progress callbacks may report out of order

5. ⚠️ **Missing resource cleanup guarantees** (Phase 1, 7)
   - `DbConnection` has `close()` but no RAII pattern
   - What happens if CLI crashes mid-operation?
   - **Impact**: Database locks may persist

6. ⚠️ **Revision loop termination not guaranteed** (Phase 5)
   - `shouldContinueRevision` has maxIterations=5
   - But `determineRevisions` can add infinite "expand_scope" actions
   - **Impact**: Could loop forever in edge cases

### Recommendations:

```typescript
// Add timeout to Haiku client
async annotate(body: string, bodyHash: BodyHash, timeoutMs: number = 30000): Promise<DoAnnotation> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await this.client.messages.create({
      // ...
    }, { signal: controller.signal });
    // ...
  } finally {
    clearTimeout(timeoutId);
  }
}

// Add idempotent invalidation
invalidateNode(nodeId: NodeId): {affectedChains: ChainId[], wasAlreadyStale: boolean} {
  const node = this.nodes.get(nodeId);
  const wasAlreadyStale = node?.isStale ?? false;
  // ...
  return { affectedChains, wasAlreadyStale };
}
```

---

## Data Model Review

### Well-Defined:

- ✅ **NodeId format** - Clear specification: "file/path.ts::functionName::startByte"
- ✅ **BodyHash format** - SHA256 truncated to 16 characters
- ✅ **FunctionNode** - All required fields with types
- ✅ **SQLite schema** - Proper normalization with junction table

### Missing or Unclear:

1. ⚠️ **No migration strategy for schema evolution** (Phase 1)
   - Schema has version metadata but no migration scripts
   - What happens when schema changes between versions?
   - **Impact**: Data loss on upgrade

2. ⚠️ **Inconsistent JSON serialization strategy** (Phase 1)
   - SQLite schema uses `*_json` columns for complex types
   - No validation that JSON matches expected TypeScript types
   - **Impact**: Runtime type errors on corrupt data

3. ❌ **ChainMap in-memory vs SQLite mismatch** (Phase 1)
   - `ChainMap` class is purely in-memory with JavaScript Sets/Maps
   - SQLite schema is defined but no DAO/Repository layer
   - **Impact**: No persistence—all data lost on restart

4. ⚠️ **Missing indexes for common queries** (Phase 1)
   - No index on `nodes.name` (needed for entry point lookup)
   - No composite index on `chain_nodes` for both directions
   - **Impact**: Poor query performance at scale

### Recommendations:

```sql
-- Add migration table
CREATE TABLE IF NOT EXISTS migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT
);

-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_chain_nodes_chain ON chain_nodes(chain_id);
```

```typescript
// Add DAO layer between ChainMap and SQLite
class ChainMapRepository {
  constructor(private db: DbConnection) {}

  loadAll(): ChainMap { /* ... */ }
  save(chainMap: ChainMap): void { /* ... */ }
  saveNode(node: FunctionNode): void { /* ... */ }
  saveChain(chain: Chain): void { /* ... */ }
}
```

---

## API Review

### Well-Defined:

- ✅ **CLI command structure** - Clear subcommands with options
- ✅ **Output formats** - JSON and markdown for `build-context`
- ✅ **Progress callbacks** - Defined for batch annotation

### Missing or Unclear:

1. ⚠️ **No programmatic API for embedding** (All phases)
   - Module is CLI-only
   - No exported functions for use as a library
   - **Impact**: Cannot integrate into other tools without CLI subprocess

2. ⚠️ **Missing exit codes for CLI** (Phase 7)
   - No specification of exit codes for different error conditions
   - Scripts cannot distinguish failure types
   - **Impact**: Poor automation support

3. ⚠️ **No version/compatibility checking** (Phase 6)
   - CWA integration doesn't check CWA version
   - No protocol version in CWAChainEntry
   - **Impact**: Silent failures on incompatible CWA versions

### Recommendations:

```typescript
// Export programmatic API
export { ChainMap } from './model/chain-map.js';
export { traceOperation, type TraceResult } from './pipeline/trace.js';
export { generateWorkingContext, type WorkingContext } from './pipeline/generate.js';
export { HaikuAnnotator } from './annotator/haiku-client.js';

// Define exit codes
export const EXIT_CODES = {
  SUCCESS: 0,
  INVALID_ARGS: 1,
  DATABASE_ERROR: 2,
  PARSE_ERROR: 3,
  API_ERROR: 4,
  VALIDATION_ERROR: 5,
} as const;

// Add protocol version
interface CWAChainEntry {
  protocolVersion: 1;  // Increment on breaking changes
  entryType: 'CHAIN_MAP';
  // ...
}
```

---

## Critical Issues (Must Address Before Implementation)

### 1. **No Persistence Layer** (CRITICAL)

**Description**: ChainMap is purely in-memory but the plan expects data to persist across CLI invocations. SQLite schema is defined but never connected to ChainMap.

**Impact**:
- `chain-map trace` will create a chain
- Closing CLI loses all data
- `chain-map build-context` will fail (no chains exist)

**Recommendation**: Add ChainMapRepository class that loads/saves ChainMap to SQLite. Every CLI command should:
1. Load ChainMap from SQLite
2. Perform operation
3. Save ChainMap back to SQLite

### 2. **CWA Integration Type Mismatch** (CRITICAL)

**Description**: Plan defines `CWAChainEntry` with `entryType: 'CHAIN_MAP'` as a string, but existing CWA uses `EntryType` enum with `from_string()` validation that will reject unknown types.

**Impact**: `chain-map sync-cwa` will fail at runtime with `ValueError: Invalid entry type 'CHAIN_MAP'`

**Recommendation**: 
- (A) Add `CHAIN_MAP = "chain_map"` to `context_window_array/models.py:EntryType` enum

### 3. **Concurrent Annotation Race Condition** (HIGH)

**Description**: BatchAnnotator runs parallel Haiku calls (concurrency=10) and updates ChainMap. JavaScript is single-threaded but the async updates interleave unpredictably.

**Impact**: If two annotations complete for functions in the same chain, reverse index updates may be lost.

**Recommendation**: Use the Collect-Then-Apply pattern—run parallel API calls without mutations, then apply all ChainMap updates in a synchronous block. This leverages JavaScript's single-threaded event loop to guarantee race-free updates without additional concurrency primitives.

---

## Suggested Plan Amendments

### Phase 1 Amendments:

```diff
+ Add: ChainMapRepository class for SQLite persistence
+ Add: Error type definitions (ParseError, AnnotationError, DatabaseError)
+ Add: Migration table and version checking
~ Modify: ChainMap to use repository for persistence
```

### Phase 3 Amendments:

```diff
+ Add: Timeout parameter to HaikuAnnotator (default 30s)
+ Add: AnnotationProvider interface for pluggability
+ Add: Collect-Then-Apply pattern documentation (parallel fetch, synchronous apply)
~ Modify: BatchAnnotator to handle rate limiting with exponential backoff
```

### Phase 5 Amendments:

```diff
+ Add: PipelineProgress callback interface
+ Add: AbortController support for cancellation
+ Add: Maximum expansion limit to prevent infinite revision loops
```

### Phase 6 Amendments:

```diff
+ Add: CHAIN_MAP to existing EntryType enum in CWA
+ Add: Protocol version field to CWAChainEntry
~ Modify: CWASync to validate CWA version compatibility
```

### Phase 7 Amendments:

```diff
+ Add: Programmatic API exports for library usage
+ Add: Exit code constants
+ Add: --verbose flag for debugging
+ Add: --quiet flag for scripting
```

---

## Approval Status

- [ ] **Ready for Implementation** - No critical issues
- [x] **Needs Major Revision** - Critical issues must be resolved first:
  1. Add persistence layer (ChainMapRepository)
  2. Fix CWA EntryType integration
  3. Add concurrency safety to batch annotation

---

## Next Steps

1. Address the 3 critical issues listed above
2. Update plan with error type definitions
3. Add timeout/cancellation support specification
4. Clarify ChainMap ↔ SQLite persistence strategy
5. Re-review after amendments

---

*Review conducted: 2026-01-18*
*Plan location: `thoughts/searchable/plans/2026-01-18-staged-context-pipeline-function-chain-map.md`*
