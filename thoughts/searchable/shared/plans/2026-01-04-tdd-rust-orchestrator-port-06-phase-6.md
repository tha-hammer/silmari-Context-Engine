# Phase 6: Git Information

## Overview

Implement detailed Git repository information extraction including branch name, working tree status, recent commits, and remote tracking information. This provides context awareness for version control state.

**Human-Testable Function**: `get_detailed_git_info()`

## Dependencies

**Requires**: None (independent component)
**Blocks**: Phase 3 (Context Building)

## Changes Required

### File: silmari-oracle/src/orchestrator.rs

#### Lines 1892-1992: Test Cases (Red Phase)
- Add helper function: `init_git_repo()` - Initialize test Git repository with config
- Test: `test_get_git_info_branch` - Verifies branch name detection (main/master)
- Test: `test_get_git_info_status` - Verifies working tree status tracking (staged, unstaged, untracked files)
- Test: `test_get_git_info_commits` - Verifies recent commit history in reverse chronological order
- Test: `test_get_git_info_not_a_repo` - Verifies None returned for non-Git directories

#### Lines 2002-2087: Minimal Implementation (Green Phase)
- Struct: `DetailedGitInfo` with fields `branch`, `has_changes`, `staged_files`, `unstaged_files`, `untracked_files`, `recent_commits`
- Struct: `CommitInfo` with fields `sha`, `message`, `author`, `timestamp`
- Method: `get_detailed_git_info()` - Extract Git repository information
- Use `git2::Repository::open()` to detect and open repository
- Use `git2::StatusOptions` to get working tree status
- Use `git2::Revwalk` to iterate recent commits (limit 10)
- Return `None` for non-Git directories (no error)

#### Lines 2096-2272: Refactored Implementation (Blue Phase)
- Add constant: `DEFAULT_COMMIT_LIMIT = 10` for commit history limit
- Update `CommitInfo` to include `short_sha` field (7 characters)
- Add `RemoteTracking` struct with fields `remote_name`, `remote_branch`, `ahead`, `behind`
- Update `DetailedGitInfo` to include `remote_tracking: Option<RemoteTracking>`
- Extract method: `get_current_branch()` - Branch name with detached HEAD handling
- Extract method: `get_working_tree_status()` - Status parsing returning tuple of Vec
- Extract method: `is_staged_change()` - Check if status represents staged change
- Extract method: `is_unstaged_change()` - Check if status represents unstaged change
- Extract method: `get_recent_commits()` - Commit history with configurable limit
- Extract method: `get_remote_tracking()` - Remote branch tracking info with ahead/behind counts
- Add `get_git_info_with_limit()` for custom commit history length
- Improve error handling with `.context()`
- Handle edge cases: detached HEAD, renamed files, typechange files
- Trim commit messages to first line only

### File: silmari-oracle/Cargo.toml
- Add dependency: `git2 = "0.18"`
- Add dependency: `tempfile = "3.8"` (dev-dependencies for tests)

## Success Criteria

### Automated Tests

Run these commands to verify implementation:

```bash
# Red phase - tests fail for right reason
cargo test --lib orchestrator::tests::test_get_git_info -- --nocapture

# Green phase - tests pass
cargo test --lib orchestrator::tests::test_get_git_info

# Blue phase - all tests pass after refactor
cargo test --lib orchestrator::tests

# Additional edge case tests
cargo test --lib orchestrator::tests::test_get_git_info_not_a_repo
cargo test --lib orchestrator::tests::test_get_git_info_branch
cargo test --lib orchestrator::tests::test_get_git_info_status
cargo test --lib orchestrator::tests::test_get_git_info_commits

# Code quality checks
cargo clippy -- -D warnings
cargo fmt -- --check
```

**Expected Results**:
- ✅ All 4 Git tests pass
- ✅ Branch name detected correctly (main or master)
- ✅ Working tree status accurate (staged/unstaged/untracked)
- ✅ Commits in reverse chronological order
- ✅ Non-Git directories return None (no panic)
- ✅ No clippy warnings
- ✅ Code is formatted

### Manual Verification

Test the function interactively:

```rust
use silmari_oracle::orchestrator::{Orchestrator, OrchestratorConfig};
use std::path::PathBuf;

fn main() {
    // Test 1: Git repository
    let config = OrchestratorConfig {
        workspace_path: PathBuf::from("."),
    };
    let orchestrator = Orchestrator::new(config);

    match orchestrator.get_detailed_git_info() {
        Ok(Some(git_info)) => {
            println!("✅ Git Info:");
            println!("   Branch: {}", git_info.branch);
            println!("   Has Changes: {}", git_info.has_changes);
            println!("   Staged: {} files", git_info.staged_files.len());
            println!("   Unstaged: {} files", git_info.unstaged_files.len());
            println!("   Untracked: {} files", git_info.untracked_files.len());
            println!("   Recent Commits: {}", git_info.recent_commits.len());

            for (i, commit) in git_info.recent_commits.iter().take(3).enumerate() {
                println!("   {}. {} - {}", i+1, commit.short_sha, commit.message);
            }

            if let Some(tracking) = git_info.remote_tracking {
                println!("   Remote: {}/{}", tracking.remote_name, tracking.remote_branch);
                println!("   Ahead: {}, Behind: {}", tracking.ahead, tracking.behind);
            } else {
                println!("   No remote tracking");
            }
        }
        Ok(None) => println!("❌ Not a Git repository"),
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 2: Non-Git directory
    let temp_config = OrchestratorConfig {
        workspace_path: PathBuf::from("/tmp"),
    };
    let temp_orchestrator = Orchestrator::new(temp_config);

    match temp_orchestrator.get_detailed_git_info() {
        Ok(None) => println!("✅ Correctly returns None for non-Git directory"),
        Ok(Some(_)) => println!("❌ Should not find Git info in /tmp"),
        Err(e) => println!("❌ Unexpected error: {}", e),
    }

    // Test 3: Custom commit limit
    match orchestrator.get_git_info_with_limit(5) {
        Ok(Some(git_info)) => {
            println!("✅ Custom limit: {} commits (max 5)", git_info.recent_commits.len());
            assert!(git_info.recent_commits.len() <= 5);
        }
        Ok(None) => println!("❌ Not a Git repository"),
        Err(e) => println!("❌ Error: {}", e),
    }
}
```

**Verification Checklist**:
- [ ] Branch name is accurate (matches `git branch --show-current`)
- [ ] Working tree status matches `git status` output
- [ ] Staged files match `git diff --cached --name-only`
- [ ] Unstaged files match `git diff --name-only`
- [ ] Untracked files match `git ls-files --others --exclude-standard`
- [ ] Commits listed in reverse chronological order (newest first)
- [ ] Commit messages trimmed to first line only
- [ ] Short SHA is 7 characters
- [ ] Remote tracking info accurate (ahead/behind counts match `git status -sb`)
- [ ] Detached HEAD handled gracefully (shows commit SHA as branch)
- [ ] Fresh repository with no commits handled (empty commit list)
- [ ] Non-Git directories return None without error
- [ ] Submodules are ignored (main repo info only)
- [ ] No panics or unwraps in production code

## Implementation Notes

### Key Design Decisions

1. **git2 Library**: Using libgit2 Rust bindings for robust Git operations
2. **None for Non-Repos**: Returning `None` instead of error for non-Git directories makes the API more ergonomic
3. **Configurable Commit Limit**: Exposing both default and custom limit methods for flexibility
4. **Remote Tracking Optional**: Not all branches have remotes, so `Option<RemoteTracking>` is appropriate
5. **Detailed Status**: Separating staged/unstaged/untracked provides more actionable information

### Edge Cases Handled

- **Not a Git repository**: Returns `None` (no error)
- **Detached HEAD**: Branch field shows commit SHA in format `detached@<sha>`
- **No commits yet**: Returns empty `recent_commits` Vec
- **No remote configured**: Returns `None` for `remote_tracking`
- **Submodules**: Only main repository info extracted
- **Renamed files**: Handled by checking `is_index_renamed()` and `is_wt_renamed()`
- **Type changes**: Handled by checking `is_index_typechange()` and `is_wt_typechange()`
- **Invalid UTF-8 in paths**: Uses `unwrap_or("")` to provide empty string fallback

### Git Status Mapping

The implementation maps `git2::Status` flags to three categories:

**Staged Changes**:
- `is_index_new()` - New file added to index
- `is_index_modified()` - Modified file in index
- `is_index_deleted()` - Deleted file in index
- `is_index_renamed()` - Renamed file in index
- `is_index_typechange()` - File type change in index

**Unstaged Changes**:
- `is_wt_modified()` - Modified file in working tree
- `is_wt_deleted()` - Deleted file in working tree
- `is_wt_renamed()` - Renamed file in working tree
- `is_wt_typechange()` - File type change in working tree

**Untracked Files**:
- `is_wt_new()` - New file not tracked by Git

### Remote Tracking Algorithm

1. Get HEAD reference
2. Find local branch by name
3. Get upstream branch from local branch
4. Parse upstream name (`remote/branch` format)
5. Use `graph_ahead_behind()` to compute divergence
6. Return `None` if any step fails (no remote configured)

### Performance Considerations

- **Commit Limit**: Default limit of 10 commits prevents excessive memory usage
- **Status Options**: `recurse_untracked_dirs(false)` prevents deep traversal
- **Lazy Evaluation**: Git operations only performed when `get_detailed_git_info()` is called
- **Error Propagation**: Uses `?` operator to fail fast on errors

### Testing Strategy

- **Temporary Directories**: Using `tempfile::TempDir` for isolated test repositories
- **Git Commands**: Using `std::process::Command` to set up test Git state
- **Edge Case Coverage**: Tests for branch, status, commits, and non-repo scenarios
- **No Mocking**: Integration tests with real Git operations for confidence

### Next Steps

After completing Phase 6, proceed to:
- **Phase 7: Project Metadata** (independent component)
- **Phase 3: Context Building** (requires all component phases 4-7 complete)
