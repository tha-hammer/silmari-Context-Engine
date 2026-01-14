# Phase 3: Context Building

## Overview

Implement comprehensive context building that aggregates workspace file tree, thought documents, git repository status, and project metadata. This provides the complete context needed for planning and execution phases.

**Human-Testable Function**: `build_context()`

## Dependencies

**Requires**: Phase 2 (State Persistence), Phase 4 (Active Files), Phase 5 (Thoughts), Phase 6 (Git Integration), Phase 7 (Project Metadata)
**Blocks**: Phase 8 (Session Deduplication)

## Changes Required

### File: silmari-oracle/src/orchestrator.rs

#### Lines 709-796: Test Cases (Red Phase)
- Test: `test_build_context_file_tree` - Verifies file tree contains all workspace files with relative paths
- Test: `test_build_context_with_git` - Verifies git info populated in git repositories
- Test: `test_build_context_no_git` - Verifies git info is None for non-git workspaces
- Test: `test_build_context_size_limit` - Verifies context truncation when exceeding max size

#### Lines 805-891: Minimal Implementation (Green Phase)
- Struct: `Context` with fields `workspace_path`, `file_tree`, `git_info`, `thoughts`, `project_metadata`, `size_bytes`, `truncated`
- Struct: `GitInfo` with fields `branch`, `status`
- Struct: `ProjectMetadata` with fields `name`, `project_type`
- Method: `build_context()` - Aggregates all context components
- Method: `build_file_tree()` - Walks workspace directory tree
- Method: `get_git_info()` - Executes git commands for repository info

#### Lines 898-1039: Refactored Implementation (Blue Phase)
- Switch from CLI `git` to `git2` library for better performance and error handling
- Add `max_context_size` to `OrchestratorConfig` with default constant `DEFAULT_MAX_CONTEXT_SIZE = 5MB`
- Extract helper: `is_binary_file()` - Checks for binary files to exclude from context
- Extract helper: `calculate_context_size()` - Sums total context size
- Add ignored directories: `.git`, `node_modules`, `target`, `.beads`
- Sort file tree for deterministic output
- Add `has_changes` field to `GitInfo` for richer context
- Improve error handling with graceful degradation for optional components (git, thoughts, metadata)

### File: silmari-oracle/Cargo.toml
- Add dependency: `git2 = "0.18"`
- Add dependency: `walkdir = "2.4"`

## Success Criteria

### Automated Tests

Run these commands to verify implementation:

```bash
# Red phase - tests fail for right reason
cargo test --lib orchestrator::tests::test_build_context -- --nocapture

# Green phase - tests pass
cargo test --lib orchestrator::tests::test_build_context

# Blue phase - all tests pass after refactor
cargo test --lib orchestrator::tests

# Test with mixed text/binary workspace
cargo test --lib orchestrator::tests::test_build_context_excludes_binary

# Test with various git states
cargo test --lib orchestrator::tests::test_git_states

# Performance test
cargo test --lib orchestrator::tests::test_build_context_performance -- --ignored
```

**Expected Results**:
- ✅ All 4 core tests pass
- ✅ File tree excludes binary files
- ✅ Git info accurate for various states (clean, dirty, detached HEAD)
- ✅ Context builds in < 1s for 10k files
- ✅ No clippy warnings
- ✅ Code is formatted

### Manual Verification

Test context building interactively:

```rust
use silmari_oracle::orchestrator::{Orchestrator, OrchestratorConfig};
use std::path::PathBuf;

fn main() {
    // Test 1: Basic context building
    let config = OrchestratorConfig {
        workspace_path: PathBuf::from("."),
        max_context_size: 5_000_000, // 5MB
    };
    let orchestrator = Orchestrator::new(config);

    match orchestrator.build_context() {
        Ok(context) => {
            println!("✅ Context built successfully");
            println!("   Files: {} files", context.file_tree.len());
            println!("   Size: {} bytes", context.size_bytes);
            println!("   Truncated: {}", context.truncated);

            if let Some(git) = &context.git_info {
                println!("   Git Branch: {}", git.branch);
                println!("   Git Status: {}", git.status);
                println!("   Has Changes: {}", git.has_changes);
            } else {
                println!("   Git: Not a repository");
            }

            if let Some(metadata) = &context.project_metadata {
                println!("   Project: {} ({})", metadata.name, metadata.project_type);
            }

            // Sample file tree
            println!("\n   Sample files:");
            for file in context.file_tree.iter().take(10) {
                println!("     - {}", file);
            }
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 2: Large workspace (performance)
    use std::time::Instant;
    let start = Instant::now();
    let context = orchestrator.build_context().unwrap();
    let duration = start.elapsed();
    println!("\n✅ Context built in {:?}", duration);
    assert!(duration.as_secs() < 1, "Should build in < 1 second");

    // Test 3: Context size limiting
    let large_config = OrchestratorConfig {
        workspace_path: PathBuf::from("."),
        max_context_size: 1000, // Very small limit
    };
    let large_orchestrator = Orchestrator::new(large_config);

    match large_orchestrator.build_context() {
        Ok(context) => {
            if context.truncated {
                println!("✅ Context correctly truncated for size limit");
                println!("   Size: {} bytes (limit: 1000)", context.size_bytes);
            } else {
                println!("⚠️  Warning: Context not truncated despite small limit");
            }
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 4: Non-git workspace
    use tempfile::TempDir;
    let temp_dir = TempDir::new().unwrap();

    let non_git_config = OrchestratorConfig {
        workspace_path: temp_dir.path().to_path_buf(),
        max_context_size: 5_000_000,
    };
    let non_git_orchestrator = Orchestrator::new(non_git_config);

    match non_git_orchestrator.build_context() {
        Ok(context) => {
            if context.git_info.is_none() {
                println!("✅ Correctly handles non-git workspace");
            } else {
                println!("❌ Should not have git info for non-git workspace");
            }
        }
        Err(e) => println!("❌ Error: {}", e),
    }
}
```

