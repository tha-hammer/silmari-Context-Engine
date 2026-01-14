# Phase 4: Active File Tracking

## Overview

Implement active file tracking to include file contents in context. Files are read from the workspace, validated for type (text vs binary), and truncated if they exceed size limits. This provides the LLM with access to files the user is actively working with.

**Human-Testable Function**: `track_active_files()`

## Dependencies

**Requires**: Phase 1 (Session Initialization)
**Blocks**: Phase 3 (Context Building)

## Changes Required

### File: silmari-oracle/src/orchestrator.rs

#### Lines 1097-1194: Test Cases (Red Phase)
- Add test module additions with `tempfile` for test fixtures
- Test: `test_track_active_files` - Verifies multiple files tracked with correct content
- Test: `test_track_active_files_nonexistent` - Verifies missing files skipped gracefully
- Test: `test_track_active_files_size_limit` - Verifies large files truncated at max_file_size
- Test: `test_track_active_files_binary` - Verifies binary files excluded, text files included

#### Lines 1203-1277: Minimal Implementation (Green Phase)
- Struct: `ActiveFile` with fields `path`, `content`, `size_bytes`, `truncated`
- Update `OrchestratorConfig` to add field `max_file_size: usize` (default 1MB)
- Method: `Orchestrator::track_active_files()` - Reads files and creates ActiveFile objects
  - Joins file paths with workspace path
  - Skips nonexistent files with warning
  - Detects and skips binary files with warning
  - Reads file content up to max_file_size
  - Sets truncated flag if size exceeds limit

#### Lines 1285-1394: Refactored Implementation (Blue Phase)
- Add `modified_at: Option<u64>` to `ActiveFile` for staleness detection
- Extract helper method: `track_single_file()` - Handles single file tracking with error
- Extract helper method: `read_file_content()` - Reads content with truncation logic
- Use `filter_map()` for cleaner error handling (skip failed files)
- Use `BufReader` for more efficient file reading
- Add `Pipe` trait for functional-style composition
- Improve error messages with file-specific context
- Gracefully handle file errors (skip and continue) instead of failing entire operation
- Add constant `DEFAULT_MAX_FILE_SIZE = 1_000_000` (1MB)

### File: silmari-oracle/Cargo.toml
- Add dev-dependency: `tempfile = "3.8"` (for test fixtures)

## Success Criteria

### Automated Tests

Run these commands to verify implementation:

```bash
# Red phase - tests fail for right reason
cargo test --lib orchestrator::tests::test_track_active_files -- --nocapture

# Green phase - tests pass
cargo test --lib orchestrator::tests::test_track_active_files

# Blue phase - all tests pass after refactor
cargo test --lib orchestrator::tests

# Binary file exclusion test
cargo test --lib orchestrator::tests::test_track_active_files_binary

# Large file truncation test
cargo test --lib orchestrator::tests::test_track_active_files_size_limit

# Code quality checks
cargo clippy -- -D warnings
cargo fmt -- --check
```

**Expected Results**:
- ✅ All 4 tests pass (basic, nonexistent, size limit, binary)
- ✅ No clippy warnings
- ✅ Code is formatted
- ✅ Binary files correctly excluded
- ✅ Large files correctly truncated

### Manual Verification

Test file tracking interactively:

