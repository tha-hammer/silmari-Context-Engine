# Phase 2: State Persistence

## Overview

Implement session persistence to both in-memory cache and SQLite database. This enables session state to survive across restarts and provides fast access through caching.

**Human-Testable Functions**: `persist_to_cache()`, `persist_to_database()`, `get_from_cache()`, `get_from_database()`

## Dependencies

**Requires**: Phase 1 (Session Initialization)
**Blocks**: Phase 3 (Context Building), Phase 8 (Session Deduplication)

## Changes Required

### File: silmari-oracle/src/orchestrator.rs

#### Lines 345-404: Test Cases (Red Phase)
- Test: `test_persist_session_to_cache` - Verifies cache storage and retrieval
- Test: `test_persist_session_to_database` - Verifies database persistence with in-memory SQLite
- Test: `test_get_nonexistent_session` - Verifies None returned for missing sessions

#### Lines 413-507: Minimal Implementation (Green Phase)
- Update `Orchestrator` struct to include `cache: HashMap<String, Session>` and `db: Option<Connection>`
- Method: `Orchestrator::with_connection()` - Constructor with database
- Method: `persist_to_cache()` - Store session in HashMap
- Method: `get_from_cache()` - Retrieve from HashMap
- Method: `persist_to_database()` - SQL INSERT OR REPLACE
- Method: `get_from_database()` - SQL SELECT with error handling
- Method: `initialize_database()` - CREATE TABLE IF NOT EXISTS

#### Lines 516-651: Refactored Implementation (Blue Phase)
- Thread-safe cache using `Arc<RwLock<HashMap<String, Session>>>`
- Extract `SessionState::to_string()` and `SessionState::from_string()` for serialization
- Add `Serialize`/`Deserialize` derives for future JSON support
- Improve error messages with `.context()`
- Add database indexes for performance (`idx_sessions_created_at`, `idx_sessions_state`)
- Add `updated_at` timestamp column
- Use `prepare_cached()` for statement reuse

### File: silmari-oracle/Cargo.toml
- Add dependency: `rusqlite = { version = "0.30", features = ["bundled"] }`
- Add dependency: `serde = { version = "1.0", features = ["derive"] }`

## Success Criteria

### Automated Tests

Run these commands to verify implementation:

```bash
# Red phase - tests fail for right reason
cargo test --lib orchestrator::tests::test_persist_session -- --nocapture

# Green phase - tests pass
cargo test --lib orchestrator::tests::test_persist_session

# Blue phase - all tests pass after refactor
cargo test --lib orchestrator::tests

# Thread safety test (if added)
cargo test --lib orchestrator::tests::test_concurrent_cache_access

# Database schema verification
sqlite3 :memory: < schema.sql  # Verify schema creates successfully
```

**Expected Results**:
- ✅ Cache tests pass (store/retrieve)
- ✅ Database tests pass (persist/query)
- ✅ Nonexistent session returns None
- ✅ No clippy warnings
- ✅ Code is formatted

### Manual Verification

Test persistence interactively:

```rust
use silmari_oracle::orchestrator::{Orchestrator, OrchestratorConfig, Session, SessionState};
use std::path::PathBuf;
use rusqlite::Connection;

fn main() {
    // Test 1: Cache persistence
    let config = OrchestratorConfig {
        workspace_path: PathBuf::from("."),
    };
    let orchestrator = Orchestrator::new(config);

    let session = orchestrator.initialize_session().unwrap();
    orchestrator.persist_to_cache(&session).unwrap();

    match orchestrator.get_from_cache(&session.id) {
        Ok(Some(retrieved)) => {
            println!("✅ Cache: Retrieved session {}", retrieved.id);
            assert_eq!(retrieved.id, session.id);
        }
        Ok(None) => println!("❌ Session not found in cache"),
        Err(e) => println!("❌ Cache error: {}", e),
    }

    // Test 2: Database persistence
    let conn = Connection::open("test_sessions.db").unwrap();
    let config2 = OrchestratorConfig {
        workspace_path: PathBuf::from("."),
    };
    let db_orchestrator = Orchestrator::with_connection(config2, conn).unwrap();

    let session2 = db_orchestrator.initialize_session().unwrap();
    db_orchestrator.persist_to_database(&session2).unwrap();

    match db_orchestrator.get_from_database(&session2.id) {
        Ok(Some(retrieved)) => {
            println!("✅ Database: Retrieved session {}", retrieved.id);
            assert_eq!(retrieved.id, session2.id);
            assert_eq!(retrieved.state, session2.state);
        }
        Ok(None) => println!("❌ Session not found in database"),
        Err(e) => println!("❌ Database error: {}", e),
    }

    // Test 3: Nonexistent session
    match orchestrator.get_from_cache("nonexistent-id") {
        Ok(None) => println!("✅ Correctly returns None for missing session"),
        Ok(Some(_)) => println!("❌ Should not find nonexistent session"),
        Err(e) => println!("❌ Unexpected error: {}", e),
    }

    // Test 4: Database survives restart
    drop(db_orchestrator);  // Close connection

    let conn2 = Connection::open("test_sessions.db").unwrap();
    let config3 = OrchestratorConfig {
        workspace_path: PathBuf::from("."),
    };
    let new_orchestrator = Orchestrator::with_connection(config3, conn2).unwrap();

    match new_orchestrator.get_from_database(&session2.id) {
        Ok(Some(_)) => println!("✅ Session persists across restarts"),
        Ok(None) => println!("❌ Session lost after restart"),
        Err(e) => println!("❌ Database error: {}", e),
    }

    // Cleanup
    std::fs::remove_file("test_sessions.db").ok();
}
```

**Verification Checklist**:
- [ ] Sessions persist to cache successfully
- [ ] Sessions persist to database successfully
- [ ] Sessions retrievable by ID from both sources
- [ ] Cache and database contents are consistent
- [ ] Missing sessions return None (not error)
- [ ] Database schema initializes correctly
- [ ] Sessions survive process restart (database only)
- [ ] No race conditions with concurrent cache access (if threading added)
- [ ] Database connection failure handled gracefully

## Implementation Notes

### Key Design Decisions

1. **Dual Storage**: Cache provides fast access, database provides durability
2. **Thread-Safe Cache**: Using `Arc<RwLock<HashMap>>` allows concurrent access
3. **Optional Database**: `db: Option<Connection>` allows operation without database
4. **Schema Initialization**: Automatically creates tables on first connection
5. **State Serialization**: Custom `to_string`/`from_string` for database storage

### Edge Cases Handled

- **Database connection failure**: Error propagated with context
- **Concurrent writes**: RwLock prevents data races (last write wins)
- **Missing session ID**: Returns `None` instead of error
- **Database schema mismatch**: `CREATE TABLE IF NOT EXISTS` ensures schema exists
- **Invalid state values**: `from_string()` handles unknown states with error

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL,
    state TEXT NOT NULL,
    workspace_path TEXT NOT NULL,
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(state);
```

### Performance Considerations

- **Prepared Statements**: Using `prepare_cached()` for repeated queries
- **Indexes**: Added on `created_at` and `state` for common queries
- **RwLock**: Allows multiple concurrent readers, single writer

### Next Steps

After completing Phase 2, you can proceed to either:
- **Phase 4-7** (parallel): Implement component behaviors (Active Files, Thoughts, Git, Metadata)
- **Phase 3** (depends on 4-7): Combine components into full context building
