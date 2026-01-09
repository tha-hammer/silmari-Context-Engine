# Rust Orchestrator Port TDD Implementation Plan

## Overview

Port the TypeScript orchestrator (`silmari-oracle-wui/src/orchestrator/orchestrator.ts`) to Rust (`silmari-oracle/src/orchestrator.rs`), implementing a complete, production-ready session orchestration system with incremental testable behaviors.

**Key Objective**: Full Rust rewrite of orchestration logic, designed for end-to-end functionality but implemented incrementally through TDD cycles.

## Current State Analysis

### TypeScript Implementation
The TypeScript orchestrator (`silmari-oracle-wui/src/orchestrator/orchestrator.ts:1-547`) provides:
- Session initialization and state management
- Multi-level context (files, thoughts, git, project)
- Active file tracking with content inclusion
- Thought retrieval and filtering
- Git status and branch information
- Project metadata extraction
- Session deduplication and naming
- Session state persistence (cache and SQLite)

**Key Discoveries:**
- Context building: `silmari-oracle-wui/src/orchestrator/orchestrator.ts:280-350`
- Active files: `silmari-oracle-wui/src/orchestrator/orchestrator.ts:352-395`
- Thought retrieval: `silmari-oracle-wui/src/orchestrator/orchestrator.ts:397-450`
- State persistence: `silmari-oracle-wui/src/orchestrator/orchestrator.ts:165-215`
- Session deduplication: `silmari-oracle-wui/src/orchestrator/orchestrator.ts:120-163`

### Rust Foundation
Current minimal implementation in `silmari-oracle/src/orchestrator.rs:1-50`:
- Basic trait structure (`OrchestratorTrait`)
- Minimal struct (`Orchestrator`)
- Placeholder methods returning empty/default values

### Test Infrastructure
- **Framework**: Rust built-in test framework (`#[cfg(test)]`, `#[test]`, `assert_eq!`)
- **Location**: Tests in same file as implementation (`mod tests { ... }`)
- **Patterns**: Unit tests for behavior, integration tests in `tests/` directory
- **Existing**: `silmari-oracle/tests/integration_test.rs` shows integration test pattern

## Desired End State

A complete Rust orchestrator that:
1. Initializes sessions with unique IDs and tracking
2. Manages session state with persistence (memory and SQLite)
3. Builds multi-level context (files, thoughts, git, project)
4. Tracks active files with content inclusion
5. Retrieves and filters thought documents
6. Provides git status and branch information
7. Extracts project metadata
8. Deduplicates sessions and generates contextual names

**Verification**: Full test suite passing (unit + integration + E2E), all behaviors working end-to-end.

## Observable Behaviors

1. **Session Initialization**: Given configuration, when initializing, then unique session created with timestamp and tracking state
2. **State Persistence**: Given session state, when persisting, then state saved to cache and database, retrievable on restart
3. **Context Building**: Given workspace, when building context, then multi-level context assembled (files, thoughts, git, project)
4. **Active File Tracking**: Given file list, when tracking active files, then file contents included in context with size limits
5. **Thought Retrieval**: Given thoughts directory, when retrieving thoughts, then filtered and categorized thought documents returned
6. **Git Information**: Given git repository, when requesting git info, then current branch, status, and changes provided
7. **Project Metadata**: Given workspace, when extracting metadata, then project name, type, and configuration detected
8. **Session Deduplication**: Given existing sessions, when creating new session, then duplicate contexts avoided and meaningful names generated

## What We're NOT Doing

- UI components or web server integration (handled by `silmari-oracle-wui`)
- Database schema changes (use existing schema from TypeScript)
- Complete API parity with every TypeScript method (focus on core behaviors)
- Performance optimization beyond basic best practices (premature optimization)
- Comprehensive error recovery strategies (basic error handling only)

## Testing Strategy

- **Framework**: Rust built-in (`#[test]`, `assert_eq!`, `assert!`, `assert_matches!`)
- **Test Types**:
  - **Unit**: Individual behavior functions (parsing, filtering, state management)
  - **Integration**: Component interactions (database + context builder, git + state manager)
  - **E2E**: Full orchestration flows (session init → context build → persist → retrieve)
- **Mocking/Setup**:
  - Temporary directories for filesystem tests (`tempfile` crate)
  - In-memory SQLite for database tests (`:memory:`)
  - Mock git repositories (`git2` test utilities)
  - Fixture files in `tests/fixtures/`

---

## Behavior 1: Session Initialization

### Test Specification

**Given**: Orchestrator configuration with workspace path
**When**: Initializing a new session
**Then**:
- Session has unique ID (timestamp-based)
- Session has creation timestamp
- Session state is `Active`
- Session metadata includes workspace path

**Edge Cases**:
- Invalid workspace path → Error
- Concurrent session creation → Unique IDs guaranteed
- Missing configuration → Default values used

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_initialize_session_creates_unique_id() {
        let config = OrchestratorConfig {
            workspace_path: PathBuf::from("/tmp/test-workspace"),
        };
        let orchestrator = Orchestrator::new(config);

        let session = orchestrator.initialize_session().unwrap();

        assert!(!session.id.is_empty());
        assert!(session.id.starts_with("session-"));
        assert!(session.created_at > 0);
        assert_eq!(session.state, SessionState::Active);
    }

    #[test]
    fn test_initialize_session_unique_ids() {
        let config = OrchestratorConfig {
            workspace_path: PathBuf::from("/tmp/test-workspace"),
        };
        let orchestrator = Orchestrator::new(config);

        let session1 = orchestrator.initialize_session().unwrap();
        let session2 = orchestrator.initialize_session().unwrap();

        assert_ne!(session1.id, session2.id);
    }

    #[test]
    fn test_initialize_session_invalid_workspace() {
        let config = OrchestratorConfig {
            workspace_path: PathBuf::from("/nonexistent/invalid/path"),
        };
        let orchestrator = Orchestrator::new(config);

        let result = orchestrator.initialize_session();
        assert!(result.is_err());
    }
}
```

**Expected Failure**: Compilation errors (missing types) and test failures (not implemented).

#### 🟢 Green: Minimal Implementation

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};
use anyhow::{Result, anyhow};

pub struct OrchestratorConfig {
    pub workspace_path: PathBuf,
}

#[derive(Debug, PartialEq)]
pub enum SessionState {
    Active,
    Completed,
    Error,
}

pub struct Session {
    pub id: String,
    pub created_at: u64,
    pub state: SessionState,
    pub workspace_path: PathBuf,
}

pub struct Orchestrator {
    config: OrchestratorConfig,
}

impl Orchestrator {
    pub fn new(config: OrchestratorConfig) -> Self {
        Self { config }
    }

    pub fn initialize_session(&self) -> Result<Session> {
        // Validate workspace path exists
        if !self.config.workspace_path.exists() {
            return Err(anyhow!("Workspace path does not exist"));
        }

        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_millis();

        let session = Session {
            id: format!("session-{}", timestamp),
            created_at: timestamp as u64,
            state: SessionState::Active,
            workspace_path: self.config.workspace_path.clone(),
        };

        Ok(session)
    }
}
```

**Run Tests**: `cargo test --lib orchestrator::tests::test_initialize_session`

#### 🔵 Refactor: Improve Code

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};
use anyhow::{Context, Result};
use uuid::Uuid;

pub struct OrchestratorConfig {
    pub workspace_path: PathBuf,
}

#[derive(Debug, PartialEq, Clone)]
pub enum SessionState {
    Active,
    Completed,
    Error,
}

#[derive(Debug, Clone)]
pub struct Session {
    pub id: String,
    pub created_at: u64,
    pub state: SessionState,
    pub workspace_path: PathBuf,
}

pub struct Orchestrator {
    config: OrchestratorConfig,
}

impl Orchestrator {
    pub fn new(config: OrchestratorConfig) -> Self {
        Self { config }
    }

    pub fn initialize_session(&self) -> Result<Session> {
        self.validate_workspace()?;

        let session = Session {
            id: Self::generate_session_id(),
            created_at: Self::current_timestamp()?,
            state: SessionState::Active,
            workspace_path: self.config.workspace_path.clone(),
        };

        Ok(session)
    }

    fn validate_workspace(&self) -> Result<()> {
        if !self.config.workspace_path.exists() {
            anyhow::bail!(
                "Workspace path does not exist: {}",
                self.config.workspace_path.display()
            );
        }
        Ok(())
    }

    fn generate_session_id() -> String {
        format!("session-{}", Uuid::new_v4())
    }

    fn current_timestamp() -> Result<u64> {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .context("Failed to get current timestamp")
            .map(|d| d.as_millis() as u64)
    }
}
```

**Refactorings**:
- Extracted `validate_workspace()` for clarity
- Extracted `generate_session_id()` using UUID for better uniqueness
- Extracted `current_timestamp()` with error handling
- Added `Clone` derives for easier testing
- Improved error messages

**Verify**: `cargo test --lib orchestrator::tests` (all tests pass)

### Success Criteria

**Automated:**
- [ ] Tests fail for right reason (Red): `cargo test --lib orchestrator::tests::test_initialize_session -- --nocapture`
- [ ] Tests pass (Green): `cargo test --lib orchestrator::tests::test_initialize_session`
- [ ] All tests pass after refactor: `cargo test --lib orchestrator::tests`
- [ ] Clippy passes: `cargo clippy -- -D warnings`
- [ ] Format check: `cargo fmt -- --check`

**Manual:**
- [ ] Session IDs are unique and well-formed
- [ ] Timestamps are accurate (within reasonable delta)
- [ ] Invalid workspace paths properly rejected
- [ ] No panics or unwraps in production code

---

## Behavior 2: State Persistence

### Test Specification

**Given**: Session with state
**When**: Persisting to cache and database
**Then**:
- Session saved to in-memory cache
- Session persisted to SQLite database
- Session retrievable by ID from both sources
- Cache and database contents consistent

**Edge Cases**:
- Database connection failure → Error propagated
- Concurrent writes → Last write wins (or error)
- Missing session ID on retrieval → None returned
- Database schema mismatch → Initialization creates schema

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use rusqlite::Connection;

    #[test]
    fn test_persist_session_to_cache() {
        let config = OrchestratorConfig {
            workspace_path: PathBuf::from("/tmp/test-workspace"),
        };
        let mut orchestrator = Orchestrator::new(config);

        let session = Session {
            id: "session-test-123".to_string(),
            created_at: 1704355200000,
            state: SessionState::Active,
            workspace_path: PathBuf::from("/tmp/test-workspace"),
        };

        orchestrator.persist_to_cache(&session).unwrap();

        let retrieved = orchestrator.get_from_cache(&session.id).unwrap();
        assert_eq!(retrieved.id, session.id);
        assert_eq!(retrieved.state, session.state);
    }

    #[test]
    fn test_persist_session_to_database() {
        let conn = Connection::open_in_memory().unwrap();
        let config = OrchestratorConfig {
            workspace_path: PathBuf::from("/tmp/test-workspace"),
        };
        let mut orchestrator = Orchestrator::with_connection(config, conn);

        let session = Session {
            id: "session-test-456".to_string(),
            created_at: 1704355200000,
            state: SessionState::Active,
            workspace_path: PathBuf::from("/tmp/test-workspace"),
        };

        orchestrator.persist_to_database(&session).unwrap();

        let retrieved = orchestrator.get_from_database(&session.id).unwrap().unwrap();
        assert_eq!(retrieved.id, session.id);
        assert_eq!(retrieved.state, session.state);
    }

    #[test]
    fn test_get_nonexistent_session() {
        let config = OrchestratorConfig {
            workspace_path: PathBuf::from("/tmp/test-workspace"),
        };
        let orchestrator = Orchestrator::new(config);

        let result = orchestrator.get_from_cache("nonexistent-id");
        assert!(result.is_none());
    }
}
```