**Verification Checklist**:
- [ ] File tree includes all text files with correct relative paths
- [ ] File tree excludes binary files (images, executables, etc.)
- [ ] File tree excludes ignored directories (.git, node_modules, target, .beads)
- [ ] Git info accurate (branch name, status, has_changes flag)
- [ ] Git info is None for non-git workspaces (no errors)
- [ ] Context size calculated correctly
- [ ] Context truncation works when exceeding max_context_size
- [ ] Context builds quickly (< 1s for typical workspace)
- [ ] No panics or unwraps for missing optional components
- [ ] File tree is sorted (deterministic output)

## Implementation Notes

### Key Design Decisions

1. **Aggregation Pattern**: Context building aggregates data from multiple specialized components (Phases 4-7)
2. **Size Limiting**: Configurable `max_context_size` prevents memory issues with large workspaces
3. **Binary Exclusion**: Automatically excludes binary files by checking for null bytes in first 512 bytes
4. **Graceful Degradation**: Optional components (git, thoughts, metadata) return None instead of error
5. **git2 Library**: Using libgit2 bindings instead of CLI for better performance and error handling
6. **Deterministic Output**: Sorted file tree ensures consistent context across runs

### Edge Cases Handled

- **Empty workspace**: Returns minimal context with empty file tree
- **No git repository**: `git_info` is None (graceful)
- **No thoughts directory**: `thoughts` is empty vector (graceful)
- **Very large workspace**: Context truncated with `truncated` flag set
- **Binary files**: Excluded from file tree automatically
- **Symlinks**: Not followed (prevents infinite loops)
- **Permission errors**: Files skipped with warning (no fatal error)
- **Detached HEAD**: Git branch shows commit hash
- **Dirty working tree**: `has_changes` flag set correctly

### Directory Exclusions

The following directories are automatically excluded from file tree:
- `.git` - Git internal directory
- `node_modules` - Node.js dependencies
- `target` - Rust build artifacts
- `.beads` - Silmari internal directory

### Binary File Detection

Files are considered binary if:
- First 512 bytes contain null byte (0x00)
- File read fails (permissions, etc.) - excluded with warning

### Context Size Calculation

Total size = sum of all file paths + sum of all thought content

This approximates memory usage without reading all file contents.

### Performance Considerations

- **Directory Walking**: Using `walkdir` crate with early filtering
- **Git Operations**: Using `git2` library (faster than spawning processes)
- **Binary Detection**: Only reads first 512 bytes of each file
- **Lazy Loading**: Thoughts and metadata loaded by stubs (implemented in Phases 5, 7)
- **Expected Performance**: < 100ms for 1k files, < 1s for 10k files

### Integration Points

Context building depends on these components:
- **Phase 4 (Active Files)**: Provides file filtering and tracking
- **Phase 5 (Thoughts)**: Provides `get_thoughts()` method
- **Phase 6 (Git Integration)**: Provides enhanced git status
- **Phase 7 (Project Metadata)**: Provides `get_project_metadata()` method

Stubs are used during Phase 3 implementation:
```rust
fn get_thoughts(&self) -> Vec<String> {
    // Placeholder - will be implemented in Behavior 5
    Vec::new()
}

fn get_project_metadata(&self) -> Option<ProjectMetadata> {
    // Placeholder - will be implemented in Behavior 7
    None
}
```

### Testing Strategy

1. **Unit Tests**: Test each component method in isolation
2. **Integration Tests**: Test full context building with real workspace
3. **Performance Tests**: Benchmark with large workspaces (marked `#[ignore]`)
4. **Edge Case Tests**: Test empty workspace, no git, binary files, etc.

### Next Steps

After completing Phase 3:
- Verify integration with completed Phases 4-7
- Replace stub implementations with real component calls
- Add performance benchmarks for large workspaces
- Proceed to **Phase 8: Session Deduplication** for duplicate detection
