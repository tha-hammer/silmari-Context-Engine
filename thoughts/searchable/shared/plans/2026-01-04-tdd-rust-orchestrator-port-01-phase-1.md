# Phase 1: Session Initialization

## Overview

Implement session creation with unique IDs, timestamps, and workspace validation. This is the foundation for all orchestrator functionality.

**Human-Testable Function**: `initialize_session()`

## Dependencies

**Requires**: None (foundation phase)
**Blocks**: Phase 2 (State Persistence)

## Changes Required

### File: silmari-oracle/src/orchestrator.rs

#### Lines 110-157: Test Cases (Red Phase)
- Add test module structure with `#[cfg(test)]`
- Test: `test_initialize_session_creates_unique_id` - Verifies unique ID generation, timestamp, and active state
- Test: `test_initialize_session_unique_ids` - Verifies concurrent sessions get unique IDs
- Test: `test_initialize_session_invalid_workspace` - Verifies error handling for invalid paths

#### Lines 165-217: Minimal Implementation (Green Phase)
- Struct: `OrchestratorConfig` with `workspace_path: PathBuf`
- Enum: `SessionState` with variants `Active`, `Completed`, `Error`
- Struct: `Session` with fields `id`, `created_at`, `state`, `workspace_path`
- Struct: `Orchestrator` with field `config`
- Method: `Orchestrator::new()` - Constructor
- Method: `Orchestrator::initialize_session()` - Creates session with validation

#### Lines 225-302: Refactored Implementation (Blue Phase)
- Add UUID dependency for better uniqueness
- Extract helper method: `validate_workspace()` - Workspace existence check
- Extract helper method: `generate_session_id()` - UUID-based ID generation
- Extract helper method: `current_timestamp()` - Timestamp with error handling
- Add `Clone` derives for easier testing
- Improve error messages with context

### File: silmari-oracle/Cargo.toml
- Add dependency: `uuid = { version = "1.6", features = ["v4"] }`
- Add dependency: `anyhow = "1.0"`

## Success Criteria

### Automated Tests

Run these commands to verify implementation:

```bash
# Red phase - tests fail for right reason
cargo test --lib orchestrator::tests::test_initialize_session -- --nocapture

# Green phase - tests pass
cargo test --lib orchestrator::tests::test_initialize_session

# Blue phase - all tests pass after refactor
cargo test --lib orchestrator::tests

# Code quality checks
cargo clippy -- -D warnings
cargo fmt -- --check
```

**Expected Results**:
- ✅ All 3 tests pass
- ✅ No clippy warnings
- ✅ Code is formatted

### Manual Verification

Test the function interactively:

```rust
use silmari_oracle::orchestrator::{Orchestrator, OrchestratorConfig};
use std::path::PathBuf;

fn main() {
    // Test 1: Valid workspace
    let config = OrchestratorConfig {
        workspace_path: PathBuf::from("."),
    };
    let orchestrator = Orchestrator::new(config);

    match orchestrator.initialize_session() {
        Ok(session) => {
            println!("✅ Session created: {}", session.id);
            println!("   Timestamp: {}", session.created_at);
            println!("   State: {:?}", session.state);
            println!("   Workspace: {}", session.workspace_path.display());
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 2: Multiple sessions have unique IDs
    let session1 = orchestrator.initialize_session().unwrap();
    let session2 = orchestrator.initialize_session().unwrap();
    assert_ne!(session1.id, session2.id);
    println!("✅ Session IDs are unique");

    // Test 3: Invalid workspace
    let bad_config = OrchestratorConfig {
        workspace_path: PathBuf::from("/nonexistent/path"),
    };
    let bad_orchestrator = Orchestrator::new(bad_config);

    match bad_orchestrator.initialize_session() {
        Ok(_) => println!("❌ Should have failed for invalid path"),
        Err(e) => println!("✅ Correctly rejected invalid path: {}", e),
    }
}
```

**Verification Checklist**:
- [ ] Session IDs are unique and well-formed (format: `session-<uuid>`)
- [ ] Timestamps are accurate (within ~1 second of current time)
- [ ] Invalid workspace paths are properly rejected with descriptive error
- [ ] No panics or unwraps in production code
- [ ] All tests pass consistently (run 5 times to check for timing issues)

## Implementation Notes

### Key Design Decisions

1. **UUID for Session IDs**: Using UUID v4 instead of timestamps ensures true uniqueness even with concurrent session creation
2. **Workspace Validation**: Failing fast on invalid workspace paths prevents downstream errors
3. **Error Handling**: Using `anyhow::Result` for ergonomic error propagation
4. **Test-First Approach**: Tests written before implementation to ensure correct behavior

### Edge Cases Handled

- **Invalid workspace path**: Returns error with descriptive message
- **Concurrent session creation**: UUIDs guarantee uniqueness
- **Missing configuration**: Constructor requires explicit config (no defaults)

### Next Steps

After completing Phase 1, proceed to **Phase 2: State Persistence** to enable session storage and retrieval.