**Expected Failure**: Compilation errors (missing methods) and test failures.

#### 🟢 Green: Minimal Implementation

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::collections::HashMap;
use rusqlite::{Connection, params};

pub struct Orchestrator {
    config: OrchestratorConfig,
    cache: HashMap<String, Session>,
    db: Option<Connection>,
}

impl Orchestrator {
    pub fn new(config: OrchestratorConfig) -> Self {
        Self {
            config,
            cache: HashMap::new(),
            db: None,
        }
    }

    pub fn with_connection(config: OrchestratorConfig, conn: Connection) -> Self {
        let mut orch = Self::new(config);
        orch.db = Some(conn);
        orch.initialize_database().ok();
        orch
    }

    pub fn persist_to_cache(&mut self, session: &Session) -> Result<()> {
        self.cache.insert(session.id.clone(), session.clone());
        Ok(())
    }

    pub fn get_from_cache(&self, session_id: &str) -> Option<Session> {
        self.cache.get(session_id).cloned()
    }

    pub fn persist_to_database(&mut self, session: &Session) -> Result<()> {
        let db = self.db.as_ref().context("No database connection")?;

        db.execute(
            "INSERT OR REPLACE INTO sessions (id, created_at, state, workspace_path) VALUES (?1, ?2, ?3, ?4)",
            params![
                session.id,
                session.created_at as i64,
                format!("{:?}", session.state),
                session.workspace_path.to_string_lossy().as_ref(),
            ],
        )?;

        Ok(())
    }

    pub fn get_from_database(&self, session_id: &str) -> Result<Option<Session>> {
        let db = self.db.as_ref().context("No database connection")?;

        let mut stmt = db.prepare("SELECT id, created_at, state, workspace_path FROM sessions WHERE id = ?1")?;
        let result = stmt.query_row(params![session_id], |row| {
            let state_str: String = row.get(2)?;
            let state = match state_str.as_str() {
                "Active" => SessionState::Active,
                "Completed" => SessionState::Completed,
                "Error" => SessionState::Error,
                _ => SessionState::Active,
            };

            Ok(Session {
                id: row.get(0)?,
                created_at: row.get::<_, i64>(1)? as u64,
                state,
                workspace_path: PathBuf::from(row.get::<_, String>(3)?),
            })
        });

        match result {
            Ok(session) => Ok(Some(session)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e.into()),
        }
    }

    fn initialize_database(&self) -> Result<()> {
        let db = self.db.as_ref().context("No database connection")?;

        db.execute(
            "CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at INTEGER NOT NULL,
                state TEXT NOT NULL,
                workspace_path TEXT NOT NULL
            )",
            [],
        )?;

        Ok(())
    }
}
```

**Run Tests**: `cargo test --lib orchestrator::tests::test_persist_session`

#### 🔵 Refactor: Improve Code

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use rusqlite::{Connection, params};
use serde::{Serialize, Deserialize};

// Add serialization for database storage
#[derive(Debug, PartialEq, Clone, Serialize, Deserialize)]
pub enum SessionState {
    Active,
    Completed,
    Error,
}

impl SessionState {
    fn to_string(&self) -> String {
        match self {
            SessionState::Active => "Active".to_string(),
            SessionState::Completed => "Completed".to_string(),
            SessionState::Error => "Error".to_string(),
        }
    }

    fn from_string(s: &str) -> Result<Self> {
        match s {
            "Active" => Ok(SessionState::Active),
            "Completed" => Ok(SessionState::Completed),
            "Error" => Ok(SessionState::Error),
            _ => Err(anyhow!("Invalid session state: {}", s)),
        }
    }
}

pub struct Orchestrator {
    config: OrchestratorConfig,
    cache: Arc<RwLock<HashMap<String, Session>>>,
    db: Option<Connection>,
}

impl Orchestrator {
    pub fn new(config: OrchestratorConfig) -> Self {
        Self {
            config,
            cache: Arc::new(RwLock::new(HashMap::new())),
            db: None,
        }
    }

    pub fn with_connection(config: OrchestratorConfig, conn: Connection) -> Result<Self> {
        let mut orch = Self::new(config);
        orch.db = Some(conn);
        orch.initialize_database()?;
        Ok(orch)
    }

    pub fn persist_to_cache(&self, session: &Session) -> Result<()> {
        let mut cache = self.cache.write()
            .map_err(|e| anyhow!("Cache lock poisoned: {}", e))?;
        cache.insert(session.id.clone(), session.clone());
        Ok(())
    }

    pub fn get_from_cache(&self, session_id: &str) -> Result<Option<Session>> {
        let cache = self.cache.read()
            .map_err(|e| anyhow!("Cache lock poisoned: {}", e))?;
        Ok(cache.get(session_id).cloned())
    }

    pub fn persist_to_database(&self, session: &Session) -> Result<()> {
        let db = self.db.as_ref()
            .context("No database connection configured")?;

        db.execute(
            "INSERT OR REPLACE INTO sessions (id, created_at, state, workspace_path) VALUES (?1, ?2, ?3, ?4)",
            params![
                &session.id,
                session.created_at as i64,
                session.state.to_string(),
                session.workspace_path.to_string_lossy().as_ref(),
            ],
        )
        .context("Failed to persist session to database")?;

        Ok(())
    }

    pub fn get_from_database(&self, session_id: &str) -> Result<Option<Session>> {
        let db = self.db.as_ref()
            .context("No database connection configured")?;

        let mut stmt = db.prepare_cached(
            "SELECT id, created_at, state, workspace_path FROM sessions WHERE id = ?1"
        )?;

        let result = stmt.query_row(params![session_id], |row| {
            let state_str: String = row.get(2)?;
            let state = SessionState::from_string(&state_str)
                .map_err(|e| rusqlite::Error::FromSqlConversionFailure(
                    2, rusqlite::types::Type::Text, Box::new(e)
                ))?;

            Ok(Session {
                id: row.get(0)?,
                created_at: row.get::<_, i64>(1)? as u64,
                state,
                workspace_path: PathBuf::from(row.get::<_, String>(3)?),
            })
        });

        match result {
            Ok(session) => Ok(Some(session)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e.into()),
        }
    }

    fn initialize_database(&self) -> Result<()> {
        let db = self.db.as_ref()
            .context("No database connection configured")?;

        db.execute_batch(
            "CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at INTEGER NOT NULL,
                state TEXT NOT NULL,
                workspace_path TEXT NOT NULL,
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
            CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(state);"
        )
        .context("Failed to initialize database schema")?;

        Ok(())
    }
}
```

**Refactorings**:
- Thread-safe cache using `Arc<RwLock<HashMap>>`
- Extracted `SessionState::to_string()` and `from_string()` for serialization
- Added `Serialize`/`Deserialize` derives for future JSON serialization
- Improved error messages with `.context()`
- Added database indexes for query performance
- Added `updated_at` timestamp for tracking changes
- Used `prepare_cached()` for statement reuse

**Verify**: `cargo test --lib orchestrator::tests` (all tests pass)

### Success Criteria

**Automated:**
- [ ] Tests fail for right reason (Red): `cargo test --lib orchestrator::tests::test_persist_session -- --nocapture`
- [ ] Tests pass (Green): `cargo test --lib orchestrator::tests::test_persist_session`
- [ ] All tests pass after refactor: `cargo test --lib orchestrator::tests`
- [ ] Concurrent access test: Multi-threaded cache read/write test passes
- [ ] Database schema created correctly: Inspect with SQLite viewer

**Manual:**
- [ ] Sessions persist across orchestrator instances (database test)
- [ ] Cache provides fast retrieval (no database hit)
- [ ] Database provides durable storage (survives process restart)
- [ ] No race conditions with concurrent access

---

## Behavior 3: Context Building

### Test Specification

**Given**: Workspace with files, thoughts, git repo, and project metadata
**When**: Building context for a session
**Then**:
- Context contains workspace file tree
- Context includes filtered thought documents
- Context includes git branch and status
- Context includes project metadata (name, type)
- Context size within limits (configurable max size)

**Edge Cases**:
- Empty workspace → Minimal context
- No git repository → Git context empty/null
- No thoughts directory → Thoughts context empty
- Very large workspace → Context truncated with warning
- Binary files → Excluded from context

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use std::fs;

    #[test]
    fn test_build_context_file_tree() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        // Create test files
        fs::write(workspace.join("file1.txt"), "content1").unwrap();
        fs::create_dir(workspace.join("subdir")).unwrap();
        fs::write(workspace.join("subdir/file2.txt"), "content2").unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
        };
        let orchestrator = Orchestrator::new(config);

        let context = orchestrator.build_context().unwrap();

        assert!(context.file_tree.contains("file1.txt"));
        assert!(context.file_tree.contains("subdir/file2.txt"));
        assert_eq!(context.workspace_path, workspace);
    }

    #[test]
    fn test_build_context_with_git() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        // Initialize git repo
        std::process::Command::new("git")
            .args(&["init"])
            .current_dir(workspace)
            .output()
            .unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
        };
        let orchestrator = Orchestrator::new(config);

        let context = orchestrator.build_context().unwrap();

        assert!(context.git_info.is_some());
        let git_info = context.git_info.unwrap();
        assert_eq!(git_info.branch, "main"); // or "master"
    }

    #[test]
    fn test_build_context_no_git() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
        };
        let orchestrator = Orchestrator::new(config);

        let context = orchestrator.build_context().unwrap();

        assert!(context.git_info.is_none());
    }

    #[test]
    fn test_build_context_size_limit() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        // Create large file
        let large_content = "x".repeat(10_000_000); // 10MB
        fs::write(workspace.join("large.txt"), large_content).unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
        };
        let orchestrator = Orchestrator::new(config);

        let context = orchestrator.build_context().unwrap();

        // Context should be truncated
        assert!(context.size_bytes < 10_000_000);
        assert!(context.truncated);
    }
}
```

**Expected Failure**: Compilation errors (missing types) and test failures.

#### 🟢 Green: Minimal Implementation

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::fs;
use walkdir::WalkDir;

#[derive(Debug, Clone)]
pub struct Context {
    pub workspace_path: PathBuf,
    pub file_tree: Vec<String>,
    pub git_info: Option<GitInfo>,
    pub thoughts: Vec<String>,
    pub project_metadata: Option<ProjectMetadata>,
    pub size_bytes: usize,
    pub truncated: bool,
}

#[derive(Debug, Clone)]
pub struct GitInfo {
    pub branch: String,
    pub status: String,
}

#[derive(Debug, Clone)]
pub struct ProjectMetadata {
    pub name: String,
    pub project_type: String,
}

impl Orchestrator {
    pub fn build_context(&self) -> Result<Context> {
        let file_tree = self.build_file_tree()?;
        let git_info = self.get_git_info().ok();

        let size_bytes = file_tree.iter().map(|s| s.len()).sum();
        let max_size = 5_000_000; // 5MB limit
        let truncated = size_bytes > max_size;

        Ok(Context {
            workspace_path: self.config.workspace_path.clone(),
            file_tree,
            git_info,
            thoughts: vec![],
            project_metadata: None,
            size_bytes,
            truncated,
        })
    }

    fn build_file_tree(&self) -> Result<Vec<String>> {
        let mut files = Vec::new();

        for entry in WalkDir::new(&self.config.workspace_path)
            .follow_links(false)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            if entry.file_type().is_file() {
                if let Ok(rel_path) = entry.path().strip_prefix(&self.config.workspace_path) {
                    files.push(rel_path.to_string_lossy().to_string());
                }
            }
        }

        Ok(files)
    }

    fn get_git_info(&self) -> Result<GitInfo> {
        let output = std::process::Command::new("git")
            .args(&["branch", "--show-current"])
            .current_dir(&self.config.workspace_path)
            .output()
            .context("Failed to execute git command")?;

        if !output.status.success() {
            anyhow::bail!("Not a git repository");
        }

        let branch = String::from_utf8_lossy(&output.stdout)
            .trim()
            .to_string();

        Ok(GitInfo {
            branch,
            status: String::new(),
        })
    }
}
```

