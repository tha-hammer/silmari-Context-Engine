# Staged Context Pipeline - Function Chain Map Implementation Plan

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   STAGED CONTEXT PIPELINE WITH FUNCTION CHAIN MAP                          │
│   Four-Layer Memory Architecture Implementation                             │
│                                                                             │
│   Status: REVISED (Post-Review)                                             │
│   Date: 2026-01-18                                                          │
│   Module: silmari-chain-map (new)                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📚 Overview

This plan implements a **Staged Context Pipeline** with a **Function Chain Map** to address LLM performance degradation as codebases grow. The core insight: more context ≠ better understanding—noise degrades output quality.

**The Solution**: Separate retrieval from reasoning from generation through a 4-stage pipeline:

| Stage | Purpose | Output |
|-------|---------|--------|
| **1. Trace** | Map end-to-end data flow | Function chain skeleton |
| **2. Review** | Validate contracts, detect gaps | Gap/inconsistency list |
| **3. Revise** | Expand scope if gaps found | Updated chain |
| **4. Generate** | Build curated working context | Focused context for LLM |

**Key Innovation**: The Function Chain Map provides **contract-annotated dataflow graphs** where each function node has:
- **IN**: Input contracts (parameters, types)
- **DO**: Semantic description (what it does, side effects, errors)
- **OUT**: Output contracts (return types, thrown errors)

## 📊 Current State Analysis

### Existing Infrastructure

| Component | Location | Reusability |
|-----------|----------|-------------|
| Tree-sitter AST | `silmari-code-eval/src/utils/tree_sitter_analyzer.py` | 🟢 Port to TypeScript |
| Gate 4 IN:DO:OUT | `silmari-code-eval/src/tree_sitter_gate4.py` | 🟢 Pattern reference |
| Function hashing | `silmari-code-eval/src/database/function_hash.py` | 🟢 Algorithm reference |
| CWA Store | `silmari-Context-Engine/context_window_array/` | 🟢 Direct integration |
| Git diff wrapper | `silmari-Context-Engine/go/internal/exec/git.go` | 🟡 Partial reference |

### Key Discoveries

| Finding | File Reference | Impact |
|---------|----------------|--------|
| Gate 4 already extracts IN:DO:OUT patterns | `tree_sitter_gate4.py:59-80` | Can model after this |
| CWA has 21 phases complete, 235 tests | `plans/2026-01-04-tdd-context-window-array/` | Stable foundation |
| Function body hashing uses SHA256[:12] | `function_hash.py:9-55` | Adopt same approach |
| No git-triggered invalidation exists | N/A | Must build from scratch |

### Architecture Gap

```
CURRENT STATE:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Raw Files  │────▶│  LLM Call   │────▶│   Output    │
└─────────────┘     └─────────────┘     └─────────────┘
     ↑                    ↑
     │                    │
  Too much            Noise degrades
  context             quality

DESIRED STATE:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Raw Files  │────▶│ Chain Map   │────▶│  Staged     │────▶│  Curated    │
│             │     │ (IN:DO:OUT) │     │  Pipeline   │     │  Context    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     ↑                    ↑                   ↑                   ↑
     │                    │                   │                   │
  Deterministic      Cached DO           Validated           Focused
  AST parsing        annotations         contracts           for LLM
```

## 🎯 Desired End State

After this plan is complete:

1. **A new `silmari-chain-map` TypeScript module exists** that can:
   - Parse TypeScript files and extract function definitions with IN/OUT contracts
   - Generate DO annotations using Haiku (cached by body hash)
   - Build function chain maps from entry points to leaf functions
   - Detect file changes via git diff and invalidate stale nodes
   - Execute the 4-stage context pipeline
   - Sync chain maps with CWA Central Context Store

2. **CLI commands are available**:
   ```bash
   chain-map init                    # Initialize SQLite DB
   chain-map trace <entry-point>     # Build chain from entry
   chain-map annotate [--parallel]   # Generate DO annotations
   chain-map invalidate              # Check git diff, mark stale
   chain-map build-context <task>    # Run 4-stage pipeline
   chain-map sync-cwa                # Push to CWA store
   ```

3. **Performance targets**:
   - Initial annotation: <5 minutes for 1000 functions
   - Incremental annotation: <10 seconds for 10 changed functions
   - Context build: <2 seconds for typical operation chain

### Verification

**Automated**:
- [ ] All unit tests pass: `npm test`
- [ ] Type checking passes: `npm run typecheck`
- [ ] Linting passes: `npm run lint`
- [ ] Integration tests pass with sample codebase

**Manual**:
- [ ] Trace a real function chain in Agent SDK codebase
- [ ] Verify DO annotations are accurate and useful
- [ ] Confirm git changes trigger correct invalidation
- [ ] Test 4-stage pipeline produces focused context

## 🚫 What We're NOT Doing

| Out of Scope | Why | What We ARE Doing |
|--------------|-----|-------------------|
| Multi-language support | Focus on Agent SDK (TypeScript) | TypeScript-only initially |
| rlm_act integration | Build standalone first | Export interface for later integration |
| Embedding-based search | Adds complexity | Keyword/path-based chain queries |
| Real-time file watching | Not needed for CLI tool | Git diff on-demand |
| Web UI | CLI-first approach | CLI commands only |
| Python port | TypeScript is target | TypeScript implementation |

## ⚠️ Critical Issues Addressed (From Review)

This plan has been revised to address the following critical issues identified during review:

| Issue | Severity | Resolution |
|-------|----------|------------|
| **No Persistence Layer** | 🔴 CRITICAL | Added `ChainMapRepository` class in Phase 1 |
| **CWA EntryType Mismatch** | 🔴 CRITICAL | Extended existing `EntryType` enum in Phase 6 |
| **Concurrent Annotation Race** | 🟠 HIGH | Added Collect-Then-Apply pattern in Phase 3 |
| **Missing Error Types** | 🟡 MEDIUM | Added `ParseError`, `AnnotationError`, `DatabaseError` in Phase 1 |
| **No Timeout Handling** | 🟡 MEDIUM | Added timeout + AbortController in Phase 3 |
| **No Migration Strategy** | 🟡 MEDIUM | Added migrations table in Phase 1 |
| **No Programmatic API** | 🟡 MEDIUM | Added exports in Phase 7 |

## 🚀 Implementation Approach

### Deterministic/Stochastic Split

```
┌─────────────────────────────────────────────────────────────┐
│                    DETERMINISTIC                            │
│  (tree-sitter, git diff, hashing, caching)                 │
├─────────────────────────────────────────────────────────────┤
│  • File → AST → Function nodes                             │
│  • Function signature → IN contract                        │
│  • Return type → OUT contract                              │
│  • Call sites → Edge graph                                 │
│  • Git diff → Invalidation set                             │
│  • Body hash → Cache key                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    STOCHASTIC (sandboxed)                   │
│  (Haiku, single function, cached indefinitely)             │
├─────────────────────────────────────────────────────────────┤
│  • Function body → DO annotation                           │
│  • Run once, cache until body changes                      │
│  • Parallel execution for throughput                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    DETERMINISTIC                            │
│  (chain assembly, context construction)                    │
├─────────────────────────────────────────────────────────────┤
│  • Nodes + DO → Complete chain map                         │
│  • Query → Relevant chains                                 │
│  • 4-stage pipeline → Curated context                      │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | TypeScript | Agent SDK compatibility |
| AST Parser | tree-sitter + tree-sitter-typescript | Fast, deterministic, mature |
| DO Model | Claude Haiku | Fast ($0.25/1M), accurate for code |
| Database | SQLite (better-sqlite3) | Embedded, no server, fast |
| CWA Integration | Direct import from silmari-Context-Engine | Shared context store |
| CLI | Commander.js | Standard Node CLI framework |

---

╔═════════════════════════════════════════════════════════════════════════════╗
║                              PHASE 1                                         ║
║                    Project Scaffolding & Data Model                          ║
╚═════════════════════════════════════════════════════════════════════════════╝

## Phase 1: Project Scaffolding & Data Model

### Overview

Set up the TypeScript project structure, define core data models, and create the SQLite schema. This phase establishes the foundation for all subsequent phases.

### Changes Required

#### 1. Project Initialization

**Directory**: `silmari-chain-map/`

```bash
mkdir silmari-chain-map && cd silmari-chain-map
npm init -y
npm install typescript @types/node better-sqlite3 @types/better-sqlite3
npm install -D vitest tsx
npx tsc --init
```

**File**: `package.json`
```json
{
  "name": "silmari-chain-map",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest",
    "typecheck": "tsc --noEmit",
    "lint": "eslint src/",
    "cli": "tsx src/cli/index.ts"
  },
  "dependencies": {
    "better-sqlite3": "^9.4.0",
    "@anthropic-ai/sdk": "^0.20.0",
    "tree-sitter": "^0.21.0",
    "tree-sitter-typescript": "^0.21.0",
    "commander": "^12.0.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "@types/node": "^20.0.0",
    "@types/better-sqlite3": "^7.6.0",
    "vitest": "^1.4.0",
    "tsx": "^4.7.0",
    "eslint": "^8.57.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0"
  }
}
```

**File**: `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

#### 2. Core Data Models

**File**: `src/model/types.ts`
```typescript
// ─────────────────────────────────────────────────────────────
// Error Types (Added from Review)
// ─────────────────────────────────────────────────────────────

/**
 * Error during AST parsing.
 */
export class ParseError extends Error {
  constructor(
    public file: string,
    public cause: 'syntax_error' | 'file_not_found' | 'encoding_error',
    message: string
  ) {
    super(`Failed to parse ${file}: ${message}`);
    this.name = 'ParseError';
  }
}

/**
 * Error during DO annotation.
 */
export class AnnotationError extends Error {
  constructor(
    public bodyHash: string,
    public cause: 'rate_limit' | 'timeout' | 'parse_error' | 'api_error' | 'network_error',
    message: string
  ) {
    super(message);
    this.name = 'AnnotationError';
  }
}

/**
 * Error during database operations.
 */
export class DatabaseError extends Error {
  constructor(
    public cause: 'locked' | 'disk_full' | 'corruption' | 'migration_failed',
    message: string
  ) {
    super(message);
    this.name = 'DatabaseError';
  }
}

// ─────────────────────────────────────────────────────────────
// Core Types
// ─────────────────────────────────────────────────────────────

/**
 * Unique identifier for a function node.
 * Format: "file/path.ts::functionName::startByte"
 */
export type NodeId = string;

/**
 * Unique identifier for a chain.
 * Format: "operation_name" (e.g., "user_login", "process_payment")
 */
export type ChainId = string;

/**
 * Git commit SHA for staleness tracking.
 */
export type GitCommit = string;

/**
 * Hash of function body for cache keying.
 * SHA256 truncated to 16 characters.
 */
export type BodyHash = string;

/**
 * Contract for function input parameters.
 */
export interface InContract {
  parameters: Array<{
    name: string;
    type: string;
    optional: boolean;
    description?: string;
  }>;
  /** Raw signature string for display */
  signature: string;
}

/**
 * Contract for function output.
 */
export interface OutContract {
  returnType: string;
  /** Possible error types thrown */
  errorTypes: string[];
  /** Whether the function is async */
  isAsync: boolean;
}

/**
 * Semantic description of what a function does.
 * Generated by Haiku, cached by body hash.
 */
export interface DoAnnotation {
  /** Primary action (1 sentence) */
  action: string;
  /** Side effects (DB writes, network calls, logging) */
  sideEffects: string[];
  /** Error conditions that cause exceptions/failures */
  errorConditions: string[];
  /** Cached at this body hash */
  bodyHash: BodyHash;
  /** When this annotation was generated */
  annotatedAt: Date;
}
```

**File**: `src/model/node.ts`
```typescript
import type { NodeId, BodyHash, GitCommit, InContract, OutContract, DoAnnotation } from './types.js';

/**
 * A function node in the chain map.
 * Represents a single function with its contracts.
 */
export interface FunctionNode {
  /** Unique identifier */
  id: NodeId;

  /** Function name */
  name: string;

  /** Source file path (relative to project root) */
  file: string;

  /** Line range in source file */
  startLine: number;
  endLine: number;

  /** Byte range for precise extraction */
  startByte: number;
  endByte: number;

  /** Input contract (deterministic from AST) */
  inContract: InContract;

  /** Output contract (deterministic from AST) */
  outContract: OutContract;

  /** Semantic description (stochastic, cached) */
  doAnnotation: DoAnnotation | null;

  /** Functions this node calls */
  calls: NodeId[];

  /** Hash of function body for cache keying */
  bodyHash: BodyHash;

  /** Git commit when last validated */
  lastValidCommit: GitCommit;

  /** Whether this node needs re-annotation */
  isStale: boolean;
}

/**
 * Create a node ID from components.
 */
export function createNodeId(file: string, name: string, startByte: number): NodeId {
  return `${file}::${name}::${startByte}`;
}

/**
 * Parse a node ID into components.
 */
export function parseNodeId(id: NodeId): { file: string; name: string; startByte: number } {
  const parts = id.split('::');
  return {
    file: parts[0],
    name: parts[1],
    startByte: parseInt(parts[2], 10),
  };
}
```

