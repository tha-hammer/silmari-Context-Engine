# Phase 8: Session Deduplication

## Overview

Implement session deduplication based on context hashing, along with contextual session naming. This prevents duplicate sessions for identical workspace states and provides human-readable session identification based on git branch, project metadata, and recent activity.

**Human-Testable Functions**: `deduplicate_sessions()`, `generate_session_name()`, `compute_context_hash()`

## Dependencies

**Requires**: Phase 2 (State Persistence), Phase 3 (Context Building)
**Blocks**: None (final optimization phase)

## Changes Required

### File: silmari-oracle/src/orchestrator.rs

#### Lines 2912-3006: Test Cases (Red Phase)
- Test: `test_deduplicate_sessions` - Verifies identical sessions are deduplicated with most recent kept
- Test: `test_generate_session_name_with_git` - Verifies session names include git branch when available
- Test: `test_generate_session_name_no_git` - Verifies fallback to workspace name + timestamp
- Test: `test_context_hash` - Verifies deterministic context hashing for identical contexts

#### Lines 3015-3091: Minimal Implementation (Green Phase)
- Update `Session` struct to include `name: Option<String>` and `context_hash: Option<String>`
- Import: `use sha2::{Sha256, Digest}` and `use std::collections::HashMap`
- Method: `deduplicate_sessions()` - Groups sessions by context hash, returns most recent per group
- Method: `generate_session_name()` - Creates name from git branch or workspace name
- Method: `compute_context_hash()` - SHA-256 hash of file tree, git info, and project metadata

#### Lines 3100-3272: Refactored Implementation (Blue Phase)
- Add `display_name: Option<String>` to `Session` for richer UI display
- Import: `use chrono::{DateTime, Utc}`
- Constant: `MAX_SESSION_NAME_LENGTH = 64` for name truncation
- Method: `initialize_session_with_context()` - Convenience method combining initialization, context building, and naming
- Extract: `group_sessions_by_hash()` - Session grouping logic
- Extract: `select_most_recent_sessions()` - Most recent selection with functional approach
- Extract: `collect_name_components()` - Name component gathering (git branch, project name, workspace)
- Extract: `format_session_name()` - Name formatting with component joining
- Extract: `sanitize_branch_name()` - Branch name sanitization (replace `/` with `-`, filter special chars)
- Extract: `truncate_name()` - Name length limiting with ellipsis
- Method: `generate_display_name()` - Human-readable session names with timestamp and activity summary
- Extract: `summarize_recent_activity()` - Activity summary from git changes
- Improve: `compute_context_hash()` - Sort files for consistency, add separators, include project type

### File: silmari-oracle/Cargo.toml
- Add dependency: `sha2 = "0.10"` (for context hashing)
- Add dependency: `chrono = "0.4"` (for timestamp formatting in display names)

## Success Criteria

### Automated Tests

Run these commands to verify implementation:

```bash
# Red phase - tests fail for right reason
cargo test --lib orchestrator::tests::test_deduplicate_sessions -- --nocapture

# Green phase - tests pass
cargo test --lib orchestrator::tests::test_deduplicate_sessions
cargo test --lib orchestrator::tests::test_generate_session_name_with_git
cargo test --lib orchestrator::tests::test_generate_session_name_no_git
cargo test --lib orchestrator::tests::test_context_hash

# Blue phase - all tests pass after refactor
cargo test --lib orchestrator::tests

# Context hashing determinism
cargo test --lib orchestrator::tests::test_context_hash -- --nocapture

# Session name sanitization with special characters
cargo test --lib orchestrator::tests::test_sanitize_branch_name
```

**Expected Results**:
- ✅ All 4+ tests pass
- ✅ Context hashing is deterministic (multiple computations produce same hash)
- ✅ Session names sanitized (special characters handled)
- ✅ No clippy warnings
- ✅ Code is formatted

### Manual Verification

Test deduplication and naming interactively:

```rust
use silmari_oracle::orchestrator::{Orchestrator, OrchestratorConfig};
use std::path::PathBuf;

fn main() {
    // Test 1: Session deduplication
    let config = OrchestratorConfig {
        workspace_path: PathBuf::from("."),
    };
    let mut orchestrator = Orchestrator::new(config);

    // Create multiple sessions with identical context
    let session1 = orchestrator.initialize_session_with_context().unwrap();
    let session2 = orchestrator.initialize_session_with_context().unwrap();

    orchestrator.persist_to_cache(&session1).unwrap();
    orchestrator.persist_to_cache(&session2).unwrap();

    let deduplicated = orchestrator.deduplicate_sessions().unwrap();

    println!("Created 2 sessions, deduplicated to: {}", deduplicated.len());
    if deduplicated.len() == 1 {
        println!("✅ Deduplication successful");
        println!("   Kept session: {}", deduplicated[0].id);
        println!("   Session name: {:?}", deduplicated[0].name);
    } else {
        println!("❌ Expected 1 session, got {}", deduplicated.len());
    }

    // Test 2: Session naming with git
    if let Some(name) = &session1.name {
        println!("\n✅ Session name generated: {}", name);
        println!("   Length: {} chars", name.len());

        // Check for git branch in name
        if name.contains("-") || name.len() > 0 {
            println!("   Appears to be contextual (contains branch or project info)");
        }
    } else {
        println!("\n❌ No session name generated");
    }

    // Test 3: Display name with timestamp
    if let Some(display) = &session1.display_name {
        println!("\n✅ Display name generated: {}", display);
        println!("   Contains timestamp: {}", display.contains("UTC") || display.contains("2026"));
    } else {
        println!("\n❌ No display name generated");
    }

    // Test 4: Context hash consistency
    let context1 = orchestrator.build_context().unwrap();
    let context2 = orchestrator.build_context().unwrap();

    let hash1 = orchestrator.compute_context_hash(&context1).unwrap();
    let hash2 = orchestrator.compute_context_hash(&context2).unwrap();

    if hash1 == hash2 {
        println!("\n✅ Context hashing is deterministic");
        println!("   Hash: {}...", &hash1[..16]);
    } else {
        println!("\n❌ Context hashing is non-deterministic");
        println!("   Hash1: {}...", &hash1[..16]);
        println!("   Hash2: {}...", &hash2[..16]);
    }

    // Test 5: Long name truncation
    // (Create a test case with very long branch name)
    let long_branch = "feature/this-is-a-very-long-branch-name-that-should-be-truncated-to-avoid-ui-issues";
    let truncated = orchestrator.truncate_name(long_branch.to_string(), 64);

    if truncated.len() <= 64 {
        println!("\n✅ Long names truncated properly");
        println!("   Original length: {}", long_branch.len());
        println!("   Truncated length: {}", truncated.len());
        println!("   Truncated name: {}", truncated);
    } else {
        println!("\n❌ Name truncation failed");
    }
}
```

**Verification Checklist**:
- [ ] Duplicate sessions correctly identified by context hash
- [ ] Most recent session selected when duplicates exist
- [ ] Session names human-readable and contextual
- [ ] Session names include git branch when available (format: `feature-new-thing`)
- [ ] Session names fallback to workspace name without git
- [ ] Session display names include timestamp (format: `YYYY-MM-DD HH:MM UTC`)
- [ ] Session display names include activity summary (e.g., `3 files changed`)
- [ ] Long session names truncated with ellipsis at 64 characters
- [ ] Branch names sanitized (slashes become dashes, special chars filtered)
- [ ] Context hash deterministic (same context = same hash)
- [ ] Different contexts produce different hashes
- [ ] No panics with missing git info or project metadata

## Implementation Notes

### Key Design Decisions

1. **SHA-256 for Context Hashing**: Provides collision-resistant hashing of context components (file tree, git info, project metadata)
2. **Sorted File Tree**: Files sorted before hashing to ensure deterministic results regardless of file system order
3. **Session Naming Strategy**: Prioritize git branch > project name > workspace name for contextual identification
4. **Display Names**: Separate field for UI-friendly names with timestamp and activity
5. **Name Sanitization**: Replace slashes and filter special characters for filesystem/URL safety
6. **Truncation with Ellipsis**: Prevents UI overflow while indicating truncation

### Edge Cases Handled

- **Identical contexts**: Sessions deduplicated, most recent kept
- **Similar but different contexts**: Separate sessions maintained (different hashes)
- **No context differences**: Timestamp-based differentiation through created_at
- **Very long session names**: Truncated to 64 chars with `...` ellipsis
- **No git repository**: Fallback to workspace name
- **No project metadata**: Skip project name in session naming
- **Missing timestamp**: Display "Unknown time" instead of crashing
- **Empty file tree**: Hash still computes (based on other components)
- **Concurrent session creation**: Timestamps differ, so hashes may differ

### Context Hash Components

The context hash includes (in order):
1. **File tree** (sorted): All file paths in workspace
2. **Git branch**: Current branch name (if git repo)
3. **Project name and type**: From project metadata (if available)

Note: File contents are NOT hashed for performance. This means sessions with identical file structure but different content may be deduplicated. For more precise deduplication, consider adding content hashing.

### Session Name Format

- **With git**: `{sanitized_branch}` (e.g., `feature-new-thing`)
- **With git + project**: `{sanitized_branch}-{project_name}` (e.g., `feature-new-thing-myapp`)
- **Without git**: `{workspace_name}` (e.g., `silmari-Context-Engine`)

### Display Name Format

`{name} - {timestamp} ({activity})`

Examples:
- `feature-auth - 2026-01-04 15:30 UTC (5 files changed)`
- `main - 2026-01-04 10:15 UTC (No changes)`

### Performance Considerations

- **Deduplication Complexity**: O(n) where n = number of sessions (single pass grouping)
- **Hash Computation**: O(f) where f = number of files (linear scan of file tree)
- **Name Generation**: O(1) (constant time operations)
- **Memory**: HashMap for grouping requires O(n) space

### Database Schema Updates

If persisting session names and hashes:

```sql
ALTER TABLE sessions ADD COLUMN name TEXT;
ALTER TABLE sessions ADD COLUMN context_hash TEXT;
ALTER TABLE sessions ADD COLUMN display_name TEXT;

CREATE INDEX IF NOT EXISTS idx_sessions_context_hash ON sessions(context_hash);
```

### Next Steps

Phase 8 is the final phase of the orchestrator port. After completion:
1. Run integration tests to verify all phases work together
2. Run E2E tests with real workspaces
3. Performance test with large workspaces (10k+ files)
4. Consider adding content-based hashing for more precise deduplication
5. Implement session cleanup/archival for old sessions