**Run Tests**: `cargo test --lib orchestrator::tests::test_build_context`

#### 🔵 Refactor: Improve Code

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::fs;
use walkdir::WalkDir;
use git2::Repository;

const DEFAULT_MAX_CONTEXT_SIZE: usize = 5_000_000; // 5MB

#[derive(Debug, Clone)]
pub struct Context {
    pub workspace_path: PathBuf,
    pub file_tree: Vec<String>,
    pub git_info: Option<GitInfo>,
    pub thoughts: Vec<String>,
    pub project_metadata: Option<ProjectMetadata>,
    pub size_bytes: usize,
    pub truncated: bool,
}

#[derive(Debug, Clone)]
pub struct GitInfo {
    pub branch: String,
    pub status: String,
    pub has_changes: bool,
}

#[derive(Debug, Clone)]
pub struct ProjectMetadata {
    pub name: String,
    pub project_type: String,
}

pub struct OrchestratorConfig {
    pub workspace_path: PathBuf,
    pub max_context_size: usize,
}

impl Default for OrchestratorConfig {
    fn default() -> Self {
        Self {
            workspace_path: PathBuf::new(),
            max_context_size: DEFAULT_MAX_CONTEXT_SIZE,
        }
    }
}

impl Orchestrator {
    pub fn build_context(&self) -> Result<Context> {
        let file_tree = self.build_file_tree()?;
        let git_info = self.get_git_info();
        let thoughts = self.get_thoughts();
        let project_metadata = self.get_project_metadata();

        let size_bytes = self.calculate_context_size(&file_tree, &thoughts);
        let truncated = size_bytes > self.config.max_context_size;

        Ok(Context {
            workspace_path: self.config.workspace_path.clone(),
            file_tree,
            git_info,
            thoughts,
            project_metadata,
            size_bytes,
            truncated,
        })
    }

    fn build_file_tree(&self) -> Result<Vec<String>> {
        let mut files = Vec::new();
        let ignored_dirs = [".git", "node_modules", "target", ".beads"];

        for entry in WalkDir::new(&self.config.workspace_path)
            .follow_links(false)
            .into_iter()
            .filter_entry(|e| {
                // Skip ignored directories
                !ignored_dirs.iter().any(|dir| e.file_name() == *dir)
            })
            .filter_map(|e| e.ok())
        {
            if entry.file_type().is_file() {
                // Skip binary files
                if self.is_binary_file(entry.path())? {
                    continue;
                }

                if let Ok(rel_path) = entry.path().strip_prefix(&self.config.workspace_path) {
                    files.push(rel_path.to_string_lossy().to_string());
                }
            }
        }

        files.sort();
        Ok(files)
    }

    fn get_git_info(&self) -> Option<GitInfo> {
        let repo = Repository::open(&self.config.workspace_path).ok()?;

        let head = repo.head().ok()?;
        let branch = head.shorthand()?.to_string();

        let statuses = repo.statuses(None).ok()?;
        let has_changes = !statuses.is_empty();

        let status = if has_changes {
            format!("{} files changed", statuses.len())
        } else {
            "Clean working tree".to_string()
        };

        Some(GitInfo {
            branch,
            status,
            has_changes,
        })
    }

    fn get_thoughts(&self) -> Vec<String> {
        // Placeholder - will be implemented in Behavior 5
        Vec::new()
    }

    fn get_project_metadata(&self) -> Option<ProjectMetadata> {
        // Placeholder - will be implemented in Behavior 7
        None
    }

    fn is_binary_file(&self, path: &Path) -> Result<bool> {
        let mut file = fs::File::open(path)?;
        let mut buffer = [0u8; 512];
        let n = file.read(&mut buffer)?;

        // Check for null bytes (common in binary files)
        Ok(buffer[..n].contains(&0))
    }

    fn calculate_context_size(&self, file_tree: &[String], thoughts: &[String]) -> usize {
        file_tree.iter().map(|s| s.len()).sum::<usize>()
            + thoughts.iter().map(|s| s.len()).sum::<usize>()
    }
}
```

**Refactorings**:
- Switched from CLI `git` to `git2` library for better performance and error handling
- Added `max_context_size` to config with default constant
- Extracted `is_binary_file()` to exclude binary files
- Extracted `calculate_context_size()` for clarity
- Added ignored directories (`.git`, `node_modules`, `target`, `.beads`)
- Sorted file tree for deterministic output
- Added `has_changes` to `GitInfo` for richer git context
- Improved error handling with `Option` for git operations (graceful degradation)

**Verify**: `cargo test --lib orchestrator::tests` (all tests pass)

### Success Criteria

**Automated:**
- [ ] Tests fail for right reason (Red): `cargo test --lib orchestrator::tests::test_build_context -- --nocapture`
- [ ] Tests pass (Green): `cargo test --lib orchestrator::tests::test_build_context`
- [ ] All tests pass after refactor: `cargo test --lib orchestrator::tests`
- [ ] File tree excludes binary files: Test with mixed text/binary workspace
- [ ] Git info accurate: Test with various git states (clean, dirty, detached HEAD)

**Manual:**
- [ ] Context builds quickly for large workspaces (< 1s for 10k files)
- [ ] Binary files excluded (check with images, executables)
- [ ] Git info accurate (branch name, status)
- [ ] Context size reasonable (not bloated with unnecessary data)

---

## Behavior 4: Active File Tracking

### Test Specification

**Given**: List of active file paths in workspace
**When**: Tracking active files
**Then**:
- File contents read and included in context
- File metadata included (path, size, modified time)
- Content truncated if exceeds size limit
- Non-existent files skipped with warning
- Binary files excluded

**Edge Cases**:
- Empty file list → Empty active files context
- File doesn't exist → Skipped, logged
- File too large → Content truncated, marked as truncated
- File is binary → Excluded
- Concurrent file modifications → Latest content read

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use std::fs;

    #[test]
    fn test_track_active_files() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        fs::write(workspace.join("file1.txt"), "content of file1").unwrap();
        fs::write(workspace.join("file2.txt"), "content of file2").unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let active_files = vec!["file1.txt".to_string(), "file2.txt".to_string()];
        let tracked = orchestrator.track_active_files(&active_files).unwrap();

        assert_eq!(tracked.len(), 2);
        assert_eq!(tracked[0].path, "file1.txt");
        assert_eq!(tracked[0].content, "content of file1");
        assert_eq!(tracked[1].path, "file2.txt");
        assert_eq!(tracked[1].content, "content of file2");
    }

    #[test]
    fn test_track_active_files_nonexistent() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        fs::write(workspace.join("exists.txt"), "content").unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let active_files = vec!["exists.txt".to_string(), "missing.txt".to_string()];
        let tracked = orchestrator.track_active_files(&active_files).unwrap();

        // Only existing file should be tracked
        assert_eq!(tracked.len(), 1);
        assert_eq!(tracked[0].path, "exists.txt");
    }

    #[test]
    fn test_track_active_files_size_limit() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        let large_content = "x".repeat(2_000_000); // 2MB
        fs::write(workspace.join("large.txt"), &large_content).unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            max_file_size: 1_000_000, // 1MB limit
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let active_files = vec!["large.txt".to_string()];
        let tracked = orchestrator.track_active_files(&active_files).unwrap();

        assert_eq!(tracked.len(), 1);
        assert!(tracked[0].truncated);
        assert!(tracked[0].content.len() <= 1_000_000);
    }

    #[test]
    fn test_track_active_files_binary() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        // Create binary file
        fs::write(workspace.join("binary.bin"), &[0u8, 1u8, 255u8, 0u8]).unwrap();
        fs::write(workspace.join("text.txt"), "text content").unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let active_files = vec!["binary.bin".to_string(), "text.txt".to_string()];
        let tracked = orchestrator.track_active_files(&active_files).unwrap();

        // Binary file should be excluded
        assert_eq!(tracked.len(), 1);
        assert_eq!(tracked[0].path, "text.txt");
    }
}
```

**Expected Failure**: Compilation errors (missing types) and test failures.

#### 🟢 Green: Minimal Implementation

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::fs;
use std::io::Read;

#[derive(Debug, Clone)]
pub struct ActiveFile {
    pub path: String,
    pub content: String,
    pub size_bytes: usize,
    pub truncated: bool,
}

pub struct OrchestratorConfig {
    pub workspace_path: PathBuf,
    pub max_context_size: usize,
    pub max_file_size: usize,
}

impl Default for OrchestratorConfig {
    fn default() -> Self {
        Self {
            workspace_path: PathBuf::new(),
            max_context_size: DEFAULT_MAX_CONTEXT_SIZE,
            max_file_size: 1_000_000, // 1MB default
        }
    }
}