**File**: `src/model/chain.ts`
```typescript
import type { ChainId, NodeId, GitCommit } from './types.js';

/**
 * A function chain representing an operation's data flow.
 * References nodes by ID (doesn't duplicate node data).
 */
export interface Chain {
  /** Unique identifier (operation name) */
  id: ChainId;

  /** Human-readable description of the operation */
  description: string;

  /** Entry point node (e.g., API handler) */
  entryNodeId: NodeId;

  /** All nodes in this chain (including entry) */
  nodeIds: Set<NodeId>;

  /** Git commit when this chain was traced */
  tracedAtCommit: GitCommit;

  /** When this chain was last traced */
  tracedAt: Date;

  /** Whether any node in this chain is stale */
  isStale: boolean;
}

/**
 * Create a new chain.
 */
export function createChain(
  id: ChainId,
  description: string,
  entryNodeId: NodeId,
  commit: GitCommit
): Chain {
  return {
    id,
    description,
    entryNodeId,
    nodeIds: new Set([entryNodeId]),
    tracedAtCommit: commit,
    tracedAt: new Date(),
    isStale: false,
  };
}
```

**File**: `src/model/chain-map.ts`
```typescript
import type { NodeId, ChainId, GitCommit } from './types.js';
import type { FunctionNode } from './node.js';
import type { Chain } from './chain.js';

/**
 * The central chain map with reverse index for invalidation.
 */
export class ChainMap {
  /** All function nodes, keyed by NodeId */
  private nodes: Map<NodeId, FunctionNode> = new Map();

  /** All chains, keyed by ChainId */
  private chains: Map<ChainId, Chain> = new Map();

  /** Reverse index: which chains contain each node */
  private nodeToChains: Map<NodeId, Set<ChainId>> = new Map();

  // ─────────────────────────────────────────────────────────────
  // Node Operations
  // ─────────────────────────────────────────────────────────────

  /**
   * Add or update a node.
   */
  addNode(node: FunctionNode): void {
    this.nodes.set(node.id, node);
  }

  /**
   * Get a node by ID.
   */
  getNode(id: NodeId): FunctionNode | undefined {
    return this.nodes.get(id);
  }

  /**
   * Get all nodes.
   */
  getAllNodes(): FunctionNode[] {
    return Array.from(this.nodes.values());
  }

  /**
   * Get nodes in a file.
   */
  getNodesInFile(file: string): FunctionNode[] {
    return Array.from(this.nodes.values()).filter(n => n.file === file);
  }

  // ─────────────────────────────────────────────────────────────
  // Chain Operations
  // ─────────────────────────────────────────────────────────────

  /**
   * Add a chain and update reverse index.
   */
  addChain(chain: Chain): void {
    this.chains.set(chain.id, chain);

    // Update reverse index
    for (const nodeId of chain.nodeIds) {
      if (!this.nodeToChains.has(nodeId)) {
        this.nodeToChains.set(nodeId, new Set());
      }
      this.nodeToChains.get(nodeId)!.add(chain.id);
    }
  }

  /**
   * Get a chain by ID.
   */
  getChain(id: ChainId): Chain | undefined {
    return this.chains.get(id);
  }

  /**
   * Get all chains.
   */
  getAllChains(): Chain[] {
    return Array.from(this.chains.values());
  }

  /**
   * Get chains containing a specific node.
   */
  getChainsContainingNode(nodeId: NodeId): Chain[] {
    const chainIds = this.nodeToChains.get(nodeId);
    if (!chainIds) return [];
    return Array.from(chainIds)
      .map(id => this.chains.get(id))
      .filter((c): c is Chain => c !== undefined);
  }

  // ─────────────────────────────────────────────────────────────
  // Invalidation
  // ─────────────────────────────────────────────────────────────

  /**
   * Mark a node as stale and propagate to affected chains.
   * Returns the chain IDs that were invalidated.
   */
  invalidateNode(nodeId: NodeId): ChainId[] {
    const node = this.nodes.get(nodeId);
    if (node) {
      node.isStale = true;
    }

    const affectedChainIds: ChainId[] = [];
    const chainIds = this.nodeToChains.get(nodeId);
    if (chainIds) {
      for (const chainId of chainIds) {
        const chain = this.chains.get(chainId);
        if (chain) {
          chain.isStale = true;
          affectedChainIds.push(chainId);
        }
      }
    }

    return affectedChainIds;
  }

  /**
   * Mark a node as valid after re-annotation.
   */
  validateNode(nodeId: NodeId, commit: GitCommit): void {
    const node = this.nodes.get(nodeId);
    if (node) {
      node.isStale = false;
      node.lastValidCommit = commit;
    }
  }

  /**
   * Get all stale nodes.
   */
  getStaleNodes(): FunctionNode[] {
    return Array.from(this.nodes.values()).filter(n => n.isStale);
  }

  /**
   * Get all stale chains.
   */
  getStaleChains(): Chain[] {
    return Array.from(this.chains.values()).filter(c => c.isStale);
  }

  // ─────────────────────────────────────────────────────────────
  // Query
  // ─────────────────────────────────────────────────────────────

  /**
   * Find chains by keyword in description or entry node name.
   */
  queryChains(keyword: string): Chain[] {
    const lowerKeyword = keyword.toLowerCase();
    return Array.from(this.chains.values()).filter(chain => {
      if (chain.description.toLowerCase().includes(lowerKeyword)) return true;
      const entryNode = this.nodes.get(chain.entryNodeId);
      if (entryNode?.name.toLowerCase().includes(lowerKeyword)) return true;
      return false;
    });
  }

  /**
   * Find chains that touch a specific file.
   */
  queryChainsForFile(file: string): Chain[] {
    const nodesInFile = this.getNodesInFile(file);
    const chainIds = new Set<ChainId>();
    for (const node of nodesInFile) {
      const chains = this.nodeToChains.get(node.id);
      if (chains) {
        for (const chainId of chains) {
          chainIds.add(chainId);
        }
      }
    }
    return Array.from(chainIds)
      .map(id => this.chains.get(id))
      .filter((c): c is Chain => c !== undefined);
  }

  // ─────────────────────────────────────────────────────────────
  // Statistics
  // ─────────────────────────────────────────────────────────────

  /**
   * Get chain map statistics.
   */
  getStats(): {
    totalNodes: number;
    totalChains: number;
    staleNodes: number;
    staleChains: number;
    nodesWithoutDO: number;
  } {
    const nodes = Array.from(this.nodes.values());
    const chains = Array.from(this.chains.values());
    return {
      totalNodes: nodes.length,
      totalChains: chains.length,
      staleNodes: nodes.filter(n => n.isStale).length,
      staleChains: chains.filter(c => c.isStale).length,
      nodesWithoutDO: nodes.filter(n => !n.doAnnotation).length,
    };
  }
}
```

#### 3. SQLite Schema

**File**: `db/schema.sql`
```sql
-- ============================================================
-- Function Chain Map SQLite Schema
-- ============================================================

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ────────────────────────────────────────────────────────────
-- Function Nodes
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,                    -- NodeId: "file::name::startByte"
    name TEXT NOT NULL,                     -- Function name
    file TEXT NOT NULL,                     -- Source file path
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    start_byte INTEGER NOT NULL,
    end_byte INTEGER NOT NULL,

    -- Contracts (JSON serialized)
    in_contract_json TEXT NOT NULL,         -- InContract
    out_contract_json TEXT NOT NULL,        -- OutContract

    -- DO annotation (nullable until annotated)
    do_annotation_json TEXT,                -- DoAnnotation | null

    -- Call graph edges (JSON array of NodeIds)
    calls_json TEXT NOT NULL DEFAULT '[]',

    -- Caching
    body_hash TEXT NOT NULL,                -- SHA256[:16] of function body
    last_valid_commit TEXT NOT NULL,        -- Git commit SHA
    is_stale INTEGER NOT NULL DEFAULT 0,    -- Boolean

    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_nodes_file ON nodes(file);
CREATE INDEX IF NOT EXISTS idx_nodes_body_hash ON nodes(body_hash);
CREATE INDEX IF NOT EXISTS idx_nodes_is_stale ON nodes(is_stale);

-- ────────────────────────────────────────────────────────────
-- Chains
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chains (
    id TEXT PRIMARY KEY,                    -- ChainId: operation name
    description TEXT NOT NULL,
    entry_node_id TEXT NOT NULL,            -- References nodes.id
    traced_at_commit TEXT NOT NULL,         -- Git commit SHA
    traced_at TEXT NOT NULL,                -- ISO timestamp
    is_stale INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (entry_node_id) REFERENCES nodes(id)
);

-- ────────────────────────────────────────────────────────────
-- Chain-Node Junction (many-to-many)
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chain_nodes (
    chain_id TEXT NOT NULL,
    node_id TEXT NOT NULL,

    PRIMARY KEY (chain_id, node_id),
    FOREIGN KEY (chain_id) REFERENCES chains(id) ON DELETE CASCADE,
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- Reverse index for invalidation queries
CREATE INDEX IF NOT EXISTS idx_chain_nodes_node ON chain_nodes(node_id);

-- ────────────────────────────────────────────────────────────
-- DO Annotation Cache
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS do_cache (
    body_hash TEXT PRIMARY KEY,             -- SHA256[:16] of function body
    annotation_json TEXT NOT NULL,          -- DoAnnotation
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ────────────────────────────────────────────────────────────
-- Migrations (Added from Review)
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT NOT NULL
);

-- Track initial schema
INSERT OR IGNORE INTO migrations (version, description)
VALUES (1, 'Initial schema');

-- ────────────────────────────────────────────────────────────
-- Metadata
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Initialize metadata
INSERT OR IGNORE INTO metadata (key, value) VALUES ('schema_version', '1');
INSERT OR IGNORE INTO metadata (key, value) VALUES ('last_invalidation_commit', '');

-- ────────────────────────────────────────────────────────────
-- Additional Indexes (Added from Review)
-- ────────────────────────────────────────────────────────────

-- Index on node name for entry point lookup
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);

-- Composite index on chain_nodes for both directions
CREATE INDEX IF NOT EXISTS idx_chain_nodes_chain ON chain_nodes(chain_id);
```

**File**: `src/db/connection.ts`
```typescript
import Database from 'better-sqlite3';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * Database connection manager.
 */
export class DbConnection {
  private db: Database.Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.db.pragma('journal_mode = WAL');
    this.db.pragma('foreign_keys = ON');
  }

  /**
   * Initialize schema from SQL file.
   */
  initializeSchema(): void {
    const schemaPath = join(__dirname, '../../db/schema.sql');
    const schema = readFileSync(schemaPath, 'utf-8');
    this.db.exec(schema);
  }

  /**
   * Get the underlying database instance.
   */
  getDb(): Database.Database {
    return this.db;
  }

  /**
   * Close the database connection.
   */
  close(): void {
    this.db.close();
  }
}
```

#### 4. ChainMap Repository (CRITICAL - Added from Review)

**File**: `src/db/repository.ts`

> **Why This Is Critical**: The original plan defined ChainMap as purely in-memory, but the CLI expects data to persist across invocations. Without this repository layer, `chain-map trace` creates a chain that is lost when the CLI exits, causing `chain-map build-context` to fail.