```rust
use silmari_oracle::orchestrator::{Orchestrator, OrchestratorConfig};
use std::path::PathBuf;
use std::fs;

fn main() {
    // Setup test workspace
    let workspace = PathBuf::from("./test_workspace");
    fs::create_dir_all(&workspace).unwrap();

    fs::write(workspace.join("file1.txt"), "Hello from file 1").unwrap();
    fs::write(workspace.join("file2.txt"), "Content of file 2").unwrap();
    fs::write(workspace.join("large.txt"), "x".repeat(2_000_000)).unwrap(); // 2MB
    fs::write(workspace.join("binary.bin"), &[0u8, 1u8, 255u8, 0u8]).unwrap();

    let config = OrchestratorConfig {
        workspace_path: workspace.clone(),
        max_file_size: 1_000_000, // 1MB
        ..Default::default()
    };
    let orchestrator = Orchestrator::new(config);

    // Test 1: Track valid text files
    let files = vec!["file1.txt".to_string(), "file2.txt".to_string()];
    match orchestrator.track_active_files(&files) {
        Ok(tracked) => {
            println!("✅ Tracked {} files", tracked.len());
            for file in tracked {
                println!("   - {}: {} bytes", file.path, file.size_bytes);
                println!("     Content: {}", file.content);
            }
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 2: Nonexistent file
    let files = vec!["file1.txt".to_string(), "missing.txt".to_string()];
    match orchestrator.track_active_files(&files) {
        Ok(tracked) => {
            println!("✅ Skipped missing file, tracked {}", tracked.len());
            assert_eq!(tracked.len(), 1);
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 3: Large file truncation
    let files = vec!["large.txt".to_string()];
    match orchestrator.track_active_files(&files) {
        Ok(tracked) => {
            let file = &tracked[0];
            println!("✅ Large file: {} bytes (truncated: {})",
                     file.size_bytes, file.truncated);
            assert!(file.truncated);
            assert!(file.content.len() <= 1_000_000);
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 4: Binary file exclusion
    let files = vec!["binary.bin".to_string(), "file1.txt".to_string()];
    match orchestrator.track_active_files(&files) {
        Ok(tracked) => {
            println!("✅ Excluded binary, tracked {} text files", tracked.len());
            assert_eq!(tracked.len(), 1);
            assert_eq!(tracked[0].path, "file1.txt");
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 5: Empty file list
    match orchestrator.track_active_files(&[]) {
        Ok(tracked) => {
            println!("✅ Empty list handled: {} files", tracked.len());
            assert_eq!(tracked.len(), 0);
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Cleanup
    fs::remove_dir_all(workspace).ok();
}
```

**Verification Checklist**:
- [ ] Text files tracked with correct content
- [ ] File metadata included (path, size, modified_at)
- [ ] Nonexistent files skipped with warning (check stderr)
- [ ] Binary files excluded with warning (check stderr)
- [ ] Large files truncated at max_file_size with truncated flag set
- [ ] Empty file list returns empty results (no panic)
- [ ] Multiple files tracked in single call
- [ ] File errors don't crash entire operation (graceful degradation)

## Implementation Notes

### Key Design Decisions

1. **Graceful Degradation**: Failed files are skipped rather than failing the entire operation
2. **Binary Detection**: Uses `is_binary_file()` helper (implementation depends on heuristic)
3. **Size Limits**: Files exceeding `max_file_size` are truncated, not rejected
4. **Metadata Capture**: Includes modification time for staleness detection in future phases
5. **Error Context**: Each file error includes the file path for debugging

### Edge Cases Handled

- **Missing files**: Skipped with warning, operation continues
- **Binary files**: Detected and excluded automatically
- **Large files**: Content truncated, original size preserved in metadata
- **Empty file list**: Returns empty vector (no error)
- **Concurrent modifications**: Always reads latest content (no locking)
- **Permission errors**: Logged and skipped (file-level error handling)

### Binary File Detection

The implementation assumes an `is_binary_file()` helper method exists. Common approaches:

1. **Extension-based**: Check against known text extensions (.txt, .rs, .py, etc.)
2. **Content-based**: Read first N bytes and check for null bytes or non-UTF8 sequences
3. **MIME type**: Use file magic numbers to detect type

Recommended implementation (content-based):
```rust
fn is_binary_file(&self, path: &Path) -> Result<bool> {
    let mut file = fs::File::open(path)?;
    let mut buffer = [0u8; 512];
    let bytes_read = file.read(&mut buffer)?;

    // Check for null bytes (common in binary files)
    Ok(buffer[..bytes_read].contains(&0u8))
}
```

### Performance Considerations

- **BufReader**: Used for efficient reading of large files
- **Take Adapter**: Used to limit reads to max_file_size without loading entire file
- **Filter Map**: Avoids collecting errors into separate collection
- **Parallel Reading**: Could be added with `rayon` for large file lists (future optimization)

### Security Considerations

- **Path Traversal**: Should validate file paths don't escape workspace (add in Blue phase)
- **Symlink Handling**: Should decide policy on following symlinks
- **Size Limits**: Prevents memory exhaustion from extremely large files

### Next Steps

After completing Phase 4, you can proceed to:
- **Phase 5** (parallel): Thoughts file tracking
- **Phase 6** (parallel): Git context gathering
- **Phase 7** (parallel): Metadata collection
- **Phase 3** (depends on 4-7): Combine all components into context building