impl Orchestrator {
    pub fn track_active_files(&self, file_paths: &[String]) -> Result<Vec<ActiveFile>> {
        let mut tracked_files = Vec::new();

        for file_path in file_paths {
            let full_path = self.config.workspace_path.join(file_path);

            // Skip if file doesn't exist
            if !full_path.exists() {
                eprintln!("Warning: Active file not found: {}", file_path);
                continue;
            }

            // Skip binary files
            if self.is_binary_file(&full_path)? {
                eprintln!("Warning: Skipping binary file: {}", file_path);
                continue;
            }

            // Read file content
            let mut file = fs::File::open(&full_path)?;
            let metadata = file.metadata()?;
            let size = metadata.len() as usize;

            let mut content = String::new();
            let truncated = if size > self.config.max_file_size {
                // Read only up to max_file_size
                let mut limited_reader = file.take(self.config.max_file_size as u64);
                limited_reader.read_to_string(&mut content)?;
                true
            } else {
                file.read_to_string(&mut content)?;
                false
            };

            tracked_files.push(ActiveFile {
                path: file_path.clone(),
                content,
                size_bytes: size,
                truncated,
            });
        }

        Ok(tracked_files)
    }
}
```

**Run Tests**: `cargo test --lib orchestrator::tests::test_track_active_files`

#### 🔵 Refactor: Improve Code

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::fs;
use std::io::{Read, BufReader};
use std::time::SystemTime;

const DEFAULT_MAX_FILE_SIZE: usize = 1_000_000; // 1MB

#[derive(Debug, Clone)]
pub struct ActiveFile {
    pub path: String,
    pub content: String,
    pub size_bytes: usize,
    pub modified_at: Option<u64>,
    pub truncated: bool,
}

pub struct OrchestratorConfig {
    pub workspace_path: PathBuf,
    pub max_context_size: usize,
    pub max_file_size: usize,
}

impl Default for OrchestratorConfig {
    fn default() -> Self {
        Self {
            workspace_path: PathBuf::new(),
            max_context_size: DEFAULT_MAX_CONTEXT_SIZE,
            max_file_size: DEFAULT_MAX_FILE_SIZE,
        }
    }
}

impl Orchestrator {
    pub fn track_active_files(&self, file_paths: &[String]) -> Result<Vec<ActiveFile>> {
        file_paths
            .iter()
            .filter_map(|path| self.track_single_file(path).ok())
            .collect::<Vec<_>>()
            .pipe(Ok)
    }

    fn track_single_file(&self, file_path: &str) -> Result<ActiveFile> {
        let full_path = self.config.workspace_path.join(file_path);

        // Check existence
        if !full_path.exists() {
            anyhow::bail!("File not found: {}", file_path);
        }

        // Skip binary files
        if self.is_binary_file(&full_path)? {
            anyhow::bail!("Binary file skipped: {}", file_path);
        }

        // Get metadata
        let metadata = fs::metadata(&full_path)
            .context(format!("Failed to read metadata for {}", file_path))?;

        let size = metadata.len() as usize;
        let modified_at = metadata.modified()
            .ok()
            .and_then(|time| time.duration_since(SystemTime::UNIX_EPOCH).ok())
            .map(|duration| duration.as_secs());

        // Read content
        let file = fs::File::open(&full_path)
            .context(format!("Failed to open file {}", file_path))?;

        let (content, truncated) = self.read_file_content(file, size)?;

        Ok(ActiveFile {
            path: file_path.to_string(),
            content,
            size_bytes: size,
            modified_at,
            truncated,
        })
    }

    fn read_file_content(&self, file: fs::File, size: usize) -> Result<(String, bool)> {
        let mut reader = BufReader::new(file);
        let mut content = String::new();

        let truncated = if size > self.config.max_file_size {
            let mut limited_reader = reader.take(self.config.max_file_size as u64);
            limited_reader.read_to_string(&mut content)
                .context("Failed to read file content")?;
            true
        } else {
            reader.read_to_string(&mut content)
                .context("Failed to read file content")?;
            false
        };

        Ok((content, truncated))
    }
}

// Extension trait for pipe operator (functional style)
trait Pipe: Sized {
    fn pipe<F, R>(self, f: F) -> R
    where
        F: FnOnce(Self) -> R,
    {
        f(self)
    }
}

impl<T> Pipe for T {}
```

**Refactorings**:
- Extracted `track_single_file()` for single file tracking logic
- Extracted `read_file_content()` for content reading with truncation
- Used `filter_map()` for cleaner error handling (skip failed files)
- Added `modified_at` timestamp to `ActiveFile` for staleness detection
- Used `BufReader` for more efficient reading
- Added `Pipe` trait for functional-style composition
- Improved error messages with file-specific context
- Gracefully handle file errors (skip and continue) instead of failing entire operation

**Verify**: `cargo test --lib orchestrator::tests` (all tests pass)

### Success Criteria

**Automated:**
- [ ] Tests fail for right reason (Red): `cargo test --lib orchestrator::tests::test_track_active_files -- --nocapture`
- [ ] Tests pass (Green): `cargo test --lib orchestrator::tests::test_track_active_files`
- [ ] All tests pass after refactor: `cargo test --lib orchestrator::tests`
- [ ] Binary files excluded: Test with mixed text/binary files
- [ ] Large files truncated: Test with files exceeding max_file_size

**Manual:**
- [ ] Active files tracked accurately
- [ ] File contents included in context
- [ ] Binary files excluded (images, executables)
- [ ] Large files truncated with warning
- [ ] Nonexistent files skipped gracefully

---

## Behavior 5: Thought Retrieval

### Test Specification

**Given**: Thoughts directory with categorized documents
**When**: Retrieving thoughts
**Then**:
- Documents found in `thoughts/` directory
- Documents categorized (searchable, user-specific, etc.)
- Documents filtered by relevance (configurable)
- Document metadata included (path, category, size)
- Documents sorted by relevance/recency

**Edge Cases**:
- No thoughts directory → Empty list
- Empty thoughts directory → Empty list
- Invalid markdown files → Skipped with warning
- Very large thought files → Truncated
- Nested subdirectories → All found and categorized

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use std::fs;

    #[test]
    fn test_retrieve_thoughts_searchable() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        // Create thoughts directory structure
        let thoughts_dir = workspace.join("thoughts");
        fs::create_dir_all(thoughts_dir.join("searchable/research")).unwrap();
        fs::write(
            thoughts_dir.join("searchable/research/doc1.md"),
            "# Research Document 1\nContent here",
        ).unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let thoughts = orchestrator.retrieve_thoughts().unwrap();

        assert_eq!(thoughts.len(), 1);
        assert_eq!(thoughts[0].path, "thoughts/searchable/research/doc1.md");
        assert_eq!(thoughts[0].category, ThoughtCategory::Searchable);
        assert!(thoughts[0].content.contains("Research Document 1"));
    }

    #[test]
    fn test_retrieve_thoughts_user_specific() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        // Create user-specific thoughts
        let thoughts_dir = workspace.join("thoughts");
        fs::create_dir_all(thoughts_dir.join("user123")).unwrap();
        fs::write(
            thoughts_dir.join("user123/note.md"),
            "# User Note\nUser-specific content",
        ).unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let thoughts = orchestrator.retrieve_thoughts().unwrap();

        assert_eq!(thoughts.len(), 1);
        assert_eq!(thoughts[0].category, ThoughtCategory::UserSpecific);
    }

    #[test]
    fn test_retrieve_thoughts_no_directory() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let thoughts = orchestrator.retrieve_thoughts().unwrap();

        assert_eq!(thoughts.len(), 0);
    }

    #[test]
    fn test_retrieve_thoughts_filtering() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        let thoughts_dir = workspace.join("thoughts");
        fs::create_dir_all(thoughts_dir.join("searchable/research")).unwrap();
        fs::create_dir_all(thoughts_dir.join("searchable/plans")).unwrap();
        fs::write(thoughts_dir.join("searchable/research/doc1.md"), "content1").unwrap();
        fs::write(thoughts_dir.join("searchable/plans/doc2.md"), "content2").unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let filter = ThoughtFilter {
            categories: vec![ThoughtCategory::Searchable],
            subcategories: Some(vec!["research".to_string()]),
        };

        let thoughts = orchestrator.retrieve_thoughts_filtered(&filter).unwrap();

        assert_eq!(thoughts.len(), 1);
        assert!(thoughts[0].path.contains("research"));
    }
}
```

**Expected Failure**: Compilation errors (missing types) and test failures.

#### 🟢 Green: Minimal Implementation

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::fs;
use walkdir::WalkDir;

#[derive(Debug, Clone, PartialEq)]
pub enum ThoughtCategory {
    Searchable,
    UserSpecific,
    Other,
}

#[derive(Debug, Clone)]
pub struct Thought {
    pub path: String,
    pub category: ThoughtCategory,
    pub content: String,
    pub size_bytes: usize,
}

#[derive(Debug, Clone)]
pub struct ThoughtFilter {
    pub categories: Vec<ThoughtCategory>,
    pub subcategories: Option<Vec<String>>,
}

impl Orchestrator {
    pub fn retrieve_thoughts(&self) -> Result<Vec<Thought>> {
        let thoughts_dir = self.config.workspace_path.join("thoughts");

        if !thoughts_dir.exists() {
            return Ok(Vec::new());
        }

        let mut thoughts = Vec::new();

        for entry in WalkDir::new(&thoughts_dir)
            .follow_links(false)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            if entry.file_type().is_file() && entry.path().extension() == Some("md".as_ref()) {
                let rel_path = entry.path()
                    .strip_prefix(&self.config.workspace_path)
                    .unwrap()
                    .to_string_lossy()
                    .to_string();

                let category = self.categorize_thought(&rel_path);
                let content = fs::read_to_string(entry.path())?;
                let size = content.len();

                thoughts.push(Thought {
                    path: rel_path,
                    category,
                    content,
                    size_bytes: size,
                });
            }
        }

        Ok(thoughts)
    }

    pub fn retrieve_thoughts_filtered(&self, filter: &ThoughtFilter) -> Result<Vec<Thought>> {
        let all_thoughts = self.retrieve_thoughts()?;

        let filtered = all_thoughts
            .into_iter()
            .filter(|thought| {
                // Filter by category
                if !filter.categories.contains(&thought.category) {
                    return false;
                }

                // Filter by subcategory
                if let Some(ref subcats) = filter.subcategories {
                    return subcats.iter().any(|subcat| thought.path.contains(subcat));
                }

                true
            })
            .collect();

        Ok(filtered)
    }

    fn categorize_thought(&self, path: &str) -> ThoughtCategory {
        if path.contains("thoughts/searchable") {
            ThoughtCategory::Searchable
        } else if path.contains("thoughts/") && !path.contains("thoughts/searchable") {
            // User-specific paths are like "thoughts/user123/"
            ThoughtCategory::UserSpecific
        } else {
            ThoughtCategory::Other
        }
    }
}
```

**Run Tests**: `cargo test --lib orchestrator::tests::test_retrieve_thoughts`

#### 🔵 Refactor: Improve Code

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::fs;
use std::time::SystemTime;
use walkdir::WalkDir;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum ThoughtCategory {
    Searchable,
    UserSpecific,
    Archived,
    Other,
}

#[derive(Debug, Clone)]
pub struct Thought {
    pub path: String,
    pub category: ThoughtCategory,
    pub subcategory: Option<String>,
    pub content: String,
    pub size_bytes: usize,
    pub modified_at: Option<u64>,
}

#[derive(Debug, Clone, Default)]
pub struct ThoughtFilter {
    pub categories: Vec<ThoughtCategory>,
    pub subcategories: Option<Vec<String>>,
    pub max_size: Option<usize>,
    pub limit: Option<usize>,
}

impl Orchestrator {
    pub fn retrieve_thoughts(&self) -> Result<Vec<Thought>> {
        self.retrieve_thoughts_filtered(&ThoughtFilter::default())
    }

    pub fn retrieve_thoughts_filtered(&self, filter: &ThoughtFilter) -> Result<Vec<Thought>> {
        let thoughts_dir = self.config.workspace_path.join("thoughts");

        if !thoughts_dir.exists() {
            return Ok(Vec::new());
        }

        let mut thoughts: Vec<Thought> = WalkDir::new(&thoughts_dir)
            .follow_links(false)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|entry| {
                entry.file_type().is_file()
                    && entry.path().extension().map_or(false, |ext| ext == "md")
            })
            .filter_map(|entry| self.parse_thought_file(&entry).ok())
            .filter(|thought| self.matches_filter(thought, filter))
            .collect();

        // Sort by modified time (most recent first)
        thoughts.sort_by(|a, b| {
            b.modified_at
                .unwrap_or(0)
                .cmp(&a.modified_at.unwrap_or(0))
        });

        // Apply limit if specified
        if let Some(limit) = filter.limit {
            thoughts.truncate(limit);
        }