```typescript
import type Database from 'better-sqlite3';
import type { ChainMap } from '../model/chain-map.js';
import type { FunctionNode } from '../model/node.js';
import type { Chain } from '../model/chain.js';
import type { NodeId, ChainId, DoAnnotation, InContract, OutContract } from '../model/types.js';
import { DatabaseError } from '../model/types.js';

/**
 * Repository for persisting ChainMap to SQLite.
 * Bridges the in-memory ChainMap with durable storage.
 */
export class ChainMapRepository {
  private db: Database.Database;

  // Prepared statements for performance
  private stmts: {
    insertNode: Database.Statement;
    updateNode: Database.Statement;
    getNode: Database.Statement;
    getAllNodes: Database.Statement;
    getNodesByFile: Database.Statement;
    deleteNode: Database.Statement;
    insertChain: Database.Statement;
    updateChain: Database.Statement;
    getChain: Database.Statement;
    getAllChains: Database.Statement;
    deleteChain: Database.Statement;
    insertChainNode: Database.Statement;
    deleteChainNodes: Database.Statement;
    getChainNodes: Database.Statement;
    getNodeChains: Database.Statement;
  };

  constructor(db: Database.Database) {
    this.db = db;
    this.stmts = this.prepareStatements();
  }

  private prepareStatements() {
    return {
      insertNode: this.db.prepare(`
        INSERT INTO nodes (
          id, name, file, start_line, end_line, start_byte, end_byte,
          in_contract_json, out_contract_json, do_annotation_json,
          calls_json, body_hash, last_valid_commit, is_stale
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `),
      updateNode: this.db.prepare(`
        UPDATE nodes SET
          do_annotation_json = ?,
          calls_json = ?,
          body_hash = ?,
          last_valid_commit = ?,
          is_stale = ?,
          updated_at = datetime('now')
        WHERE id = ?
      `),
      getNode: this.db.prepare(`SELECT * FROM nodes WHERE id = ?`),
      getAllNodes: this.db.prepare(`SELECT * FROM nodes`),
      getNodesByFile: this.db.prepare(`SELECT * FROM nodes WHERE file = ?`),
      deleteNode: this.db.prepare(`DELETE FROM nodes WHERE id = ?`),
      insertChain: this.db.prepare(`
        INSERT INTO chains (id, description, entry_node_id, traced_at_commit, traced_at, is_stale)
        VALUES (?, ?, ?, ?, ?, ?)
      `),
      updateChain: this.db.prepare(`
        UPDATE chains SET is_stale = ? WHERE id = ?
      `),
      getChain: this.db.prepare(`SELECT * FROM chains WHERE id = ?`),
      getAllChains: this.db.prepare(`SELECT * FROM chains`),
      deleteChain: this.db.prepare(`DELETE FROM chains WHERE id = ?`),
      insertChainNode: this.db.prepare(`
        INSERT OR IGNORE INTO chain_nodes (chain_id, node_id) VALUES (?, ?)
      `),
      deleteChainNodes: this.db.prepare(`DELETE FROM chain_nodes WHERE chain_id = ?`),
      getChainNodes: this.db.prepare(`SELECT node_id FROM chain_nodes WHERE chain_id = ?`),
      getNodeChains: this.db.prepare(`SELECT chain_id FROM chain_nodes WHERE node_id = ?`),
    };
  }

  // ─────────────────────────────────────────────────────────────
  // Load/Save Full ChainMap
  // ─────────────────────────────────────────────────────────────

  /**
   * Load entire ChainMap from SQLite.
   */
  loadAll(): ChainMap {
    const chainMap = new ChainMap();

    try {
      // Load all nodes
      const nodeRows = this.stmts.getAllNodes.all() as any[];
      for (const row of nodeRows) {
        chainMap.addNode(this.rowToNode(row));
      }

      // Load all chains with their node sets
      const chainRows = this.stmts.getAllChains.all() as any[];
      for (const row of chainRows) {
        const chain = this.rowToChain(row);
        const nodeIds = this.stmts.getChainNodes.all(row.id) as { node_id: string }[];
        chain.nodeIds = new Set(nodeIds.map(n => n.node_id));
        chainMap.addChain(chain);
      }

      return chainMap;
    } catch (error) {
      throw new DatabaseError('corruption', `Failed to load ChainMap: ${error}`);
    }
  }

  /**
   * Save entire ChainMap to SQLite (full sync).
   * Use sparingly - prefer incremental saves.
   */
  saveAll(chainMap: ChainMap): void {
    const transaction = this.db.transaction(() => {
      // Save all nodes
      for (const node of chainMap.getAllNodes()) {
        this.saveNode(node);
      }

      // Save all chains
      for (const chain of chainMap.getAllChains()) {
        this.saveChain(chain);
      }
    });

    try {
      transaction();
    } catch (error) {
      if (String(error).includes('SQLITE_BUSY')) {
        throw new DatabaseError('locked', 'Database is locked by another process');
      }
      throw new DatabaseError('corruption', `Failed to save ChainMap: ${error}`);
    }
  }

  // ─────────────────────────────────────────────────────────────
  // Individual Node Operations
  // ─────────────────────────────────────────────────────────────

  /**
   * Save a single node (insert or update).
   */
  saveNode(node: FunctionNode): void {
    const existing = this.stmts.getNode.get(node.id);

    if (existing) {
      this.stmts.updateNode.run(
        node.doAnnotation ? JSON.stringify(node.doAnnotation) : null,
        JSON.stringify(node.calls),
        node.bodyHash,
        node.lastValidCommit,
        node.isStale ? 1 : 0,
        node.id
      );
    } else {
      this.stmts.insertNode.run(
        node.id,
        node.name,
        node.file,
        node.startLine,
        node.endLine,
        node.startByte,
        node.endByte,
        JSON.stringify(node.inContract),
        JSON.stringify(node.outContract),
        node.doAnnotation ? JSON.stringify(node.doAnnotation) : null,
        JSON.stringify(node.calls),
        node.bodyHash,
        node.lastValidCommit,
        node.isStale ? 1 : 0
      );
    }
  }

  /**
   * Get a single node by ID.
   */
  getNode(id: NodeId): FunctionNode | null {
    const row = this.stmts.getNode.get(id) as any;
    return row ? this.rowToNode(row) : null;
  }

  /**
   * Delete a node by ID.
   */
  deleteNode(id: NodeId): void {
    this.stmts.deleteNode.run(id);
  }

  // ─────────────────────────────────────────────────────────────
  // Individual Chain Operations
  // ─────────────────────────────────────────────────────────────

  /**
   * Save a single chain (insert or update).
   */
  saveChain(chain: Chain): void {
    const existing = this.stmts.getChain.get(chain.id);

    if (existing) {
      this.stmts.updateChain.run(chain.isStale ? 1 : 0, chain.id);
    } else {
      this.stmts.insertChain.run(
        chain.id,
        chain.description,
        chain.entryNodeId,
        chain.tracedAtCommit,
        chain.tracedAt.toISOString(),
        chain.isStale ? 1 : 0
      );
    }

    // Update chain_nodes junction table
    this.stmts.deleteChainNodes.run(chain.id);
    for (const nodeId of chain.nodeIds) {
      this.stmts.insertChainNode.run(chain.id, nodeId);
    }
  }

  /**
   * Get a single chain by ID.
   */
  getChain(id: ChainId): Chain | null {
    const row = this.stmts.getChain.get(id) as any;
    if (!row) return null;

    const chain = this.rowToChain(row);
    const nodeIds = this.stmts.getChainNodes.all(id) as { node_id: string }[];
    chain.nodeIds = new Set(nodeIds.map(n => n.node_id));
    return chain;
  }

  /**
   * Mark a node as stale and return affected chain IDs.
   */
  markNodeStale(nodeId: NodeId): ChainId[] {
    // Update node
    this.db.prepare(`UPDATE nodes SET is_stale = 1 WHERE id = ?`).run(nodeId);

    // Find and update affected chains
    const chainIds = this.stmts.getNodeChains.all(nodeId) as { chain_id: string }[];
    for (const { chain_id } of chainIds) {
      this.db.prepare(`UPDATE chains SET is_stale = 1 WHERE id = ?`).run(chain_id);
    }

    return chainIds.map(c => c.chain_id);
  }

  // ─────────────────────────────────────────────────────────────
  // Row Conversion Helpers
  // ─────────────────────────────────────────────────────────────

  private rowToNode(row: any): FunctionNode {
    return {
      id: row.id,
      name: row.name,
      file: row.file,
      startLine: row.start_line,
      endLine: row.end_line,
      startByte: row.start_byte,
      endByte: row.end_byte,
      inContract: JSON.parse(row.in_contract_json),
      outContract: JSON.parse(row.out_contract_json),
      doAnnotation: row.do_annotation_json ? JSON.parse(row.do_annotation_json) : null,
      calls: JSON.parse(row.calls_json),
      bodyHash: row.body_hash,
      lastValidCommit: row.last_valid_commit,
      isStale: row.is_stale === 1,
    };
  }

  private rowToChain(row: any): Chain {
    return {
      id: row.id,
      description: row.description,
      entryNodeId: row.entry_node_id,
      nodeIds: new Set(),  // Filled by caller
      tracedAtCommit: row.traced_at_commit,
      tracedAt: new Date(row.traced_at),
      isStale: row.is_stale === 1,
    };
  }
}
```

### Success Criteria

#### Automated Verification:
- [ ] `npm install` completes without errors
- [ ] `npm run typecheck` passes
- [ ] `npm run lint` passes
- [ ] Unit tests for ChainMap class pass: `npm test -- --grep "ChainMap"`
- [ ] SQLite schema creates successfully

#### Manual Verification:
- [ ] Project structure matches specification
- [ ] TypeScript compiles to valid JavaScript
- [ ] ChainMap reverse index correctly tracks node→chain relationships

---

╔═════════════════════════════════════════════════════════════════════════════╗
║                              PHASE 2                                         ║
║                    Tree-Sitter Integration (TypeScript)                      ║
╚═════════════════════════════════════════════════════════════════════════════╝

## Phase 2: Tree-Sitter Integration

### Overview

Implement deterministic AST parsing for TypeScript files to extract function definitions, signatures, call sites, and contracts. This phase is 100% deterministic—no LLM calls.

### Changes Required

#### 1. Tree-Sitter Parser Wrapper

**File**: `src/parser/tree-sitter.ts`
```typescript
import Parser from 'tree-sitter';
import TypeScript from 'tree-sitter-typescript';

/**
 * Tree-sitter parser wrapper for TypeScript.
 */
export class TypeScriptParser {
  private parser: Parser;

  constructor() {
    this.parser = new Parser();
    this.parser.setLanguage(TypeScript.typescript);
  }

  /**
   * Parse TypeScript source code into AST.
   */
  parse(code: string): Parser.Tree {
    return this.parser.parse(code);
  }

  /**
   * Parse with previous tree for incremental parsing.
   */
  parseIncremental(code: string, previousTree: Parser.Tree): Parser.Tree {
    return this.parser.parse(code, previousTree);
  }
}

// Singleton instance
let parserInstance: TypeScriptParser | null = null;

export function getParser(): TypeScriptParser {
  if (!parserInstance) {
    parserInstance = new TypeScriptParser();
  }
  return parserInstance;
}
```

#### 2. Function Extractor

**File**: `src/parser/extractor.ts`
```typescript
import type Parser from 'tree-sitter';
import { createHash } from 'crypto';
import type { FunctionNode, InContract, OutContract, NodeId } from '../model/types.js';
import { createNodeId } from '../model/node.js';
import { getParser } from './tree-sitter.js';

/**
 * Raw extracted function data before full node creation.
 */
export interface ExtractedFunction {
  name: string;
  file: string;
  startLine: number;
  endLine: number;
  startByte: number;
  endByte: number;
  body: string;
  bodyHash: string;
  inContract: InContract;
  outContract: OutContract;
  callSites: string[];  // Function names called
}

/**
 * Extract all functions from TypeScript source code.
 */
export function extractFunctions(code: string, filePath: string): ExtractedFunction[] {
  const parser = getParser();
  const tree = parser.parse(code);
  const functions: ExtractedFunction[] = [];

  // Query for function declarations, arrow functions, and methods
  traverseForFunctions(tree.rootNode, code, filePath, functions);

  return functions;
}

/**
 * Traverse AST to find function definitions.
 */
function traverseForFunctions(
  node: Parser.SyntaxNode,
  code: string,
  filePath: string,
  functions: ExtractedFunction[]
): void {
  // Function declaration: function foo() {}
  if (node.type === 'function_declaration') {
    const func = extractFunctionDeclaration(node, code, filePath);
    if (func) functions.push(func);
  }

  // Arrow function in variable: const foo = () => {}
  if (node.type === 'lexical_declaration' || node.type === 'variable_declaration') {
    const declarator = node.childForFieldName('declarator') ||
                       node.children.find(c => c.type === 'variable_declarator');
    if (declarator) {
      const value = declarator.childForFieldName('value');
      if (value?.type === 'arrow_function') {
        const name = declarator.childForFieldName('name')?.text;
        if (name) {
          const func = extractArrowFunction(value, name, code, filePath);
          if (func) functions.push(func);
        }
      }
    }
  }

  // Method definition in class
  if (node.type === 'method_definition') {
    const func = extractMethodDefinition(node, code, filePath);
    if (func) functions.push(func);
  }

  // Recurse into children
  for (const child of node.children) {
    traverseForFunctions(child, code, filePath, functions);
  }
}

/**
 * Extract a function declaration.
 */
function extractFunctionDeclaration(
  node: Parser.SyntaxNode,
  code: string,
  filePath: string
): ExtractedFunction | null {
  const nameNode = node.childForFieldName('name');
  const paramsNode = node.childForFieldName('parameters');
  const bodyNode = node.childForFieldName('body');
  const returnTypeNode = node.childForFieldName('return_type');

  if (!nameNode || !bodyNode) return null;

  const name = nameNode.text;
  const body = bodyNode.text;
  const bodyHash = hashBody(body);

  return {
    name,
    file: filePath,
    startLine: node.startPosition.row + 1,
    endLine: node.endPosition.row + 1,
    startByte: node.startIndex,
    endByte: node.endIndex,
    body,
    bodyHash,
    inContract: extractInContract(paramsNode),
    outContract: extractOutContract(returnTypeNode, node),
    callSites: extractCallSites(bodyNode),
  };
}

/**
 * Extract an arrow function.
 */
function extractArrowFunction(
  node: Parser.SyntaxNode,
  name: string,
  code: string,
  filePath: string
): ExtractedFunction | null {
  const paramsNode = node.childForFieldName('parameters');
  const bodyNode = node.childForFieldName('body');
  const returnTypeNode = node.childForFieldName('return_type');

  if (!bodyNode) return null;

  const body = bodyNode.text;
  const bodyHash = hashBody(body);

  return {
    name,
    file: filePath,
    startLine: node.startPosition.row + 1,
    endLine: node.endPosition.row + 1,
    startByte: node.startIndex,
    endByte: node.endIndex,
    body,
    bodyHash,
    inContract: extractInContract(paramsNode),
    outContract: extractOutContract(returnTypeNode, node),
    callSites: extractCallSites(bodyNode),
  };
}

/**
 * Extract a method definition from a class.
 */
function extractMethodDefinition(
  node: Parser.SyntaxNode,
  code: string,
  filePath: string
): ExtractedFunction | null {
  const nameNode = node.childForFieldName('name');
  const paramsNode = node.childForFieldName('parameters');
  const bodyNode = node.childForFieldName('body');
  const returnTypeNode = node.childForFieldName('return_type');

  if (!nameNode || !bodyNode) return null;

  // Get class name for qualified name
  let className = '';
  let parent = node.parent;
  while (parent) {
    if (parent.type === 'class_declaration') {
      className = parent.childForFieldName('name')?.text || '';
      break;
    }
    parent = parent.parent;
  }

  const methodName = nameNode.text;
  const name = className ? `${className}.${methodName}` : methodName;
  const body = bodyNode.text;
  const bodyHash = hashBody(body);

  return {
    name,
    file: filePath,
    startLine: node.startPosition.row + 1,
    endLine: node.endPosition.row + 1,
    startByte: node.startIndex,
    endByte: node.endIndex,
    body,
    bodyHash,
    inContract: extractInContract(paramsNode),
    outContract: extractOutContract(returnTypeNode, node),
    callSites: extractCallSites(bodyNode),
  };
}

/**
 * Extract IN contract from parameters node.
 */
function extractInContract(paramsNode: Parser.SyntaxNode | null): InContract {
  const parameters: InContract['parameters'] = [];

  if (paramsNode) {
    for (const child of paramsNode.children) {
      if (child.type === 'required_parameter' || child.type === 'optional_parameter') {
        const nameNode = child.childForFieldName('pattern') ||
                         child.childForFieldName('name');
        const typeNode = child.childForFieldName('type');

        parameters.push({
          name: nameNode?.text || 'unknown',
          type: typeNode?.text || 'any',
          optional: child.type === 'optional_parameter',
        });
      }
    }
  }

  const signature = paramsNode?.text || '()';

  return { parameters, signature };
}

/**
 * Extract OUT contract from return type and body.
 */
function extractOutContract(
  returnTypeNode: Parser.SyntaxNode | null,
  funcNode: Parser.SyntaxNode
): OutContract {
  const returnType = returnTypeNode?.text?.replace(/^:\s*/, '') || 'void';
  const isAsync = funcNode.children.some(c => c.type === 'async');

  // Extract throw statements for error types
  const errorTypes: string[] = [];
  traverseForThrows(funcNode, errorTypes);

  return { returnType, errorTypes, isAsync };
}

/**
 * Find throw statements to identify error types.
 */
function traverseForThrows(node: Parser.SyntaxNode, errorTypes: string[]): void {
  if (node.type === 'throw_statement') {
    const expr = node.children[1];
    if (expr?.type === 'new_expression') {
      const constructorName = expr.childForFieldName('constructor')?.text;
      if (constructorName && !errorTypes.includes(constructorName)) {
        errorTypes.push(constructorName);
      }
    }
  }

  for (const child of node.children) {
    traverseForThrows(child, errorTypes);
  }
}

/**
 * Extract function call sites from body.
 */
function extractCallSites(bodyNode: Parser.SyntaxNode): string[] {
  const calls: string[] = [];
  traverseForCalls(bodyNode, calls);

  // Filter out common non-function identifiers
  const excluded = new Set(['if', 'for', 'while', 'return', 'console', 'require', 'import']);
  return [...new Set(calls)].filter(c => !excluded.has(c));
}

/**
 * Traverse to find call expressions.
 */
function traverseForCalls(node: Parser.SyntaxNode, calls: string[]): void {
  if (node.type === 'call_expression') {
    const funcNode = node.childForFieldName('function');
    if (funcNode) {
      // Handle method calls: obj.method()
      if (funcNode.type === 'member_expression') {
        const property = funcNode.childForFieldName('property');
        if (property) {
          calls.push(property.text);
        }
      }
      // Handle direct calls: func()
      else if (funcNode.type === 'identifier') {
        calls.push(funcNode.text);
      }
    }
  }

  for (const child of node.children) {
    traverseForCalls(child, calls);
  }
}

/**
 * Hash function body for cache keying.
 * Uses SHA256 truncated to 16 characters.
 */
export function hashBody(body: string): string {
  // Normalize whitespace for more stable hashing
  const normalized = body.replace(/\s+/g, ' ').trim();
  return createHash('sha256').update(normalized).digest('hex').slice(0, 16);
}
```

#### 3. Call Graph Builder

**File**: `src/parser/call-graph.ts`
```typescript
import type { NodeId } from '../model/types.js';
import type { ExtractedFunction } from './extractor.js';
import { createNodeId } from '../model/node.js';

/**
 * Build call graph edges from extracted functions.
 * Resolves call site names to actual NodeIds where possible.
 */
export function buildCallGraph(
  functions: ExtractedFunction[]
): Map<NodeId, NodeId[]> {
  // Build lookup from function name to NodeId
  const nameToNodeId = new Map<string, NodeId>();
  for (const func of functions) {
    const nodeId = createNodeId(func.file, func.name, func.startByte);
    nameToNodeId.set(func.name, nodeId);

    // Also map unqualified method names
    if (func.name.includes('.')) {
      const methodName = func.name.split('.').pop()!;
      // Only map if unambiguous (no collision)
      if (!nameToNodeId.has(methodName)) {
        nameToNodeId.set(methodName, nodeId);
      }
    }
  }

  // Build edges
  const callGraph = new Map<NodeId, NodeId[]>();
  for (const func of functions) {
    const nodeId = createNodeId(func.file, func.name, func.startByte);
    const calls: NodeId[] = [];

    for (const callSite of func.callSites) {
      const targetId = nameToNodeId.get(callSite);
      if (targetId && targetId !== nodeId) {  // Exclude self-calls
        calls.push(targetId);
      }
    }

    callGraph.set(nodeId, calls);
  }

  return callGraph;
}

/**
 * Trace a chain from entry point to all reachable functions.
 * Uses BFS to avoid infinite loops in recursive calls.
 */
export function traceChain(
  entryNodeId: NodeId,
  callGraph: Map<NodeId, NodeId[]>
): Set<NodeId> {
  const visited = new Set<NodeId>();
  const queue = [entryNodeId];

  while (queue.length > 0) {
    const current = queue.shift()!;
    if (visited.has(current)) continue;

    visited.add(current);

    const calls = callGraph.get(current) || [];
    for (const callee of calls) {
      if (!visited.has(callee)) {
        queue.push(callee);
      }
    }
  }

  return visited;
}
```

### Success Criteria

#### Automated Verification:
- [ ] `npm run typecheck` passes
- [ ] Unit tests for extractor pass: `npm test -- --grep "extractor"`
- [ ] Unit tests for call-graph pass: `npm test -- --grep "call-graph"`
- [ ] Extracts functions from sample TypeScript file correctly

#### Manual Verification:
- [ ] Correctly identifies function declarations, arrow functions, and methods
- [ ] IN contracts capture all parameters with types
- [ ] OUT contracts capture return types and async status
- [ ] Call sites are correctly identified

---

╔═════════════════════════════════════════════════════════════════════════════╗
║                              PHASE 3                                         ║
║                       DO Annotation Service (Haiku)                          ║
╚═════════════════════════════════════════════════════════════════════════════╝

## Phase 3: DO Annotation Service

### Overview

Implement the DO annotation service using Claude Haiku. Each function body is analyzed independently (sandboxed stochastic element), with results cached by body hash. Supports parallel batch annotation for throughput.

### Changes Required

#### 1. Annotation Provider Interface (Added from Review)

**File**: `src/annotator/provider.ts`

> **Why This Matters**: Decouples annotation logic from Anthropic SDK, enabling testing with mocks and future support for local models or other providers.

```typescript
import type { DoAnnotation, BodyHash } from '../model/types.js';

/**
 * Interface for annotation providers.
 * Allows swapping between Haiku, local models, or mock implementations.
 */
export interface AnnotationProvider {
  /**
   * Annotate a single function body.
   * @param body - The function body source code
   * @param bodyHash - Hash of the body for caching
   * @param options - Optional configuration
   */
  annotate(
    body: string,
    bodyHash: BodyHash,
    options?: AnnotationOptions
  ): Promise<DoAnnotation>;

  /**
   * Annotate multiple function bodies in batch.
   * Default implementation calls annotate() in parallel.
   */
  batchAnnotate?(
    items: Array<{ body: string; hash: BodyHash }>,
    options?: BatchAnnotationOptions
  ): Promise<Map<BodyHash, DoAnnotation>>;

  /**
   * Provider name for logging/debugging.
   */
  readonly name: string;
}

/**
 * Options for single annotation.
 */
export interface AnnotationOptions {
  /** Timeout in milliseconds (default: 30000) */
  timeoutMs?: number;
  /** AbortController signal for cancellation */
  signal?: AbortSignal;
}

/**
 * Options for batch annotation.
 */
export interface BatchAnnotationOptions extends AnnotationOptions {
  /** Maximum concurrent requests (default: 10) */
  concurrency?: number;
  /** Progress callback */
  onProgress?: (completed: number, total: number, current: string) => void;
}

/**
 * Mock provider for testing.
 */
export class MockAnnotationProvider implements AnnotationProvider {
  readonly name = 'mock';

  async annotate(body: string, bodyHash: BodyHash): Promise<DoAnnotation> {
    return {
      action: `Mock annotation for ${bodyHash.slice(0, 8)}`,
      sideEffects: [],
      errorConditions: [],
      bodyHash,
      annotatedAt: new Date(),
    };
  }
}
```

#### 2. Haiku Client (Enhanced with Timeout)

**File**: `src/annotator/haiku-client.ts`
```typescript
import Anthropic from '@anthropic-ai/sdk';
import type { DoAnnotation, BodyHash } from '../model/types.js';
import type { AnnotationProvider, AnnotationOptions } from './provider.js';
import { AnnotationError } from '../model/types.js';

const HAIKU_MODEL = 'claude-3-5-haiku-latest';
const DEFAULT_TIMEOUT_MS = 30000;

/**
 * DO annotation prompt template.
 * Designed for minimal tokens while capturing key semantic info.
 */
const DO_PROMPT = `Analyze this TypeScript function body and provide:
1. ACTION: What does this function do? (1 sentence, start with a verb)
2. SIDE_EFFECTS: List any side effects (DB writes, network calls, logging, file I/O). Write "none" if pure.
3. ERROR_CONDITIONS: What conditions cause this function to throw or return errors? Write "none" if never errors.

Function body:
\`\`\`typescript
{{BODY}}
\`\`\`

Respond in this exact format:
ACTION: <one sentence>
SIDE_EFFECTS: <comma-separated list or "none">
ERROR_CONDITIONS: <comma-separated list or "none">`;

/**
 * Haiku client for generating DO annotations.
 * Implements AnnotationProvider interface for pluggability.
 */
export class HaikuAnnotator implements AnnotationProvider {
  readonly name = 'haiku';
  private client: Anthropic;

  constructor(apiKey?: string) {
    this.client = new Anthropic({
      apiKey: apiKey || process.env.ANTHROPIC_API_KEY,
    });
  }

  /**
   * Generate a DO annotation for a single function body.
   * Enhanced with timeout and cancellation support (from review).
   */
  async annotate(
    body: string,
    bodyHash: BodyHash,
    options?: AnnotationOptions
  ): Promise<DoAnnotation> {
    const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    // Combine with external signal if provided
    if (options?.signal) {
      options.signal.addEventListener('abort', () => controller.abort());
    }

    const prompt = DO_PROMPT.replace('{{BODY}}', body);

    try {
      const response = await this.client.messages.create({
        model: HAIKU_MODEL,
        max_tokens: 256,
        messages: [{ role: 'user', content: prompt }],
      }, {
        signal: controller.signal,
      });

      // Extract text content
      const text = response.content
        .filter(block => block.type === 'text')
        .map(block => block.text)
        .join('\n');

      return this.parseResponse(text, bodyHash);
    } catch (error) {
      if (controller.signal.aborted) {
        throw new AnnotationError(bodyHash, 'timeout', `Annotation timed out after ${timeoutMs}ms`);
      }
      if (error instanceof Anthropic.RateLimitError) {
        throw new AnnotationError(bodyHash, 'rate_limit', 'Rate limited by Anthropic API');
      }
      if (error instanceof Anthropic.APIConnectionError) {
        throw new AnnotationError(bodyHash, 'network_error', `Network error: ${error.message}`);
      }
      throw new AnnotationError(bodyHash, 'api_error', `API error: ${error}`);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Parse Haiku response into DoAnnotation.
   */
  private parseResponse(text: string, bodyHash: BodyHash): DoAnnotation {
    const lines = text.split('\n').map(l => l.trim());

    let action = 'Unknown action';
    let sideEffects: string[] = [];
    let errorConditions: string[] = [];

    for (const line of lines) {
      if (line.startsWith('ACTION:')) {
        action = line.replace('ACTION:', '').trim();
      } else if (line.startsWith('SIDE_EFFECTS:')) {
        const value = line.replace('SIDE_EFFECTS:', '').trim();
        sideEffects = value.toLowerCase() === 'none'
          ? []
          : value.split(',').map(s => s.trim()).filter(Boolean);
      } else if (line.startsWith('ERROR_CONDITIONS:')) {
        const value = line.replace('ERROR_CONDITIONS:', '').trim();
        errorConditions = value.toLowerCase() === 'none'
          ? []
          : value.split(',').map(s => s.trim()).filter(Boolean);
      }
    }

    return {
      action,
      sideEffects,
      errorConditions,
      bodyHash,
      annotatedAt: new Date(),
    };
  }
}
```

#### 2. Annotation Cache

**File**: `src/annotator/cache.ts`
```typescript
import type Database from 'better-sqlite3';
import type { DoAnnotation, BodyHash } from '../model/types.js';

/**
 * SQLite-backed cache for DO annotations.
 * Key: body hash (content-addressed)
 */
export class AnnotationCache {
  private db: Database.Database;
  private getStmt: Database.Statement;
  private setStmt: Database.Statement;

  constructor(db: Database.Database) {
    this.db = db;

    // Prepare statements for performance
    this.getStmt = db.prepare(`
      SELECT annotation_json FROM do_cache WHERE body_hash = ?
    `);

    this.setStmt = db.prepare(`
      INSERT OR REPLACE INTO do_cache (body_hash, annotation_json, created_at)
      VALUES (?, ?, datetime('now'))
    `);
  }

  /**
   * Get cached annotation by body hash.
   */
  get(bodyHash: BodyHash): DoAnnotation | null {
    const row = this.getStmt.get(bodyHash) as { annotation_json: string } | undefined;
    if (!row) return null;

    const parsed = JSON.parse(row.annotation_json);
    return {
      ...parsed,
      annotatedAt: new Date(parsed.annotatedAt),
    };
  }

  /**
   * Store annotation in cache.
   */
  set(annotation: DoAnnotation): void {
    this.setStmt.run(annotation.bodyHash, JSON.stringify(annotation));
  }

  /**
   * Check if annotation exists in cache.
   */
  has(bodyHash: BodyHash): boolean {
    return this.get(bodyHash) !== null;
  }

  /**
   * Get cache statistics.
   */
  getStats(): { totalEntries: number; oldestEntry: Date | null } {
    const countRow = this.db.prepare('SELECT COUNT(*) as count FROM do_cache').get() as { count: number };
    const oldestRow = this.db.prepare('SELECT MIN(created_at) as oldest FROM do_cache').get() as { oldest: string | null };

    return {
      totalEntries: countRow.count,
      oldestEntry: oldestRow.oldest ? new Date(oldestRow.oldest) : null,
    };
  }
}
```

#### 3. Batch Annotator (CRITICAL - Race Condition Fix from Review)

**File**: `src/annotator/batch.ts`

> **Why This Is Critical**: The original implementation ran parallel API calls and updated the cache immediately within the async callbacks. This caused race conditions because cache/ChainMap updates could interleave unpredictably.
>
> **Solution**: Use the **Collect-Then-Apply** pattern:
> 1. Run parallel API calls without mutations (collect results)
> 2. Apply all updates in a synchronous block (race-free due to JS event loop)

```typescript
import type { FunctionNode } from '../model/node.js';
import type { DoAnnotation, BodyHash } from '../model/types.js';
import type { AnnotationProvider, BatchAnnotationOptions } from './provider.js';
import { AnnotationCache } from './cache.js';
import { AnnotationError } from '../model/types.js';

/**
 * Progress callback for batch annotation.
 */
export type ProgressCallback = (completed: number, total: number, current: string) => void;

/**
 * Result of a single annotation attempt.
 */
interface AnnotationAttempt {
  hash: BodyHash;
  result: DoAnnotation | null;
  error: AnnotationError | null;
}

/**
 * Batch annotator with parallelism and caching.
 * Uses Collect-Then-Apply pattern to avoid race conditions.
 */
export class BatchAnnotator {
  private provider: AnnotationProvider;
  private cache: AnnotationCache;
  private concurrency: number;

  constructor(
    provider: AnnotationProvider,
    cache: AnnotationCache,
    concurrency: number = 10
  ) {
    this.provider = provider;
    this.cache = cache;
    this.concurrency = concurrency;
  }

  /**
   * Annotate a batch of functions using Collect-Then-Apply pattern.
   *
   * IMPORTANT: This method is race-condition-safe because:
   * 1. All API calls run in parallel WITHOUT any mutations
   * 2. All cache/ChainMap updates happen in a single synchronous block
   * 3. JavaScript's single-threaded event loop guarantees the apply block is atomic
   */
  async annotateBatch(
    functions: Array<{ name: string; body: string; bodyHash: string }>,
    options?: BatchAnnotationOptions
  ): Promise<Map<string, DoAnnotation>> {
    const results = new Map<string, DoAnnotation>();
    const toAnnotate: typeof functions = [];
    const onProgress = options?.onProgress;

    // ═══════════════════════════════════════════════════════════
    // PHASE 1: COLLECT - Check cache (synchronous, safe)
    // ═══════════════════════════════════════════════════════════
    for (const func of functions) {
      const cached = this.cache.get(func.bodyHash);
      if (cached) {
        results.set(func.bodyHash, cached);
      } else {
        toAnnotate.push(func);
      }
    }

    // Report cache hits
    const cacheHits = functions.length - toAnnotate.length;
    if (onProgress && cacheHits > 0) {
      onProgress(cacheHits, functions.length, `${cacheHits} cache hits`);
    }

    // ═══════════════════════════════════════════════════════════
    // PHASE 2: FETCH - Run parallel API calls WITHOUT mutations
    // ═══════════════════════════════════════════════════════════
    const pendingResults: AnnotationAttempt[] = [];
    let completed = cacheHits;

    for (let i = 0; i < toAnnotate.length; i += this.concurrency) {
      const batch = toAnnotate.slice(i, i + this.concurrency);

      // Run API calls in parallel - NO CACHE WRITES HERE
      const batchPromises = batch.map(async (func): Promise<AnnotationAttempt> => {
        try {
          const annotation = await this.provider.annotate(
            func.body,
            func.bodyHash,
            { timeoutMs: options?.timeoutMs, signal: options?.signal }
          );
          return { hash: func.bodyHash, result: annotation, error: null };
        } catch (error) {
          const annotationError = error instanceof AnnotationError
            ? error
            : new AnnotationError(func.bodyHash, 'api_error', String(error));

          // Create fallback annotation
          const fallback: DoAnnotation = {
            action: `[Annotation failed: ${annotationError.cause}] ${func.name}`,
            sideEffects: [],
            errorConditions: [],
            bodyHash: func.bodyHash,
            annotatedAt: new Date(),
          };
          return { hash: func.bodyHash, result: fallback, error: annotationError };
        }
      });

      // Wait for batch to complete
      const batchResults = await Promise.all(batchPromises);
      pendingResults.push(...batchResults);

      // Progress reporting (no mutations)
      completed += batch.length;
      if (onProgress) {
        onProgress(completed, functions.length, `Processed ${completed}/${functions.length}`);
      }
    }

    // ═══════════════════════════════════════════════════════════
    // PHASE 3: APPLY - Synchronous updates (race-free)
    // ═══════════════════════════════════════════════════════════
    // This entire block runs synchronously without yielding,
    // so JavaScript's event loop guarantees no interleaving.
    for (const attempt of pendingResults) {
      if (attempt.result) {
        results.set(attempt.hash, attempt.result);

        // Only cache successful annotations (not fallbacks)
        if (!attempt.error) {
          this.cache.set(attempt.result);
        }
      }
    }

    return results;
  }

  /**
   * Get annotation errors from the last batch (for diagnostics).
   */
  getLastBatchErrors(): AnnotationError[] {
    // Could store errors from last batch if needed
    return [];
  }
}
```

### Success Criteria

#### Automated Verification:
- [ ] `npm run typecheck` passes
- [ ] Unit tests for HaikuAnnotator pass (with mocked API)
- [ ] Unit tests for AnnotationCache pass
- [ ] Unit tests for BatchAnnotator pass
- [ ] Integration test with real Haiku API (optional, requires API key)

#### Manual Verification:
- [ ] Haiku generates accurate DO annotations for sample functions
- [ ] Cache correctly stores and retrieves annotations
- [ ] Batch annotator respects concurrency limits
- [ ] Progress callback reports correctly

---

╔═════════════════════════════════════════════════════════════════════════════╗
║                              PHASE 4                                         ║
║                       Git Diff Invalidation Pipeline                         ║
╚═════════════════════════════════════════════════════════════════════════════╝

## Phase 4: Git Diff Invalidation

### Overview

Implement the invalidation pipeline that detects file changes via git diff, identifies affected functions using tree-sitter, marks stale nodes, and propagates staleness to chains via the reverse index.

### Changes Required

#### 1. Git Diff Detector

**File**: `src/invalidation/git-diff.ts`
```typescript
import { execSync } from 'child_process';
import { join } from 'path';

/**
 * Result of git diff analysis.
 */
export interface GitDiffResult {
  /** Files that were modified */
  modifiedFiles: string[];
  /** Files that were added */
  addedFiles: string[];
  /** Files that were deleted */
  deletedFiles: string[];
  /** Current HEAD commit */
  currentCommit: string;
}

/**
 * Get changed files since a specific commit.
 */
export function getChangedFilesSince(
  projectPath: string,
  sinceCommit: string
): GitDiffResult {
  const currentCommit = execSync('git rev-parse HEAD', {
    cwd: projectPath,
    encoding: 'utf-8',
  }).trim();

  if (!sinceCommit) {
    // No previous commit, treat all files as new
    const allFiles = execSync('git ls-files "*.ts" "*.tsx"', {
      cwd: projectPath,
      encoding: 'utf-8',
    }).trim().split('\n').filter(Boolean);

    return {
      modifiedFiles: [],
      addedFiles: allFiles,
      deletedFiles: [],
      currentCommit,
    };
  }

  // Get diff with status
  const diffOutput = execSync(
    `git diff --name-status ${sinceCommit}..HEAD -- "*.ts" "*.tsx"`,
    { cwd: projectPath, encoding: 'utf-8' }
  ).trim();

  const modifiedFiles: string[] = [];
  const addedFiles: string[] = [];
  const deletedFiles: string[] = [];

  for (const line of diffOutput.split('\n').filter(Boolean)) {
    const [status, ...pathParts] = line.split('\t');
    const filePath = pathParts.join('\t');  // Handle paths with tabs

    switch (status[0]) {
      case 'M':
        modifiedFiles.push(filePath);
        break;
      case 'A':
        addedFiles.push(filePath);
        break;
      case 'D':
        deletedFiles.push(filePath);
        break;
      case 'R':
        // Rename: old path is deleted, new path is added
        deletedFiles.push(filePath);
        if (pathParts[1]) addedFiles.push(pathParts[1]);
        break;
    }
  }

  return { modifiedFiles, addedFiles, deletedFiles, currentCommit };
}

/**
 * Get current HEAD commit.
 */
export function getCurrentCommit(projectPath: string): string {
  return execSync('git rev-parse HEAD', {
    cwd: projectPath,
    encoding: 'utf-8',
  }).trim();
}
```

#### 2. Staleness Manager

**File**: `src/invalidation/staleness.ts`
```typescript
import { readFileSync } from 'fs';
import { join } from 'path';
import type { ChainMap } from '../model/chain-map.js';
import type { ChainId, NodeId, GitCommit } from '../model/types.js';
import { extractFunctions, hashBody } from '../parser/extractor.js';
import { getChangedFilesSince, getCurrentCommit } from './git-diff.js';

/**
 * Result of invalidation check.
 */
export interface InvalidationResult {
  /** Nodes that were marked stale */
  staleNodes: NodeId[];
  /** Chains that were marked stale (via reverse index) */
  staleChains: ChainId[];
  /** Nodes that were deleted (file removed) */
  deletedNodes: NodeId[];
  /** New commit after invalidation */
  currentCommit: GitCommit;
}

/**
 * Check for staleness and invalidate affected nodes/chains.
 */
export function checkAndInvalidate(
  chainMap: ChainMap,
  projectPath: string,
  lastCommit: GitCommit
): InvalidationResult {
  const diff = getChangedFilesSince(projectPath, lastCommit);

  const staleNodes: NodeId[] = [];
  const allStaleChains = new Set<ChainId>();
  const deletedNodes: NodeId[] = [];

  // Handle deleted files
  for (const file of diff.deletedFiles) {
    const nodesInFile = chainMap.getNodesInFile(file);
    for (const node of nodesInFile) {
      deletedNodes.push(node.id);
      const affectedChains = chainMap.invalidateNode(node.id);
      for (const chainId of affectedChains) {
        allStaleChains.add(chainId);
      }
    }
  }

  // Handle modified and added files
  const filesToCheck = [...diff.modifiedFiles, ...diff.addedFiles];

  for (const file of filesToCheck) {
    try {
      const fullPath = join(projectPath, file);
      const code = readFileSync(fullPath, 'utf-8');
      const extracted = extractFunctions(code, file);

      // Build map of current function hashes
      const currentHashes = new Map<string, string>();
      for (const func of extracted) {
        const key = `${file}::${func.name}`;
        currentHashes.set(key, func.bodyHash);
      }

      // Check existing nodes in this file
      const existingNodes = chainMap.getNodesInFile(file);
      for (const node of existingNodes) {
        const key = `${node.file}::${node.name}`;
        const currentHash = currentHashes.get(key);

        if (!currentHash) {
          // Function was removed
          deletedNodes.push(node.id);
          const affectedChains = chainMap.invalidateNode(node.id);
          for (const chainId of affectedChains) {
            allStaleChains.add(chainId);
          }
        } else if (currentHash !== node.bodyHash) {
          // Function body changed
          staleNodes.push(node.id);
          const affectedChains = chainMap.invalidateNode(node.id);
          for (const chainId of affectedChains) {
            allStaleChains.add(chainId);
          }
        }
      }
    } catch (error) {
      console.warn(`Failed to process ${file}:`, error);
    }
  }

  return {
    staleNodes,
    staleChains: Array.from(allStaleChains),
    deletedNodes,
    currentCommit: diff.currentCommit,
  };
}
```

### Success Criteria

#### Automated Verification:
- [ ] `npm run typecheck` passes
- [ ] Unit tests for git-diff pass (with git test repo)
- [ ] Unit tests for staleness pass
- [ ] Integration test: modify file → correct nodes invalidated

#### Manual Verification:
- [ ] Correctly detects file modifications
- [ ] Correctly identifies changed functions by body hash
- [ ] Reverse index propagates staleness to chains
- [ ] Handles deleted files gracefully

---

╔═════════════════════════════════════════════════════════════════════════════╗
║                              PHASE 5                                         ║
║                        Staged Context Pipeline                               ║
╚═════════════════════════════════════════════════════════════════════════════╝

## Phase 5: Staged Context Pipeline

### Overview

Implement the 4-stage context pipeline:
1. **Trace**: Build chain from entry point to leaf functions
2. **Review**: Validate contracts, detect gaps
3. **Revise**: Expand scope if gaps found, loop until complete
4. **Generate**: Build curated working context

### Changes Required

#### 0. Pipeline Progress Interface (Added from Review)

**File**: `src/pipeline/progress.ts`

> **Why This Matters**: Long-running pipelines (Trace→Review→Revise→Generate) need progress reporting so CLI doesn't appear frozen.

```typescript
/**
 * Pipeline stage identifiers.
 */
export type PipelineStage = 'trace' | 'review' | 'revise' | 'generate';

/**
 * Progress event for pipeline stages.
 */
export interface PipelineProgressEvent {
  stage: PipelineStage;
  status: 'started' | 'progress' | 'completed' | 'failed';
  message: string;
  /** Progress as percentage (0-100) */
  progress?: number;
  /** Additional details */
  details?: Record<string, unknown>;
}

/**
 * Progress callback for pipeline stages.
 */
export type PipelineProgressCallback = (event: PipelineProgressEvent) => void;

/**
 * Options for pipeline execution.
 */
export interface PipelineOptions {
  /** Progress callback for all stages */
  onProgress?: PipelineProgressCallback;
  /** AbortController signal for cancellation */
  signal?: AbortSignal;
  /** Maximum revision iterations (default: 5) */
  maxRevisionIterations?: number;
  /** Maximum scope expansions per iteration (default: 3) */
  maxExpansionsPerIteration?: number;
}

/**
 * Check if operation should abort.
 */
export function checkAbort(signal?: AbortSignal): void {
  if (signal?.aborted) {
    throw new Error('Pipeline aborted');
  }
}

/**
 * Report progress if callback provided.
 */
export function reportProgress(
  callback: PipelineProgressCallback | undefined,
  stage: PipelineStage,
  status: PipelineProgressEvent['status'],
  message: string,
  progress?: number,
  details?: Record<string, unknown>
): void {
  if (callback) {
    callback({ stage, status, message, progress, details });
  }
}
```

#### 1. Stage 1: Trace

**File**: `src/pipeline/trace.ts`
```typescript
import { readFileSync } from 'fs';
import { join } from 'path';
import type { ChainMap } from '../model/chain-map.js';
import type { Chain } from '../model/chain.js';
import type { FunctionNode } from '../model/node.js';
import type { NodeId, ChainId, GitCommit } from '../model/types.js';
import { createChain } from '../model/chain.js';
import { createNodeId } from '../model/node.js';
import { extractFunctions } from '../parser/extractor.js';
import { buildCallGraph, traceChain } from '../parser/call-graph.js';
import { getCurrentCommit } from '../invalidation/git-diff.js';

/**
 * Result of tracing operation.
 */
export interface TraceResult {
  chain: Chain;
  nodes: FunctionNode[];
  /** Functions called but not found in traced files */
  unresolvedCalls: string[];
}

/**
 * Stage 1: Trace a function chain from an entry point.
 *
 * @param entryFile - File containing the entry function
 * @param entryFunctionName - Name of the entry function
 * @param operationName - Name for the chain (e.g., "user_login")
 * @param projectPath - Root of the project
 * @param filesToScan - Files to scan for function definitions
 */
export function traceOperation(
  entryFile: string,
  entryFunctionName: string,
  operationName: string,
  projectPath: string,
  filesToScan: string[]
): TraceResult {
  // Extract functions from all files
  const allFunctions: FunctionNode[] = [];
  for (const file of filesToScan) {
    try {
      const fullPath = join(projectPath, file);
      const code = readFileSync(fullPath, 'utf-8');
      const extracted = extractFunctions(code, file);

      for (const func of extracted) {
        const node: FunctionNode = {
          id: createNodeId(func.file, func.name, func.startByte),
          name: func.name,
          file: func.file,
          startLine: func.startLine,
          endLine: func.endLine,
          startByte: func.startByte,
          endByte: func.endByte,
          inContract: func.inContract,
          outContract: func.outContract,
          doAnnotation: null,  // Will be filled by annotator
          calls: [],  // Will be filled by call graph
          bodyHash: func.bodyHash,
          lastValidCommit: getCurrentCommit(projectPath),
          isStale: false,
        };
        allFunctions.push(node);
      }
    } catch (error) {
      console.warn(`Failed to extract from ${file}:`, error);
    }
  }

  // Build call graph
  const callGraph = buildCallGraph(
    allFunctions.map(n => ({
      name: n.name,
      file: n.file,
      startByte: n.startByte,
      callSites: [],  // Re-extract for call sites
      // ... other fields from ExtractedFunction
    }))
  );

  // Resolve calls for each node
  for (const node of allFunctions) {
    node.calls = callGraph.get(node.id) || [];
  }

  // Find entry node
  const entryNode = allFunctions.find(
    n => n.file === entryFile && n.name === entryFunctionName
  );

  if (!entryNode) {
    throw new Error(`Entry function ${entryFunctionName} not found in ${entryFile}`);
  }

  // Trace chain from entry
  const reachableIds = traceChain(entryNode.id, callGraph);

  // Create chain
  const chain = createChain(
    operationName as ChainId,
    `Operation: ${operationName}`,
    entryNode.id,
    getCurrentCommit(projectPath)
  );
  chain.nodeIds = reachableIds;

  // Collect nodes in chain
  const nodesInChain = allFunctions.filter(n => reachableIds.has(n.id));

  // Find unresolved calls
  const unresolvedCalls: string[] = [];
  // (Logic to find calls to functions not in our traced set)

  return {
    chain,
    nodes: nodesInChain,
    unresolvedCalls,
  };
}
```

#### 2. Stage 2: Review

**File**: `src/pipeline/review.ts`
```typescript
import type { Chain } from '../model/chain.js';
import type { FunctionNode } from '../model/node.js';
import type { NodeId } from '../model/types.js';

/**
 * Types of gaps detected during review.
 */
export type GapType =
  | 'missing_do_annotation'
  | 'contract_mismatch'
  | 'missing_dependency'
  | 'implicit_state'
  | 'unresolved_call';

/**
 * A gap or inconsistency found during review.
 */
export interface Gap {
  type: GapType;
  nodeId?: NodeId;
  description: string;
  severity: 'error' | 'warning';
}

/**
 * Result of review stage.
 */
export interface ReviewResult {
  gaps: Gap[];
  isComplete: boolean;
}

/**
 * Stage 2: Review chain for gaps and inconsistencies.
 */
export function reviewChain(
  chain: Chain,
  nodes: Map<NodeId, FunctionNode>
): ReviewResult {
  const gaps: Gap[] = [];

  for (const nodeId of chain.nodeIds) {
    const node = nodes.get(nodeId);
    if (!node) {
      gaps.push({
        type: 'missing_dependency',
        nodeId,
        description: `Node ${nodeId} is in chain but not found in node map`,
        severity: 'error',
      });
      continue;
    }

    // Check for missing DO annotation
    if (!node.doAnnotation) {
      gaps.push({
        type: 'missing_do_annotation',
        nodeId,
        description: `Function ${node.name} has no DO annotation`,
        severity: 'warning',
      });
    }

    // Check for contract mismatches (caller OUT → callee IN)
    for (const calleeId of node.calls) {
      const callee = nodes.get(calleeId);
      if (!callee) {
        gaps.push({
          type: 'unresolved_call',
          nodeId,
          description: `${node.name} calls unresolved function ${calleeId}`,
          severity: 'warning',
        });
        continue;
      }

      // Basic contract compatibility check
      // (More sophisticated checking could compare types)
      if (callee.inContract.parameters.length > 0) {
        // Has parameters - assume caller provides them (simplified)
      }
    }

    // Check for implicit state (heuristic: uses 'this.' without being a method)
    // (Simplified - real implementation would analyze AST more deeply)
  }

  return {
    gaps,
    isComplete: gaps.filter(g => g.severity === 'error').length === 0,
  };
}
```

#### 3. Stage 3: Revise

**File**: `src/pipeline/revise.ts`
```typescript
import type { Gap, ReviewResult } from './review.js';
import type { TraceResult } from './trace.js';
import type { FunctionNode } from '../model/node.js';

/**
 * Revision action to take.
 */
export interface RevisionAction {
  type: 'expand_scope' | 'annotate' | 'manual_review';
  description: string;
  targets: string[];
}

/**
 * Stage 3: Determine revision actions based on gaps.
 */
export function determineRevisions(
  reviewResult: ReviewResult,
  traceResult: TraceResult
): RevisionAction[] {
  const actions: RevisionAction[] = [];

  // Group gaps by type
  const missingAnnotations = reviewResult.gaps.filter(g => g.type === 'missing_do_annotation');
  const unresolvedCalls = reviewResult.gaps.filter(g => g.type === 'unresolved_call');
  const missingDeps = reviewResult.gaps.filter(g => g.type === 'missing_dependency');

  // Action: Annotate functions missing DO
  if (missingAnnotations.length > 0) {
    actions.push({
      type: 'annotate',
      description: `Generate DO annotations for ${missingAnnotations.length} functions`,
      targets: missingAnnotations.map(g => g.nodeId!).filter(Boolean),
    });
  }

  // Action: Expand scope for unresolved calls
  if (unresolvedCalls.length > 0 || traceResult.unresolvedCalls.length > 0) {
    actions.push({
      type: 'expand_scope',
      description: `Expand trace to include unresolved dependencies`,
      targets: [...unresolvedCalls.map(g => g.description), ...traceResult.unresolvedCalls],
    });
  }

  // Action: Manual review for complex issues
  const complexGaps = reviewResult.gaps.filter(g =>
    g.type === 'contract_mismatch' || g.type === 'implicit_state'
  );
  if (complexGaps.length > 0) {
    actions.push({
      type: 'manual_review',
      description: `Review ${complexGaps.length} potential contract/state issues`,
      targets: complexGaps.map(g => g.description),
    });
  }

  return actions;
}

/**
 * Check if revision loop should continue.
 * Enhanced with expansion tracking to prevent infinite loops (from review).
 */
export function shouldContinueRevision(
  reviewResult: ReviewResult,
  iterationCount: number,
  expansionCount: number,
  options?: {
    maxIterations?: number;
    maxExpansions?: number;
  }
): { continue: boolean; reason: string } {
  const maxIterations = options?.maxIterations ?? 5;
  const maxExpansions = options?.maxExpansions ?? 10;

  // Stop if complete
  if (reviewResult.isComplete) {
    return { continue: false, reason: 'Pipeline complete' };
  }

  // Stop if max iterations reached
  if (iterationCount >= maxIterations) {
    return { continue: false, reason: `Max iterations (${maxIterations}) reached` };
  }

  // Stop if max expansions reached (prevents infinite expand_scope loops)
  if (expansionCount >= maxExpansions) {
    return { continue: false, reason: `Max expansions (${maxExpansions}) reached` };
  }

  // Stop if only warnings remain
  const hasErrors = reviewResult.gaps.some(g => g.severity === 'error');
  if (!hasErrors) {
    return { continue: false, reason: 'Only warnings remaining' };
  }

  return { continue: true, reason: 'Errors require resolution' };
}

/**
 * Count expand_scope actions in revision list.
 */
export function countExpansions(actions: RevisionAction[]): number {
  return actions.filter(a => a.type === 'expand_scope').length;
}
```

#### 4. Stage 4: Generate

**File**: `src/pipeline/generate.ts`
```typescript
import type { Chain } from '../model/chain.js';
import type { FunctionNode } from '../model/node.js';
import type { NodeId } from '../model/types.js';

/**
 * Working context for LLM consumption.
 */
export interface WorkingContext {
  /** Operation being performed */
  operation: string;

  /** Entry point summary */
  entryPoint: {
    name: string;
    file: string;
    signature: string;
    description: string;
  };

  /** Function chain with contracts */
  chain: Array<{
    name: string;
    file: string;
    in: string;
    do: string;
    out: string;
    calls: string[];
  }>;

  /** Total context size (characters) */
  contextSize: number;
}

/**
 * Stage 4: Generate curated working context from validated chain.
 */
export function generateWorkingContext(
  chain: Chain,
  nodes: Map<NodeId, FunctionNode>
): WorkingContext {
  const entryNode = nodes.get(chain.entryNodeId);
  if (!entryNode) {
    throw new Error(`Entry node ${chain.entryNodeId} not found`);
  }

  const chainData: WorkingContext['chain'] = [];

  for (const nodeId of chain.nodeIds) {
    const node = nodes.get(nodeId);
    if (!node) continue;

    chainData.push({
      name: node.name,
      file: node.file,
      in: formatInContract(node),
      do: node.doAnnotation?.action || '[No annotation]',
      out: formatOutContract(node),
      calls: node.calls.map(id => {
        const callee = nodes.get(id);
        return callee?.name || id;
      }),
    });
  }

  // Sort by call depth (entry first, leaves last)
  // (Simplified - real implementation would do topological sort)

  const context: WorkingContext = {
    operation: chain.description,
    entryPoint: {
      name: entryNode.name,
      file: entryNode.file,
      signature: entryNode.inContract.signature,
      description: entryNode.doAnnotation?.action || '',
    },
    chain: chainData,
    contextSize: 0,
  };

  // Calculate context size
  context.contextSize = JSON.stringify(context).length;

  return context;
}

/**
 * Format IN contract for display.
 */
function formatInContract(node: FunctionNode): string {
  return node.inContract.parameters
    .map(p => `${p.name}: ${p.type}${p.optional ? '?' : ''}`)
    .join(', ');
}

/**
 * Format OUT contract for display.
 */
function formatOutContract(node: FunctionNode): string {
  const base = node.outContract.returnType;
  const errors = node.outContract.errorTypes;
  if (errors.length > 0) {
    return `${base} | throws ${errors.join(' | ')}`;
  }
  return base;
}

/**
 * Format working context as markdown for LLM prompt.
 */
export function formatContextAsMarkdown(context: WorkingContext): string {
  let md = `# Operation: ${context.operation}\n\n`;

  md += `## Entry Point\n`;
  md += `- **Function**: \`${context.entryPoint.name}\`\n`;
  md += `- **File**: \`${context.entryPoint.file}\`\n`;
  md += `- **Signature**: \`${context.entryPoint.signature}\`\n`;
  md += `- **Description**: ${context.entryPoint.description}\n\n`;

  md += `## Function Chain\n\n`;
  md += `| Function | File | IN | DO | OUT |\n`;
  md += `|----------|------|----|----|-----|\n`;

  for (const func of context.chain) {
    md += `| ${func.name} | ${func.file} | ${func.in || '-'} | ${func.do} | ${func.out} |\n`;
  }

  md += `\n*Context size: ${context.contextSize} characters*\n`;

  return md;
}
```

### Success Criteria

#### Automated Verification:
- [ ] `npm run typecheck` passes
- [ ] Unit tests for trace pass
- [ ] Unit tests for review pass
- [ ] Unit tests for revise pass
- [ ] Unit tests for generate pass
- [ ] Integration test: full 4-stage pipeline

#### Manual Verification:
- [ ] Trace correctly builds chain from entry point
- [ ] Review detects missing annotations and contract issues
- [ ] Revise loop terminates correctly
- [ ] Generated context is focused and useful for LLM

---

╔═════════════════════════════════════════════════════════════════════════════╗
║                              PHASE 6                                         ║
║                          CWA Integration                                     ║
╚═════════════════════════════════════════════════════════════════════════════╝

## Phase 6: CWA Integration

### Overview

Integrate the chain map with CWA (Context Window Array) Central Context Store. This enables the chain map to participate in the four-layer memory architecture.

### Changes Required

#### 0. CWA EntryType Extension (CRITICAL - Added from Review)

**File to modify**: `silmari-Context-Engine/context_window_array/models.py`

> **Why This Is Critical**: The original plan used `entryType: 'CHAIN_MAP'` as a string literal, but CWA's `EntryType.from_string()` will reject unknown types with a `ValueError`. We must extend the existing enum.

```python
# In context_window_array/models.py
# Add to the EntryType enum:

class EntryType(Enum):
    # ... existing types ...
    THOUGHT = "thought"
    CODE_CONTEXT = "code_context"
    SEARCH_RESULT = "search_result"
    # ... etc ...

    # NEW: Chain Map entry type (added for function chain map integration)
    CHAIN_MAP = "chain_map"
```

This change must be made BEFORE implementing the TypeScript sync module.

#### 1. CWA Sync Module (Enhanced from Review)

**File**: `src/integration/cwa-sync.ts`
```typescript
import type { ChainMap } from '../model/chain-map.js';
import type { Chain } from '../model/chain.js';
import type { FunctionNode } from '../model/node.js';
import type { WorkingContext } from '../pipeline/generate.js';

/**
 * Protocol version for CWA chain entries.
 * Increment on breaking changes to entry format.
 */
export const CWA_CHAIN_PROTOCOL_VERSION = 1;

/**
 * CWA entry type for chain map data.
 * NOTE: Uses 'chain_map' (snake_case) to match CWA EntryType enum.
 */
export interface CWAChainEntry {
  /** Protocol version for compatibility checking */
  protocolVersion: typeof CWA_CHAIN_PROTOCOL_VERSION;
  /** Entry type - MUST match CWA EntryType.CHAIN_MAP value */
  entryType: 'chain_map';  // snake_case to match Python enum
  chainId: string;
  operation: string;
  entryPoint: string;
  nodeCount: number;
  contextSize: number;
  workingContext: WorkingContext;
  lastUpdated: Date;
}

/**
 * Interface to CWA Central Context Store.
 * This is a placeholder - actual implementation will import from silmari-Context-Engine.
 */
export interface CWAStore {
  addEntry(entry: CWAChainEntry): string;  // Returns entry ID
  getEntry(id: string): CWAChainEntry | null;
  searchEntries(query: string): CWAChainEntry[];
  removeEntry(id: string): void;
}

/**
 * Sync chain map data to CWA store.
 * Enhanced with protocol version checking (from review).
 */
export class CWASync {
  private store: CWAStore;
  private entryIdMap: Map<string, string> = new Map();  // chainId → CWA entry ID

  constructor(store: CWAStore) {
    this.store = store;
  }

  /**
   * Push a working context to CWA.
   */
  pushContext(chainId: string, context: WorkingContext): string {
    const entry: CWAChainEntry = {
      protocolVersion: CWA_CHAIN_PROTOCOL_VERSION,
      entryType: 'chain_map',  // snake_case to match Python enum
      chainId,
      operation: context.operation,
      entryPoint: context.entryPoint.name,
      nodeCount: context.chain.length,
      contextSize: context.contextSize,
      workingContext: context,
      lastUpdated: new Date(),
    };

    // Remove old entry if exists
    const existingId = this.entryIdMap.get(chainId);
    if (existingId) {
      this.store.removeEntry(existingId);
    }

    // Add new entry
    const newId = this.store.addEntry(entry);
    this.entryIdMap.set(chainId, newId);

    return newId;
  }

  /**
   * Get context from CWA by chain ID.
   */
  getContext(chainId: string): WorkingContext | null {
    const entryId = this.entryIdMap.get(chainId);
    if (!entryId) return null;

    const entry = this.store.getEntry(entryId);
    return entry?.workingContext || null;
  }

  /**
   * Search for relevant contexts.
   */
  searchContexts(query: string): WorkingContext[] {
    const entries = this.store.searchEntries(query);
    return entries.map(e => e.workingContext);
  }

  /**
   * Remove context from CWA.
   */
  removeContext(chainId: string): void {
    const entryId = this.entryIdMap.get(chainId);
    if (entryId) {
      this.store.removeEntry(entryId);
      this.entryIdMap.delete(chainId);
    }
  }
}
```

### Success Criteria

#### Automated Verification:
- [ ] `npm run typecheck` passes
- [ ] Unit tests for CWASync pass (with mock store)
- [ ] Integration test with actual CWA store (when available)

#### Manual Verification:
- [ ] Contexts correctly pushed to CWA
- [ ] Search returns relevant contexts
- [ ] Old entries correctly replaced on update

---

╔═════════════════════════════════════════════════════════════════════════════╗
║                              PHASE 7                                         ║
║                           CLI & Testing                                      ║
╚═════════════════════════════════════════════════════════════════════════════╝

## Phase 7: CLI & Testing

### Overview

Implement the CLI interface and comprehensive test suite.

### Changes Required

#### 0. Programmatic API Exports (Added from Review)

**File**: `src/index.ts`

> **Why This Matters**: The original plan only provided CLI access, making it impossible to integrate into other tools without spawning subprocess. This exports programmatic API.

```typescript
/**
 * silmari-chain-map - Function Chain Map for Staged Context Pipeline
 *
 * This module can be used as a library (import) or via CLI.
 */

// ─────────────────────────────────────────────────────────────
// Core Data Models
// ─────────────────────────────────────────────────────────────
export { ChainMap } from './model/chain-map.js';
export { createNodeId, parseNodeId } from './model/node.js';
export { createChain } from './model/chain.js';
export type {
  NodeId,
  ChainId,
  GitCommit,
  BodyHash,
  InContract,
  OutContract,
  DoAnnotation,
} from './model/types.js';
export type { FunctionNode } from './model/node.js';
export type { Chain } from './model/chain.js';

// ─────────────────────────────────────────────────────────────
// Error Types
// ─────────────────────────────────────────────────────────────
export {
  ParseError,
  AnnotationError,
  DatabaseError,
} from './model/types.js';

// ─────────────────────────────────────────────────────────────
// Database Layer
// ─────────────────────────────────────────────────────────────
export { DbConnection } from './db/connection.js';
export { ChainMapRepository } from './db/repository.js';

// ─────────────────────────────────────────────────────────────
// Annotation
// ─────────────────────────────────────────────────────────────
export type { AnnotationProvider, AnnotationOptions, BatchAnnotationOptions } from './annotator/provider.js';
export { MockAnnotationProvider } from './annotator/provider.js';
export { HaikuAnnotator } from './annotator/haiku-client.js';
export { AnnotationCache } from './annotator/cache.js';
export { BatchAnnotator } from './annotator/batch.js';

// ─────────────────────────────────────────────────────────────
// Parser
// ─────────────────────────────────────────────────────────────
export { extractFunctions, hashBody } from './parser/extractor.js';
export type { ExtractedFunction } from './parser/extractor.js';
export { buildCallGraph, traceChain } from './parser/call-graph.js';

// ─────────────────────────────────────────────────────────────
// Pipeline
// ─────────────────────────────────────────────────────────────
export { traceOperation } from './pipeline/trace.js';
export type { TraceResult } from './pipeline/trace.js';
export { reviewChain } from './pipeline/review.js';
export type { ReviewResult, Gap, GapType } from './pipeline/review.js';
export { determineRevisions, shouldContinueRevision, countExpansions } from './pipeline/revise.js';
export type { RevisionAction } from './pipeline/revise.js';
export { generateWorkingContext, formatContextAsMarkdown } from './pipeline/generate.js';
export type { WorkingContext } from './pipeline/generate.js';
export type { PipelineProgressEvent, PipelineProgressCallback, PipelineOptions } from './pipeline/progress.js';
export { checkAbort, reportProgress } from './pipeline/progress.js';

// ─────────────────────────────────────────────────────────────
// Invalidation
// ─────────────────────────────────────────────────────────────
export { getChangedFilesSince, getCurrentCommit } from './invalidation/git-diff.js';
export type { GitDiffResult } from './invalidation/git-diff.js';
export { checkAndInvalidate } from './invalidation/staleness.js';
export type { InvalidationResult } from './invalidation/staleness.js';

// ─────────────────────────────────────────────────────────────
// CWA Integration
// ─────────────────────────────────────────────────────────────
export { CWASync, CWA_CHAIN_PROTOCOL_VERSION } from './integration/cwa-sync.js';
export type { CWAChainEntry, CWAStore } from './integration/cwa-sync.js';
```

#### 1. Exit Codes (Added from Review)

**File**: `src/cli/exit-codes.ts`

> **Why This Matters**: CLI scripts need to distinguish between different failure types for automation.

```typescript
/**
 * CLI exit codes for automation support.
 */
export const EXIT_CODES = {
  /** Successful execution */
  SUCCESS: 0,
  /** Invalid arguments or usage */
  INVALID_ARGS: 1,
  /** Database error (locked, corrupt, disk full) */
  DATABASE_ERROR: 2,
  /** Parse error (syntax error, file not found) */
  PARSE_ERROR: 3,
  /** API error (rate limit, timeout, network) */
  API_ERROR: 4,
  /** Validation error (contract mismatch, missing dependency) */
  VALIDATION_ERROR: 5,
  /** Git error (not a repo, invalid commit) */
  GIT_ERROR: 6,
  /** User cancellation (Ctrl+C) */
  CANCELLED: 130,
} as const;

export type ExitCode = typeof EXIT_CODES[keyof typeof EXIT_CODES];

/**
 * Exit with appropriate code based on error type.
 */
export function exitWithError(error: unknown): never {
  if (error instanceof Error) {
    console.error(`Error: ${error.message}`);

    // Determine exit code based on error type/name
    if (error.name === 'ParseError') {
      process.exit(EXIT_CODES.PARSE_ERROR);
    } else if (error.name === 'AnnotationError') {
      process.exit(EXIT_CODES.API_ERROR);
    } else if (error.name === 'DatabaseError') {
      process.exit(EXIT_CODES.DATABASE_ERROR);
    } else if (error.message.includes('not a git repository')) {
      process.exit(EXIT_CODES.GIT_ERROR);
    }
  }

  process.exit(EXIT_CODES.VALIDATION_ERROR);
}
```

#### 2. CLI Entry Point (Enhanced)

**File**: `src/cli/index.ts`
```typescript
import { Command } from 'commander';
import { DbConnection } from '../db/connection.js';
import { ChainMap } from '../model/chain-map.js';
import { ChainMapRepository } from '../db/repository.js';
import { traceOperation } from '../pipeline/trace.js';
import { reviewChain } from '../pipeline/review.js';
import { generateWorkingContext, formatContextAsMarkdown } from '../pipeline/generate.js';
import { checkAndInvalidate } from '../invalidation/staleness.js';
import { BatchAnnotator } from '../annotator/batch.js';
import { HaikuAnnotator } from '../annotator/haiku-client.js';
import { AnnotationCache } from '../annotator/cache.js';
import { EXIT_CODES, exitWithError } from './exit-codes.js';

const program = new Command();

// Global options (added from review)
program
  .name('chain-map')
  .description('Function Chain Map for Staged Context Pipeline')
  .version('0.1.0')
  .option('-v, --verbose', 'Enable verbose output')
  .option('-q, --quiet', 'Suppress non-essential output');

// Helper to get verbose/quiet flags
function getOutputOptions(): { verbose: boolean; quiet: boolean } {
  const opts = program.opts();
  return {
    verbose: opts.verbose ?? false,
    quiet: opts.quiet ?? false,
  };
}

// Helper to log if not quiet
function log(message: string): void {
  const { quiet } = getOutputOptions();
  if (!quiet) console.log(message);
}

// Helper to log if verbose
function verboseLog(message: string): void {
  const { verbose } = getOutputOptions();
  if (verbose) console.log(`[verbose] ${message}`);
}

// ─────────────────────────────────────────────────────────────
// init - Initialize database
// ─────────────────────────────────────────────────────────────
program
  .command('init')
  .description('Initialize the chain map database')
  .option('-d, --db <path>', 'Database path', '.chain-map.db')
  .action((options) => {
    try {
      verboseLog(`Initializing database at ${options.db}`);
      const db = new DbConnection(options.db);
      db.initializeSchema();
      log(`Initialized database at ${options.db}`);
      db.close();
      process.exit(EXIT_CODES.SUCCESS);
    } catch (error) {
      exitWithError(error);
    }
  });

// ─────────────────────────────────────────────────────────────
// trace - Build a function chain (uses ChainMapRepository)
// ─────────────────────────────────────────────────────────────
program
  .command('trace')
  .description('Trace a function chain from an entry point')
  .argument('<entry-file>', 'File containing entry function')
  .argument('<entry-function>', 'Name of entry function')
  .argument('<operation-name>', 'Name for the operation/chain')
  .option('-d, --db <path>', 'Database path', '.chain-map.db')
  .option('-f, --files <glob>', 'Files to scan', '**/*.ts')
  .option('-p, --project <path>', 'Project root path', '.')
  .action(async (entryFile, entryFunction, operationName, options) => {
    let db: DbConnection | null = null;
    try {
      verboseLog(`Opening database at ${options.db}`);
      db = new DbConnection(options.db);
      const repo = new ChainMapRepository(db.getDb());

      // Load existing chain map
      verboseLog('Loading existing chain map from database');
      const chainMap = repo.loadAll();

      log(`Tracing ${entryFunction} from ${entryFile} as "${operationName}"`);

      // Get files to scan (simplified - real impl would use glob)
      const filesToScan = [entryFile];  // Expand with glob in real impl

      // Trace operation
      const result = traceOperation(
        entryFile,
        entryFunction,
        operationName,
        options.project,
        filesToScan
      );

      // Add nodes and chain to map
      for (const node of result.nodes) {
        chainMap.addNode(node);
        repo.saveNode(node);  // Persist immediately
      }
      chainMap.addChain(result.chain);
      repo.saveChain(result.chain);  // Persist immediately

      log(`Traced chain "${operationName}" with ${result.nodes.length} nodes`);
      if (result.unresolvedCalls.length > 0) {
        log(`Warning: ${result.unresolvedCalls.length} unresolved calls`);
      }

      db.close();
      process.exit(EXIT_CODES.SUCCESS);
    } catch (error) {
      db?.close();
      exitWithError(error);
    }
  });

// ─────────────────────────────────────────────────────────────
// annotate - Generate DO annotations
// ─────────────────────────────────────────────────────────────
program
  .command('annotate')
  .description('Generate DO annotations for functions')
  .option('-d, --db <path>', 'Database path', '.chain-map.db')
  .option('-p, --parallel <n>', 'Parallelism', '10')
  .option('--dry-run', 'Show what would be annotated')
  .action(async (options) => {
    console.log('Generating DO annotations...');
    // ... annotate logic
  });

// ─────────────────────────────────────────────────────────────
// invalidate - Check git diff and mark stale
// ─────────────────────────────────────────────────────────────
program
  .command('invalidate')
  .description('Check for changes and invalidate stale nodes')
  .option('-d, --db <path>', 'Database path', '.chain-map.db')
  .action(async (options) => {
    console.log('Checking for invalidations...');
    // ... invalidate logic
  });

// ─────────────────────────────────────────────────────────────
// build-context - Run 4-stage pipeline
// ─────────────────────────────────────────────────────────────
program
  .command('build-context')
  .description('Build working context for a task')
  .argument('<task>', 'Task description or chain ID')
  .option('-d, --db <path>', 'Database path', '.chain-map.db')
  .option('-o, --output <format>', 'Output format (json|markdown)', 'markdown')
  .action(async (task, options) => {
    console.log(`Building context for: ${task}`);
    // ... pipeline logic
  });

// ─────────────────────────────────────────────────────────────
// stats - Show chain map statistics
// ─────────────────────────────────────────────────────────────
program
  .command('stats')
  .description('Show chain map statistics')
  .option('-d, --db <path>', 'Database path', '.chain-map.db')
  .action((options) => {
    // ... stats logic
  });

program.parse();
```

#### 2. Test Suite Structure

**File**: `tests/setup.ts`
```typescript
import { beforeAll, afterAll } from 'vitest';
import { DbConnection } from '../src/db/connection.js';
import { mkdtempSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

let testDir: string;
let testDb: DbConnection;

beforeAll(() => {
  testDir = mkdtempSync(join(tmpdir(), 'chain-map-test-'));
  testDb = new DbConnection(join(testDir, 'test.db'));
  testDb.initializeSchema();
});

afterAll(() => {
  testDb.close();
  rmSync(testDir, { recursive: true });
});

export { testDir, testDb };
```

**File**: `tests/model/chain-map.test.ts`
```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { ChainMap } from '../../src/model/chain-map.js';
import { createNodeId } from '../../src/model/node.js';
import { createChain } from '../../src/model/chain.js';
import type { FunctionNode } from '../../src/model/node.js';

describe('ChainMap', () => {
  let chainMap: ChainMap;

  beforeEach(() => {
    chainMap = new ChainMap();
  });

  describe('node operations', () => {
    it('should add and retrieve nodes', () => {
      const node: FunctionNode = {
        id: createNodeId('test.ts', 'foo', 0),
        name: 'foo',
        file: 'test.ts',
        startLine: 1,
        endLine: 10,
        startByte: 0,
        endByte: 100,
        inContract: { parameters: [], signature: '()' },
        outContract: { returnType: 'void', errorTypes: [], isAsync: false },
        doAnnotation: null,
        calls: [],
        bodyHash: 'abc123',
        lastValidCommit: 'def456',
        isStale: false,
      };

      chainMap.addNode(node);

      expect(chainMap.getNode(node.id)).toEqual(node);
    });
  });

  describe('invalidation', () => {
    it('should propagate staleness to chains via reverse index', () => {
      // Setup: create nodes and chain
      const node1 = createTestNode('a.ts', 'func1', 0);
      const node2 = createTestNode('b.ts', 'func2', 0);

      chainMap.addNode(node1);
      chainMap.addNode(node2);

      const chain = createChain('op1', 'Test operation', node1.id, 'commit1');
      chain.nodeIds.add(node2.id);
      chainMap.addChain(chain);

      // Invalidate node2
      const affected = chainMap.invalidateNode(node2.id);

      // Chain should be marked stale
      expect(affected).toContain('op1');
      expect(chainMap.getChain('op1')?.isStale).toBe(true);
    });
  });
});

function createTestNode(file: string, name: string, startByte: number): FunctionNode {
  return {
    id: createNodeId(file, name, startByte),
    name,
    file,
    startLine: 1,
    endLine: 10,
    startByte,
    endByte: startByte + 100,
    inContract: { parameters: [], signature: '()' },
    outContract: { returnType: 'void', errorTypes: [], isAsync: false },
    doAnnotation: null,
    calls: [],
    bodyHash: `hash_${name}`,
    lastValidCommit: 'commit1',
    isStale: false,
  };
}
```

### Success Criteria

#### Automated Verification:
- [ ] All unit tests pass: `npm test`
- [ ] CLI commands execute without errors
- [ ] Integration tests pass with sample codebase
- [ ] Test coverage > 80%

#### Manual Verification:
- [ ] CLI help is clear and complete
- [ ] CLI output is formatted correctly
- [ ] Error messages are helpful

---

## 🛡️ Testing Strategy

### Unit Tests

| Component | Test Focus | Coverage Target |
|-----------|------------|-----------------|
| ChainMap | Add/get/invalidate | 90% |
| Extractor | Function extraction | 85% |
| CallGraph | Edge building | 85% |
| HaikuAnnotator | Response parsing | 80% |
| AnnotationCache | CRUD operations | 90% |
| GitDiff | Diff parsing | 85% |
| Pipeline stages | Each stage | 80% |

### Integration Tests

1. **Full Pipeline Test**: Trace → Annotate → Review → Generate
2. **Invalidation Test**: Modify file → Check staleness propagation
3. **Cache Test**: Annotate → Re-annotate → Verify cache hits

### Manual Testing Steps

1. Initialize on a real TypeScript project
2. Trace a function chain from an API handler
3. Verify DO annotations are accurate
4. Modify a function and verify invalidation
5. Build context and review quality

---

## ⚡ Performance Considerations

| Operation | Target | Approach |
|-----------|--------|----------|
| Initial annotation (1000 funcs) | <5 min | Parallel Haiku calls (10 concurrent) |
| Incremental annotation (10 funcs) | <10 sec | Cache + parallel |
| Trace (100 node chain) | <1 sec | In-memory BFS |
| Context build | <2 sec | Pre-computed chain map |
| Invalidation check | <5 sec | Git diff + hash comparison |

### Optimizations

1. **Prepared SQLite statements** for frequent queries
2. **Body hash caching** to skip re-annotation
3. **Parallel Haiku calls** with configurable concurrency
4. **Incremental parsing** via tree-sitter

---

## 📚 References

- Research: `thoughts/searchable/shared/research/2026-01-04-context-window-array-architecture.md`
- CWA Implementation: `thoughts/searchable/shared/plans/2026-01-04-tdd-context-window-array/`
- Existing tree-sitter: `silmari-code-eval/src/utils/tree_sitter_analyzer.py`
- Function hashing: `silmari-code-eval/src/database/function_hash.py`
- Architecture docs: `silmari-Context-Engine/docs/ARCHITECTURE.md`

---

## 📋 Summary

This plan implements a **Staged Context Pipeline** with **Function Chain Map** to solve LLM performance degradation in large codebases. Key innovations:

1. **IN:DO:OUT contracts** for every function
2. **Deterministic/stochastic split** - only DO uses LLM
3. **Body-hash caching** - annotate once, cache forever
4. **Reverse index** - efficient invalidation propagation
5. **4-stage pipeline** - trace → review → revise → generate

The result is focused, validated context that scales with codebase size.