        Ok(thoughts)
    }

    fn parse_thought_file(&self, entry: &walkdir::DirEntry) -> Result<Thought> {
        let path = entry.path();
        let rel_path = path
            .strip_prefix(&self.config.workspace_path)
            .context("Failed to strip workspace prefix")?
            .to_string_lossy()
            .to_string();

        let metadata = fs::metadata(path)?;
        let modified_at = metadata.modified()
            .ok()
            .and_then(|time| time.duration_since(SystemTime::UNIX_EPOCH).ok())
            .map(|duration| duration.as_secs());

        let content = fs::read_to_string(path)
            .context(format!("Failed to read thought file: {}", rel_path))?;

        let size = content.len();

        let (category, subcategory) = self.categorize_thought_detailed(&rel_path);

        Ok(Thought {
            path: rel_path,
            category,
            subcategory,
            content,
            size_bytes: size,
            modified_at,
        })
    }

    fn categorize_thought_detailed(&self, path: &str) -> (ThoughtCategory, Option<String>) {
        let parts: Vec<&str> = path.split('/').collect();

        if parts.len() < 3 {
            return (ThoughtCategory::Other, None);
        }

        // paths like: "thoughts/searchable/research/doc.md"
        match parts[1] {
            "searchable" => {
                let subcategory = parts.get(2).map(|s| s.to_string());
                (ThoughtCategory::Searchable, subcategory)
            }
            "archived" => (ThoughtCategory::Archived, None),
            _ => {
                // User-specific: "thoughts/username/..."
                (ThoughtCategory::UserSpecific, None)
            }
        }
    }

    fn matches_filter(&self, thought: &Thought, filter: &ThoughtFilter) -> bool {
        // If no categories specified, match all
        if !filter.categories.is_empty() && !filter.categories.contains(&thought.category) {
            return false;
        }

        // Filter by subcategory
        if let Some(ref subcats) = filter.subcategories {
            if let Some(ref thought_subcat) = thought.subcategory {
                if !subcats.contains(thought_subcat) {
                    return false;
                }
            } else {
                return false; // Thought has no subcategory but filter requires one
            }
        }

        // Filter by size
        if let Some(max_size) = filter.max_size {
            if thought.size_bytes > max_size {
                return false;
            }
        }

        true
    }
}

impl Default for ThoughtFilter {
    fn default() -> Self {
        Self {
            categories: vec![
                ThoughtCategory::Searchable,
                ThoughtCategory::UserSpecific,
            ],
            subcategories: None,
            max_size: None,
            limit: None,
        }
    }
}
```

**Refactorings**:
- Extracted `parse_thought_file()` for cleaner file parsing
- Extracted `categorize_thought_detailed()` to return both category and subcategory
- Extracted `matches_filter()` for cleaner filtering logic
- Added `subcategory` field to `Thought` for richer categorization
- Added `modified_at` to `Thought` for sorting by recency
- Added `max_size` and `limit` to `ThoughtFilter` for more control
- Used iterator chains for cleaner collection building
- Sort thoughts by modified time (most recent first)
- Added `Archived` category for archived thoughts
- Made `retrieve_thoughts()` delegate to `retrieve_thoughts_filtered()` with default filter

**Verify**: `cargo test --lib orchestrator::tests` (all tests pass)

### Success Criteria

**Automated:**
- [ ] Tests fail for right reason (Red): `cargo test --lib orchestrator::tests::test_retrieve_thoughts -- --nocapture`
- [ ] Tests pass (Green): `cargo test --lib orchestrator::tests::test_retrieve_thoughts`
- [ ] All tests pass after refactor: `cargo test --lib orchestrator::tests`
- [ ] Filtering works: Test various filter combinations
- [ ] Sorting works: Test thoughts returned in correct order (most recent first)

**Manual:**
- [ ] All markdown files in thoughts/ found
- [ ] Categorization accurate (searchable, user-specific, archived)
- [ ] Filtering works as expected
- [ ] Sorting by recency accurate
- [ ] No thoughts directory handled gracefully

---

## Behavior 6: Git Information

### Test Specification

**Given**: Git repository in workspace
**When**: Requesting git information
**Then**:
- Current branch name provided
- Working tree status provided (clean/dirty)
- Recent commits listed
- Staged/unstaged changes summarized
- Remote tracking info included

**Edge Cases**:
- Not a git repository → None returned (no error)
- Detached HEAD → Branch shows commit SHA
- No commits yet → Empty commit list
- No remote configured → Remote info None
- Submodules → Main repo info only

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use std::process::Command;

    fn init_git_repo(path: &Path) {
        Command::new("git").args(&["init"]).current_dir(path).output().unwrap();
        Command::new("git").args(&["config", "user.name", "Test"]).current_dir(path).output().unwrap();
        Command::new("git").args(&["config", "user.email", "test@test.com"]).current_dir(path).output().unwrap();
    }

    #[test]
    fn test_get_git_info_branch() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();
        init_git_repo(workspace);

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let git_info = orchestrator.get_detailed_git_info().unwrap().unwrap();

        assert!(!git_info.branch.is_empty());
        assert!(git_info.branch == "main" || git_info.branch == "master");
    }

    #[test]
    fn test_get_git_info_status() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();
        init_git_repo(workspace);

        // Create and commit a file
        fs::write(workspace.join("file.txt"), "content").unwrap();
        Command::new("git").args(&["add", "."]).current_dir(workspace).output().unwrap();
        Command::new("git").args(&["commit", "-m", "Initial"]).current_dir(workspace).output().unwrap();

        // Create uncommitted change
        fs::write(workspace.join("file2.txt"), "new content").unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let git_info = orchestrator.get_detailed_git_info().unwrap().unwrap();

        assert!(git_info.has_changes);
        assert_eq!(git_info.untracked_files.len(), 1);
        assert_eq!(git_info.staged_files.len(), 0);
    }

    #[test]
    fn test_get_git_info_commits() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();
        init_git_repo(workspace);

        // Create commits
        fs::write(workspace.join("file.txt"), "content").unwrap();
        Command::new("git").args(&["add", "."]).current_dir(workspace).output().unwrap();
        Command::new("git").args(&["commit", "-m", "Commit 1"]).current_dir(workspace).output().unwrap();

        fs::write(workspace.join("file.txt"), "content2").unwrap();
        Command::new("git").args(&["add", "."]).current_dir(workspace).output().unwrap();
        Command::new("git").args(&["commit", "-m", "Commit 2"]).current_dir(workspace).output().unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let git_info = orchestrator.get_detailed_git_info().unwrap().unwrap();

        assert_eq!(git_info.recent_commits.len(), 2);
        assert_eq!(git_info.recent_commits[0].message, "Commit 2");
        assert_eq!(git_info.recent_commits[1].message, "Commit 1");
    }

    #[test]
    fn test_get_git_info_not_a_repo() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let git_info = orchestrator.get_detailed_git_info().unwrap();

        assert!(git_info.is_none());
    }
}
```

**Expected Failure**: Compilation errors (missing types) and test failures.

#### 🟢 Green: Minimal Implementation

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use git2::{Repository, StatusOptions};

#[derive(Debug, Clone)]
pub struct DetailedGitInfo {
    pub branch: String,
    pub has_changes: bool,
    pub staged_files: Vec<String>,
    pub unstaged_files: Vec<String>,
    pub untracked_files: Vec<String>,
    pub recent_commits: Vec<CommitInfo>,
}

#[derive(Debug, Clone)]
pub struct CommitInfo {
    pub sha: String,
    pub message: String,
    pub author: String,
    pub timestamp: i64,
}

impl Orchestrator {
    pub fn get_detailed_git_info(&self) -> Result<Option<DetailedGitInfo>> {
        let repo = match Repository::open(&self.config.workspace_path) {
            Ok(r) => r,
            Err(_) => return Ok(None),
        };

        let head = repo.head()?;
        let branch = head.shorthand().unwrap_or("HEAD").to_string();

        // Get status
        let mut opts = StatusOptions::new();
        opts.include_untracked(true);
        let statuses = repo.statuses(Some(&mut opts))?;

        let mut staged_files = Vec::new();
        let mut unstaged_files = Vec::new();
        let mut untracked_files = Vec::new();

        for entry in statuses.iter() {
            let path = entry.path().unwrap_or("").to_string();
            let status = entry.status();

            if status.is_index_new() || status.is_index_modified() || status.is_index_deleted() {
                staged_files.push(path.clone());
            }
            if status.is_wt_modified() || status.is_wt_deleted() {
                unstaged_files.push(path.clone());
            }
            if status.is_wt_new() {
                untracked_files.push(path);
            }
        }

        let has_changes = !staged_files.is_empty()
            || !unstaged_files.is_empty()
            || !untracked_files.is_empty();

        // Get recent commits
        let mut revwalk = repo.revwalk()?;
        revwalk.push_head()?;

        let mut recent_commits = Vec::new();
        for commit_oid in revwalk.take(10) {
            let oid = commit_oid?;
            let commit = repo.find_commit(oid)?;

            recent_commits.push(CommitInfo {
                sha: format!("{}", oid),
                message: commit.message().unwrap_or("").to_string(),
                author: commit.author().name().unwrap_or("").to_string(),
                timestamp: commit.time().seconds(),
            });
        }

        Ok(Some(DetailedGitInfo {
            branch,
            has_changes,
            staged_files,
            unstaged_files,
            untracked_files,
            recent_commits,
        }))
    }
}
```

**Run Tests**: `cargo test --lib orchestrator::tests::test_get_git_info`

#### 🔵 Refactor: Improve Code

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use git2::{Repository, StatusOptions, Status};

const DEFAULT_COMMIT_LIMIT: usize = 10;

#[derive(Debug, Clone)]
pub struct DetailedGitInfo {
    pub branch: String,
    pub has_changes: bool,
    pub staged_files: Vec<String>,
    pub unstaged_files: Vec<String>,
    pub untracked_files: Vec<String>,
    pub recent_commits: Vec<CommitInfo>,
    pub remote_tracking: Option<RemoteTracking>,
}

#[derive(Debug, Clone)]
pub struct CommitInfo {
    pub sha: String,
    pub short_sha: String,
    pub message: String,
    pub author: String,
    pub timestamp: i64,
}

#[derive(Debug, Clone)]
pub struct RemoteTracking {
    pub remote_name: String,
    pub remote_branch: String,
    pub ahead: usize,
    pub behind: usize,
}

impl Orchestrator {
    pub fn get_detailed_git_info(&self) -> Result<Option<DetailedGitInfo>> {
        self.get_git_info_with_limit(DEFAULT_COMMIT_LIMIT)
    }

    pub fn get_git_info_with_limit(&self, commit_limit: usize) -> Result<Option<DetailedGitInfo>> {
        let repo = match Repository::open(&self.config.workspace_path) {
            Ok(r) => r,
            Err(_) => return Ok(None),
        };

        let branch = self.get_current_branch(&repo)?;
        let (staged, unstaged, untracked) = self.get_working_tree_status(&repo)?;
        let has_changes = !staged.is_empty() || !unstaged.is_empty() || !untracked.is_empty();
        let recent_commits = self.get_recent_commits(&repo, commit_limit)?;
        let remote_tracking = self.get_remote_tracking(&repo);

        Ok(Some(DetailedGitInfo {
            branch,
            has_changes,
            staged_files: staged,
            unstaged_files: unstaged,
            untracked_files: untracked,
            recent_commits,
            remote_tracking,
        }))
    }

    fn get_current_branch(&self, repo: &Repository) -> Result<String> {
        let head = repo.head()
            .context("Failed to get HEAD reference")?;

        Ok(head.shorthand()
            .unwrap_or(&format!("detached@{}", head.target().unwrap_or_default()))
            .to_string())
    }

    fn get_working_tree_status(&self, repo: &Repository) -> Result<(Vec<String>, Vec<String>, Vec<String>)> {
        let mut opts = StatusOptions::new();
        opts.include_untracked(true)
            .recurse_untracked_dirs(false);

        let statuses = repo.statuses(Some(&mut opts))
            .context("Failed to get repository status")?;

        let mut staged = Vec::new();
        let mut unstaged = Vec::new();
        let mut untracked = Vec::new();

        for entry in statuses.iter() {
            let path = entry.path().unwrap_or("").to_string();
            let status = entry.status();

            if self.is_staged_change(status) {
                staged.push(path.clone());
            }
            if self.is_unstaged_change(status) {
                unstaged.push(path.clone());
            }
            if status.is_wt_new() {
                untracked.push(path);
            }
        }

        Ok((staged, unstaged, untracked))
    }

    fn is_staged_change(&self, status: Status) -> bool {
        status.is_index_new()
            || status.is_index_modified()
            || status.is_index_deleted()
            || status.is_index_renamed()
            || status.is_index_typechange()
    }

    fn is_unstaged_change(&self, status: Status) -> bool {
        status.is_wt_modified()
            || status.is_wt_deleted()
            || status.is_wt_renamed()
            || status.is_wt_typechange()
    }

    fn get_recent_commits(&self, repo: &Repository, limit: usize) -> Result<Vec<CommitInfo>> {
        let mut revwalk = repo.revwalk()
            .context("Failed to create revwalk")?;

        revwalk.push_head()
            .context("Failed to push HEAD to revwalk")?;

        let commits = revwalk
            .take(limit)
            .filter_map(|oid_result| oid_result.ok())
            .filter_map(|oid| {
                repo.find_commit(oid).ok().map(|commit| {
                    let sha = format!("{}", oid);
                    let short_sha = sha.chars().take(7).collect();

                    CommitInfo {
                        sha,
                        short_sha,
                        message: commit.message()
                            .unwrap_or("")
                            .lines()
                            .next()
                            .unwrap_or("")
                            .to_string(),
                        author: commit.author().name()
                            .unwrap_or("Unknown")
                            .to_string(),
                        timestamp: commit.time().seconds(),
                    }
                })
            })
            .collect();

        Ok(commits)
    }

    fn get_remote_tracking(&self, repo: &Repository) -> Option<RemoteTracking> {
        let head = repo.head().ok()?;
        let branch = head.shorthand()?;

        let local_branch = repo.find_branch(branch, git2::BranchType::Local).ok()?;
        let upstream = local_branch.upstream().ok()?;

        let upstream_name = upstream.name().ok()??;
        let parts: Vec<&str> = upstream_name.splitn(2, '/').collect();

        if parts.len() != 2 {
            return None;
        }

        let local_oid = head.target()?;
        let upstream_oid = upstream.get().target()?;

        let (ahead, behind) = repo.graph_ahead_behind(local_oid, upstream_oid).ok()?;

        Some(RemoteTracking {
            remote_name: parts[0].to_string(),
            remote_branch: parts[1].to_string(),
            ahead,
            behind,
        })
    }
}
```

**Refactorings**:
- Extracted `get_current_branch()` for branch name retrieval
- Extracted `get_working_tree_status()` for status checking
- Extracted `is_staged_change()` and `is_unstaged_change()` for cleaner status checks
- Extracted `get_recent_commits()` with configurable limit
- Extracted `get_remote_tracking()` for remote branch tracking info
- Added `RemoteTracking` struct with ahead/behind counts
- Added `short_sha` to `CommitInfo` for display
- Commit message trimmed to first line only
- Better error handling with `.context()`
- More complete status checking (renamed, typechange)
- Handle detached HEAD gracefully

**Verify**: `cargo test --lib orchestrator::tests` (all tests pass)

### Success Criteria

**Automated:**
- [ ] Tests fail for right reason (Red): `cargo test --lib orchestrator::tests::test_get_git_info -- --nocapture`
- [ ] Tests pass (Green): `cargo test --lib orchestrator::tests::test_get_git_info`
- [ ] All tests pass after refactor: `cargo test --lib orchestrator::tests`
- [ ] Handles detached HEAD: Test checkout of specific commit
- [ ] Handles no commits: Test freshly initialized repo

**Manual:**
- [ ] Branch name accurate
- [ ] Status reflects working tree state
- [ ] Commits listed in reverse chronological order
- [ ] Remote tracking info accurate (ahead/behind counts)
- [ ] Non-git directories handled gracefully (None returned)

---

## Behavior 7: Project Metadata

### Test Specification

**Given**: Workspace with project configuration files
**When**: Extracting project metadata
**Then**:
- Project name detected from config files
- Project type detected (Rust, Node.js, Python, etc.)
- Build system identified (Cargo, npm, pip, etc.)
- Key dependencies listed
- Project root identified

**Edge Cases**:
- Multiple project types → Primary type returned
- No config files → Minimal metadata with workspace name
- Monorepo → Root project metadata
- Invalid/malformed config → Graceful degradation

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use std::fs;

    #[test]
    fn test_extract_project_metadata_rust() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        fs::write(
            workspace.join("Cargo.toml"),
            r#"
[package]
name = "my-rust-project"
version = "0.1.0"

[dependencies]
serde = "1.0"
"#,
        ).unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let metadata = orchestrator.extract_project_metadata().unwrap().unwrap();

        assert_eq!(metadata.name, "my-rust-project");
        assert_eq!(metadata.project_type, ProjectType::Rust);
        assert_eq!(metadata.build_system, Some("Cargo".to_string()));
        assert!(metadata.dependencies.contains(&"serde".to_string()));
    }

    #[test]
    fn test_extract_project_metadata_nodejs() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        fs::write(
            workspace.join("package.json"),
            r#"{
  "name": "my-node-project",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21"
  }
}"#,
        ).unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let metadata = orchestrator.extract_project_metadata().unwrap().unwrap();

        assert_eq!(metadata.name, "my-node-project");
        assert_eq!(metadata.project_type, ProjectType::NodeJS);
        assert_eq!(metadata.build_system, Some("npm".to_string()));
        assert_eq!(metadata.dependencies.len(), 2);
    }

    #[test]
    fn test_extract_project_metadata_none() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let metadata = orchestrator.extract_project_metadata().unwrap();

        assert!(metadata.is_none());
    }

    #[test]
    fn test_extract_project_metadata_monorepo() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        // Root Cargo.toml with workspace
        fs::write(
            workspace.join("Cargo.toml"),
            r#"
[workspace]
members = ["crate1", "crate2"]
"#,
        ).unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let metadata = orchestrator.extract_project_metadata().unwrap().unwrap();

        assert_eq!(metadata.project_type, ProjectType::Rust);
        assert!(metadata.is_monorepo);
    }
}
```

**Expected Failure**: Compilation errors (missing types) and test failures.

#### 🟢 Green: Minimal Implementation

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::fs;
use toml::Value as TomlValue;
use serde_json::Value as JsonValue;

#[derive(Debug, Clone, PartialEq)]
pub enum ProjectType {
    Rust,
    NodeJS,
    Python,
    Unknown,
}

#[derive(Debug, Clone)]
pub struct ProjectMetadata {
    pub name: String,
    pub project_type: ProjectType,
    pub build_system: Option<String>,
    pub dependencies: Vec<String>,
    pub is_monorepo: bool,
}

impl Orchestrator {
    pub fn extract_project_metadata(&self) -> Result<Option<ProjectMetadata>> {
        // Try Rust project
        if let Some(metadata) = self.try_extract_rust_metadata()? {
            return Ok(Some(metadata));
        }

        // Try Node.js project
        if let Some(metadata) = self.try_extract_nodejs_metadata()? {
            return Ok(Some(metadata));
        }

        // Try Python project
        if let Some(metadata) = self.try_extract_python_metadata()? {
            return Ok(Some(metadata));
        }

        Ok(None)
    }

    fn try_extract_rust_metadata(&self) -> Result<Option<ProjectMetadata>> {
        let cargo_toml_path = self.config.workspace_path.join("Cargo.toml");

        if !cargo_toml_path.exists() {
            return Ok(None);
        }

        let content = fs::read_to_string(&cargo_toml_path)?;
        let toml: TomlValue = toml::from_str(&content)?;

        // Check if it's a workspace
        let is_monorepo = toml.get("workspace").is_some();

        let name = if is_monorepo {
            self.config.workspace_path
                .file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string()
        } else {
            toml.get("package")
                .and_then(|p| p.get("name"))
                .and_then(|n| n.as_str())
                .unwrap_or("unknown")
                .to_string()
        };

        let dependencies = toml
            .get("dependencies")
            .and_then(|d| d.as_table())
            .map(|table| table.keys().cloned().collect())
            .unwrap_or_default();

        Ok(Some(ProjectMetadata {
            name,
            project_type: ProjectType::Rust,
            build_system: Some("Cargo".to_string()),
            dependencies,
            is_monorepo,
        }))
    }

    fn try_extract_nodejs_metadata(&self) -> Result<Option<ProjectMetadata>> {
        let package_json_path = self.config.workspace_path.join("package.json");

        if !package_json_path.exists() {
            return Ok(None);
        }

        let content = fs::read_to_string(&package_json_path)?;
        let json: JsonValue = serde_json::from_str(&content)?;

        let name = json.get("name")
            .and_then(|n| n.as_str())
            .unwrap_or("unknown")
            .to_string();

        let dependencies: Vec<String> = json
            .get("dependencies")
            .and_then(|d| d.as_object())
            .map(|obj| obj.keys().cloned().collect())
            .unwrap_or_default();

        let is_monorepo = json.get("workspaces").is_some();

        Ok(Some(ProjectMetadata {
            name,
            project_type: ProjectType::NodeJS,
            build_system: Some("npm".to_string()),
            dependencies,
            is_monorepo,
        }))
    }

    fn try_extract_python_metadata(&self) -> Result<Option<ProjectMetadata>> {
        // Placeholder - not implemented yet
        Ok(None)
    }
}
```

**Run Tests**: `cargo test --lib orchestrator::tests::test_extract_project_metadata`

#### 🔵 Refactor: Improve Code

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::fs;
use toml::Value as TomlValue;
use serde_json::Value as JsonValue;

#[derive(Debug, Clone, PartialEq)]
pub enum ProjectType {
    Rust,
    NodeJS,
    Python,
    Go,
    Ruby,
    Unknown,
}

impl ProjectType {
    fn as_str(&self) -> &str {
        match self {
            ProjectType::Rust => "Rust",
            ProjectType::NodeJS => "Node.js",
            ProjectType::Python => "Python",
            ProjectType::Go => "Go",
            ProjectType::Ruby => "Ruby",
            ProjectType::Unknown => "Unknown",
        }
    }
}

#[derive(Debug, Clone)]
pub struct ProjectMetadata {
    pub name: String,
    pub project_type: ProjectType,
    pub build_system: Option<String>,
    pub dependencies: Vec<String>,
    pub is_monorepo: bool,
    pub root_path: PathBuf,
}

impl Orchestrator {
    pub fn extract_project_metadata(&self) -> Result<Option<ProjectMetadata>> {
        let extractors: Vec<fn(&Self) -> Result<Option<ProjectMetadata>>> = vec![
            Self::try_extract_rust_metadata,
            Self::try_extract_nodejs_metadata,
            Self::try_extract_python_metadata,
            Self::try_extract_go_metadata,
        ];

        for extractor in extractors {
            if let Some(metadata) = extractor(self)? {
                return Ok(Some(metadata));
            }
        }

        Ok(None)
    }

    fn try_extract_rust_metadata(&self) -> Result<Option<ProjectMetadata>> {
        let cargo_toml_path = self.config.workspace_path.join("Cargo.toml");

        if !cargo_toml_path.exists() {
            return Ok(None);
        }

        let content = fs::read_to_string(&cargo_toml_path)
            .context("Failed to read Cargo.toml")?;

        let toml: TomlValue = toml::from_str(&content)
            .context("Failed to parse Cargo.toml")?;

        let is_monorepo = toml.get("workspace").is_some();

        let name = if is_monorepo {
            self.workspace_name()
        } else {
            self.extract_toml_string(&toml, &["package", "name"])
                .unwrap_or_else(|| "unknown".to_string())
        };

        let dependencies = self.extract_toml_dependencies(&toml);

        Ok(Some(ProjectMetadata {
            name,
            project_type: ProjectType::Rust,
            build_system: Some("Cargo".to_string()),
            dependencies,
            is_monorepo,
            root_path: self.config.workspace_path.clone(),
        }))
    }

    fn try_extract_nodejs_metadata(&self) -> Result<Option<ProjectMetadata>> {
        let package_json_path = self.config.workspace_path.join("package.json");

        if !package_json_path.exists() {
            return Ok(None);
        }

        let content = fs::read_to_string(&package_json_path)
            .context("Failed to read package.json")?;

        let json: JsonValue = serde_json::from_str(&content)
            .context("Failed to parse package.json")?;

        let name = json.get("name")
            .and_then(|n| n.as_str())
            .unwrap_or_else(|| &self.workspace_name())
            .to_string();

        let dependencies = self.extract_json_dependencies(&json);

        let is_monorepo = json.get("workspaces").is_some();

        Ok(Some(ProjectMetadata {
            name,
            project_type: ProjectType::NodeJS,
            build_system: Some("npm".to_string()),
            dependencies,
            is_monorepo,
            root_path: self.config.workspace_path.clone(),
        }))
    }

    fn try_extract_python_metadata(&self) -> Result<Option<ProjectMetadata>> {
        let pyproject_toml_path = self.config.workspace_path.join("pyproject.toml");
        let requirements_txt_path = self.config.workspace_path.join("requirements.txt");

        if pyproject_toml_path.exists() {
            let content = fs::read_to_string(&pyproject_toml_path)?;
            let toml: TomlValue = toml::from_str(&content)?;

            let name = self.extract_toml_string(&toml, &["project", "name"])
                .or_else(|| self.extract_toml_string(&toml, &["tool", "poetry", "name"]))
                .unwrap_or_else(|| self.workspace_name());

            let dependencies = self.extract_python_dependencies(&toml);

            return Ok(Some(ProjectMetadata {
                name,
                project_type: ProjectType::Python,
                build_system: Some("pip".to_string()),
                dependencies,
                is_monorepo: false,
                root_path: self.config.workspace_path.clone(),
            }));
        } else if requirements_txt_path.exists() {
            let name = self.workspace_name();
            let dependencies = self.extract_requirements_txt_dependencies()?;

            return Ok(Some(ProjectMetadata {
                name,
                project_type: ProjectType::Python,
                build_system: Some("pip".to_string()),
                dependencies,
                is_monorepo: false,
                root_path: self.config.workspace_path.clone(),
            }));
        }

        Ok(None)
    }

    fn try_extract_go_metadata(&self) -> Result<Option<ProjectMetadata>> {
        let go_mod_path = self.config.workspace_path.join("go.mod");

        if !go_mod_path.exists() {
            return Ok(None);
        }

        let content = fs::read_to_string(&go_mod_path)?;
        let name = content
            .lines()
            .find(|line| line.starts_with("module "))
            .and_then(|line| line.strip_prefix("module "))
            .map(|s| s.trim().to_string())
            .unwrap_or_else(|| self.workspace_name());

        Ok(Some(ProjectMetadata {
            name,
            project_type: ProjectType::Go,
            build_system: Some("go".to_string()),
            dependencies: Vec::new(), // Could parse require directives if needed
            is_monorepo: false,
            root_path: self.config.workspace_path.clone(),
        }))
    }

    // Helper methods

    fn workspace_name(&self) -> String {
        self.config.workspace_path
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string()
    }

    fn extract_toml_string(&self, toml: &TomlValue, path: &[&str]) -> Option<String> {
        let mut current = toml;
        for key in path {
            current = current.get(key)?;
        }
        current.as_str().map(|s| s.to_string())
    }

    fn extract_toml_dependencies(&self, toml: &TomlValue) -> Vec<String> {
        toml.get("dependencies")
            .and_then(|d| d.as_table())
            .map(|table| table.keys().cloned().collect())
            .unwrap_or_default()
    }

    fn extract_json_dependencies(&self, json: &JsonValue) -> Vec<String> {
        let mut deps = Vec::new();

        if let Some(obj) = json.get("dependencies").and_then(|d| d.as_object()) {
            deps.extend(obj.keys().cloned());
        }

        if let Some(obj) = json.get("devDependencies").and_then(|d| d.as_object()) {
            deps.extend(obj.keys().cloned());
        }

        deps
    }

    fn extract_python_dependencies(&self, toml: &TomlValue) -> Vec<String> {
        // Try project.dependencies first (PEP 621)
        if let Some(deps) = toml.get("project")
            .and_then(|p| p.get("dependencies"))
            .and_then(|d| d.as_array())
        {
            return deps.iter()
                .filter_map(|v| v.as_str())
                .map(|s| s.split_whitespace().next().unwrap_or(s))
                .map(|s| s.to_string())
                .collect();
        }

        // Try poetry dependencies
        if let Some(table) = toml.get("tool")
            .and_then(|t| t.get("poetry"))
            .and_then(|p| p.get("dependencies"))
            .and_then(|d| d.as_table())
        {
            return table.keys().cloned().collect();
        }

        Vec::new()
    }

    fn extract_requirements_txt_dependencies(&self) -> Result<Vec<String>> {
        let path = self.config.workspace_path.join("requirements.txt");
        let content = fs::read_to_string(path)?;

        let deps = content
            .lines()
            .filter(|line| !line.trim().is_empty() && !line.starts_with('#'))
            .map(|line| {
                // Extract package name (before ==, >=, etc.)
                line.split(&['=', '<', '>', ' '][..])
                    .next()
                    .unwrap_or(line)
                    .trim()
                    .to_string()
            })
            .collect();

        Ok(deps)
    }
}
```

**Refactorings**:
- Added support for Python (`pyproject.toml`, `requirements.txt`) and Go (`go.mod`)
- Extracted `workspace_name()` helper for default names
- Extracted `extract_toml_string()` for nested TOML value extraction
- Extracted `extract_toml_dependencies()` for Rust/Python TOML dependency extraction
- Extracted `extract_json_dependencies()` for Node.js dependency extraction (including devDependencies)
- Extracted `extract_python_dependencies()` for Python-specific dependency formats
- Extracted `extract_requirements_txt_dependencies()` for requirements.txt parsing
- Added `root_path` to `ProjectMetadata` for multi-project workspaces
- Used function pointers array for cleaner extractor iteration
- Better error handling with `.context()`
- Graceful fallback to workspace name when project name not found

**Verify**: `cargo test --lib orchestrator::tests` (all tests pass)

### Success Criteria

**Automated:**
- [ ] Tests fail for right reason (Red): `cargo test --lib orchestrator::tests::test_extract_project_metadata -- --nocapture`
- [ ] Tests pass (Green): `cargo test --lib orchestrator::tests::test_extract_project_metadata`
- [ ] All tests pass after refactor: `cargo test --lib orchestrator::tests`
- [ ] Multiple project types detected: Test with various config files
- [ ] Monorepo detected: Test workspace configurations

**Manual:**
- [ ] Project name accurate
- [ ] Project type correct (Rust, Node.js, Python, Go)
- [ ] Dependencies listed
- [ ] Monorepo flag accurate
- [ ] Missing config files handled gracefully

---

## Behavior 8: Session Deduplication

### Test Specification

**Given**: Multiple sessions with similar contexts
**When**: Creating or listing sessions
**Then**:
- Sessions with identical context deduplicated
- Session names generated contextually (based on git branch, recent activity)
- Duplicate sessions marked/linked
- Most recent session preferred
- Session names human-readable

**Edge Cases**:
- Identical contexts → Single session returned
- Similar but different contexts → Separate sessions
- No context differences → Timestamp-based naming
- Very long session names → Truncated with ellipsis

### TDD Cycle

#### 🔴 Red: Write Failing Test

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use std::fs;

    #[test]
    fn test_deduplicate_sessions() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let mut orchestrator = Orchestrator::new(config);

        // Create two sessions with identical contexts
        let session1 = orchestrator.initialize_session().unwrap();
        let session2 = orchestrator.initialize_session().unwrap();

        orchestrator.persist_to_cache(&session1).unwrap();
        orchestrator.persist_to_cache(&session2).unwrap();

        let deduplicated = orchestrator.deduplicate_sessions().unwrap();

        // Should only have one session (most recent)
        assert_eq!(deduplicated.len(), 1);
        assert_eq!(deduplicated[0].id, session2.id);
    }

    #[test]
    fn test_generate_session_name_with_git() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        // Initialize git repo
        std::process::Command::new("git").args(&["init"]).current_dir(workspace).output().unwrap();
        std::process::Command::new("git").args(&["config", "user.name", "Test"]).current_dir(workspace).output().unwrap();
        std::process::Command::new("git").args(&["config", "user.email", "test@test.com"]).current_dir(workspace).output().unwrap();
        std::process::Command::new("git").args(&["checkout", "-b", "feature/new-thing"]).current_dir(workspace).output().unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let session = orchestrator.initialize_session().unwrap();
        let name = orchestrator.generate_session_name(&session).unwrap();

        assert!(name.contains("feature/new-thing") || name.contains("feature-new-thing"));
    }

    #[test]
    fn test_generate_session_name_no_git() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let session = orchestrator.initialize_session().unwrap();
        let name = orchestrator.generate_session_name(&session).unwrap();

        // Should use workspace name + timestamp
        assert!(!name.is_empty());
    }

    #[test]
    fn test_context_hash() {
        let temp_dir = TempDir::new().unwrap();
        let workspace = temp_dir.path();

        fs::write(workspace.join("file1.txt"), "content1").unwrap();

        let config = OrchestratorConfig {
            workspace_path: workspace.to_path_buf(),
            ..Default::default()
        };
        let orchestrator = Orchestrator::new(config);

        let context1 = orchestrator.build_context().unwrap();
        let context2 = orchestrator.build_context().unwrap();

        let hash1 = orchestrator.compute_context_hash(&context1).unwrap();
        let hash2 = orchestrator.compute_context_hash(&context2).unwrap();

        // Identical contexts should have same hash
        assert_eq!(hash1, hash2);
    }
}
```

**Expected Failure**: Compilation errors (missing methods) and test failures.

#### 🟢 Green: Minimal Implementation

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::collections::HashMap;
use sha2::{Sha256, Digest};

#[derive(Debug, Clone)]
pub struct Session {
    pub id: String,
    pub created_at: u64,
    pub state: SessionState,
    pub workspace_path: PathBuf,
    pub name: Option<String>,
    pub context_hash: Option<String>,
}

impl Orchestrator {
    pub fn deduplicate_sessions(&self) -> Result<Vec<Session>> {
        let cache = self.cache.read()
            .map_err(|e| anyhow!("Cache lock poisoned: {}", e))?;

        let mut sessions_by_hash: HashMap<String, Vec<Session>> = HashMap::new();

        for session in cache.values() {
            if let Some(ref hash) = session.context_hash {
                sessions_by_hash
                    .entry(hash.clone())
                    .or_insert_with(Vec::new)
                    .push(session.clone());
            }
        }

        // Keep most recent session for each unique context
        let mut deduplicated = Vec::new();
        for mut sessions in sessions_by_hash.values().cloned() {
            sessions.sort_by(|a, b| b.created_at.cmp(&a.created_at));
            if let Some(most_recent) = sessions.first() {
                deduplicated.push(most_recent.clone());
            }
        }

        Ok(deduplicated)
    }

    pub fn generate_session_name(&self, session: &Session) -> Result<String> {
        let git_info = self.get_detailed_git_info()?;

        let name = if let Some(git) = git_info {
            format!("{}", git.branch)
        } else {
            let workspace_name = self.workspace_name();
            format!("{}", workspace_name)
        };

        Ok(name)
    }

    pub fn compute_context_hash(&self, context: &Context) -> Result<String> {
        let mut hasher = Sha256::new();

        // Hash file tree
        for file in &context.file_tree {
            hasher.update(file.as_bytes());
        }

        // Hash git info
        if let Some(ref git) = context.git_info {
            hasher.update(git.branch.as_bytes());
        }

        // Hash project metadata
        if let Some(ref proj) = context.project_metadata {
            hasher.update(proj.name.as_bytes());
        }

        let result = hasher.finalize();
        Ok(format!("{:x}", result))
    }
}
```

**Run Tests**: `cargo test --lib orchestrator::tests::test_deduplicate_sessions`

#### 🔵 Refactor: Improve Code

**File**: `silmari-oracle/src/orchestrator.rs`

```rust
use std::collections::HashMap;
use sha2::{Sha256, Digest};
use chrono::{DateTime, Utc};

const MAX_SESSION_NAME_LENGTH: usize = 64;

#[derive(Debug, Clone)]
pub struct Session {
    pub id: String,
    pub created_at: u64,
    pub state: SessionState,
    pub workspace_path: PathBuf,
    pub name: Option<String>,
    pub context_hash: Option<String>,
    pub display_name: Option<String>,
}

impl Orchestrator {
    pub fn initialize_session_with_context(&self) -> Result<Session> {
        let mut session = self.initialize_session()?;
        let context = self.build_context()?;

        session.context_hash = Some(self.compute_context_hash(&context)?);
        session.name = Some(self.generate_session_name(&session)?);
        session.display_name = Some(self.generate_display_name(&session, &context)?);

        Ok(session)
    }

    pub fn deduplicate_sessions(&self) -> Result<Vec<Session>> {
        let cache = self.cache.read()
            .map_err(|e| anyhow!("Cache lock poisoned: {}", e))?;

        let sessions_by_hash = self.group_sessions_by_hash(cache.values().cloned().collect());
        let deduplicated = self.select_most_recent_sessions(sessions_by_hash);

        Ok(deduplicated)
    }

    fn group_sessions_by_hash(&self, sessions: Vec<Session>) -> HashMap<String, Vec<Session>> {
        let mut groups: HashMap<String, Vec<Session>> = HashMap::new();

        for session in sessions {
            if let Some(ref hash) = session.context_hash {
                groups
                    .entry(hash.clone())
                    .or_insert_with(Vec::new)
                    .push(session);
            }
        }

        groups
    }

    fn select_most_recent_sessions(&self, groups: HashMap<String, Vec<Session>>) -> Vec<Session> {
        groups
            .into_values()
            .filter_map(|mut sessions| {
                sessions.sort_by(|a, b| b.created_at.cmp(&a.created_at));
                sessions.into_iter().next()
            })
            .collect()
    }

    pub fn generate_session_name(&self, session: &Session) -> Result<String> {
        let components = self.collect_name_components(session)?;
        let name = self.format_session_name(components);
        Ok(name)
    }

    fn collect_name_components(&self, _session: &Session) -> Result<Vec<String>> {
        let mut components = Vec::new();

        // Add git branch if available
        if let Some(git_info) = self.get_detailed_git_info()? {
            components.push(self.sanitize_branch_name(&git_info.branch));
        }

        // Add project name if available
        if let Some(metadata) = self.extract_project_metadata()? {
            if !components.is_empty() {
                components.push(metadata.name);
            }
        }

        // Fallback to workspace name
        if components.is_empty() {
            components.push(self.workspace_name());
        }

        Ok(components)
    }

    fn format_session_name(&self, components: Vec<String>) -> String {
        let name = components.join("-");
        self.truncate_name(name, MAX_SESSION_NAME_LENGTH)
    }

    fn sanitize_branch_name(&self, branch: &str) -> String {
        branch
            .replace('/', "-")
            .replace(' ', "-")
            .chars()
            .filter(|c| c.is_alphanumeric() || *c == '-' || *c == '_')
            .collect()
    }

    fn truncate_name(&self, name: String, max_len: usize) -> String {
        if name.len() <= max_len {
            name
        } else {
            format!("{}...", &name[..max_len.saturating_sub(3)])
        }
    }

    pub fn generate_display_name(&self, session: &Session, context: &Context) -> Result<String> {
        let timestamp = DateTime::<Utc>::from_timestamp(session.created_at as i64 / 1000, 0)
            .map(|dt| dt.format("%Y-%m-%d %H:%M UTC").to_string())
            .unwrap_or_else(|| "Unknown time".to_string());

        let base_name = session.name.as_deref().unwrap_or("Session");

        let activity = self.summarize_recent_activity(context);

        Ok(format!("{} - {} ({})", base_name, timestamp, activity))
    }

    fn summarize_recent_activity(&self, context: &Context) -> String {
        if let Some(ref git_info) = context.git_info {
            if git_info.has_changes {
                return format!("{} files changed",
                    git_info.staged_files.len() + git_info.unstaged_files.len());
            } else {
                return "No changes".to_string();
            }
        }

        "Unknown activity".to_string()
    }

    pub fn compute_context_hash(&self, context: &Context) -> Result<String> {
        let mut hasher = Sha256::new();

        // Hash file tree (sorted for consistency)
        let mut sorted_files = context.file_tree.clone();
        sorted_files.sort();
        for file in sorted_files {
            hasher.update(file.as_bytes());
            hasher.update(&[0]); // Separator
        }

        // Hash git branch
        if let Some(ref git) = context.git_info {
            hasher.update(git.branch.as_bytes());
            hasher.update(&[0]);
        }

        // Hash project metadata
        if let Some(ref proj) = context.project_metadata {
            hasher.update(proj.name.as_bytes());
            hasher.update(proj.project_type.as_str().as_bytes());
            hasher.update(&[0]);
        }

        // Hash active files (if any)
        // Note: Not hashing file contents, just paths for performance
        // Could hash content for more precise deduplication

        let result = hasher.finalize();
        Ok(format!("{:x}", result))
    }
}
```

**Refactorings**:
- Added `initialize_session_with_context()` convenience method combining initialization, context building, and naming
- Extracted `group_sessions_by_hash()` for session grouping logic
- Extracted `select_most_recent_sessions()` for most recent selection
- Extracted `collect_name_components()` for name component gathering
- Extracted `format_session_name()` for name formatting
- Extracted `sanitize_branch_name()` for branch name sanitization
- Extracted `truncate_name()` for name length limiting
- Added `generate_display_name()` for human-readable session names with timestamp and activity
- Extracted `summarize_recent_activity()` for activity summary
- Improved `compute_context_hash()` with sorted files and separators for consistency
- Added `display_name` field to `Session` for richer UI display
- Used `chrono` for timestamp formatting

**Verify**: `cargo test --lib orchestrator::tests` (all tests pass)

### Success Criteria

**Automated:**
- [ ] Tests fail for right reason (Red): `cargo test --lib orchestrator::tests::test_deduplicate_sessions -- --nocapture`
- [ ] Tests pass (Green): `cargo test --lib orchestrator::tests::test_deduplicate_sessions`
- [ ] All tests pass after refactor: `cargo test --lib orchestrator::tests`
- [ ] Context hashing deterministic: Multiple computations produce same hash
- [ ] Session names sanitized: Test with special characters in branch names

**Manual:**
- [ ] Duplicate sessions correctly identified
- [ ] Session names human-readable and contextual
- [ ] Session names include git branch when available
- [ ] Session display names include timestamp and activity
- [ ] Long session names truncated with ellipsis

---

## Integration & E2E Testing

### Integration Tests

**Location**: `silmari-oracle/tests/orchestrator_integration.rs`

**Tests**:
1. **Full Session Lifecycle**: Initialize → Build context → Persist → Retrieve → Close
2. **Context Building with All Components**: File tree + thoughts + git + project metadata
3. **Active File Tracking with Context**: Track files → Include in context → Verify size limits
4. **Session Deduplication with Persistence**: Create sessions → Persist → Deduplicate → Verify
5. **Cross-Component Interactions**: Git info affects session naming, project metadata affects context

### E2E Tests

**Location**: `silmari-oracle/tests/orchestrator_e2e.rs`

**Scenarios**:
1. **New Project Session**:
   - Given: Fresh workspace with git repo and project files
   - When: Orchestrator initializes session
   - Then: Session created with full context, persisted, named correctly

2. **Existing Project Resume**:
   - Given: Workspace with existing sessions in database
   - When: Orchestrator retrieves sessions
   - Then: Sessions loaded, deduplicated, most recent selected

3. **Context Evolution**:
   - Given: Session with initial context
   - When: Files added, git branch changed
   - Then: New context computed, new session created with different hash

4. **Large Workspace Handling**:
   - Given: Workspace with 10k+ files, large thoughts directory
   - When: Building context
   - Then: Context truncated appropriately, performance acceptable (< 5s)

## References

- Research: `thoughts/searchable/research/2026-01-04-rust-orchestrator-port-research.md`
- TypeScript Implementation: `silmari-oracle-wui/src/orchestrator/orchestrator.ts:1-547`
- Current Rust Stub: `silmari-oracle/src/orchestrator.rs:1-50`
- Existing Tests: `silmari-oracle/tests/integration_test.rs`

## Dependencies to Add

```toml
[dependencies]
anyhow = "1.0"
thiserror = "1.0"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
toml = "0.8"
rusqlite = { version = "0.30", features = ["bundled"] }
walkdir = "2.4"
git2 = "0.18"
sha2 = "0.10"
uuid = { version = "1.6", features = ["v4"] }
chrono = "0.4"

[dev-dependencies]
tempfile = "3.8"
```

## Implementation Order

Follow the behavior order (1 → 8) for incremental implementation:
1. Session Initialization (foundation)
2. State Persistence (durability)
3. Context Building (core functionality)
4. Active File Tracking (file content)
5. Thought Retrieval (thought documents)
6. Git Information (version control context)
7. Project Metadata (project understanding)
8. Session Deduplication (optimization)

Each behavior is designed to be implemented and tested independently while building on previous behaviors.
