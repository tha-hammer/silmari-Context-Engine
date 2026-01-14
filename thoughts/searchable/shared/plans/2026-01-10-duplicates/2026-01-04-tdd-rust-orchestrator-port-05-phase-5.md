# Phase 5: Thought Retrieval

## Overview

Implement thought retrieval from the `thoughts/` directory with categorization, filtering, and sorting capabilities. This enables the orchestrator to discover and incorporate project documentation, research, and user-specific notes into the context.

**Human-Testable Functions**: `retrieve_thoughts()`, `retrieve_thoughts_filtered()`

## Dependencies

**Requires**: None (independent component)
**Blocks**: Phase 3 (Context Building)

## Changes Required

### File: silmari-oracle/src/orchestrator.rs

#### Lines 1453-1554: Test Cases (Red Phase)
- Add import: `use tempfile::TempDir` for test directory setup
- Add import: `use std::fs` for file operations
- Test: `test_retrieve_thoughts_searchable` - Verifies finding markdown files in `thoughts/searchable/` with correct category
- Test: `test_retrieve_thoughts_user_specific` - Verifies user-specific thoughts categorization (e.g., `thoughts/user123/`)
- Test: `test_retrieve_thoughts_no_directory` - Verifies empty list returned when `thoughts/` doesn't exist
- Test: `test_retrieve_thoughts_filtering` - Verifies filtering by category and subcategory

#### Lines 1564-1659: Minimal Implementation (Green Phase)
- Enum: `ThoughtCategory` with variants `Searchable`, `UserSpecific`, `Other`
- Struct: `Thought` with fields `path`, `category`, `content`, `size_bytes`
- Struct: `ThoughtFilter` with fields `categories: Vec<ThoughtCategory>`, `subcategories: Option<Vec<String>>`
- Method: `retrieve_thoughts()` - Walks `thoughts/` directory, finds all `.md` files
- Method: `retrieve_thoughts_filtered()` - Filters thoughts by category and subcategory
- Method: `categorize_thought()` - Determines category from file path (private helper)

#### Lines 1668-1831: Refactored Implementation (Blue Phase)
- Add `Archived` variant to `ThoughtCategory` enum
- Add derives: `Eq`, `Hash` to `ThoughtCategory` for use in collections
- Add field to `Thought`: `subcategory: Option<String>` for granular categorization
- Add field to `Thought`: `modified_at: Option<u64>` for sorting by recency
- Add fields to `ThoughtFilter`: `max_size: Option<usize>`, `limit: Option<usize>`
- Extract helper method: `parse_thought_file()` - Parses file entry into `Thought` with metadata
- Extract helper method: `categorize_thought_detailed()` - Returns both category and subcategory
- Extract helper method: `matches_filter()` - Applies filter logic (private)
- Implement `Default` for `ThoughtFilter` with sensible defaults (Searchable + UserSpecific)
- Sort thoughts by `modified_at` (most recent first)
- Apply limit if specified in filter
- Make `retrieve_thoughts()` delegate to `retrieve_thoughts_filtered()` with default filter

### File: silmari-oracle/Cargo.toml
- Add dependency: `walkdir = "2.4"` for recursive directory traversal
- Add dependency: `tempfile = "3.8"` (dev-dependency for tests)

## Success Criteria

### Automated Tests

Run these commands to verify implementation:

```bash
# Red phase - tests fail for right reason
cargo test --lib orchestrator::tests::test_retrieve_thoughts -- --nocapture

# Green phase - tests pass
cargo test --lib orchestrator::tests::test_retrieve_thoughts

# Blue phase - all tests pass after refactor
cargo test --lib orchestrator::tests

# Test filtering variations
cargo test --lib orchestrator::tests::test_retrieve_thoughts_filtering

# Test sorting by recency
cargo test --lib orchestrator::tests -- --nocapture | grep modified_at

# Code quality checks
cargo clippy -- -D warnings
cargo fmt -- --check
```

**Expected Results**:
- ✅ All 4 tests pass
- ✅ Files found recursively in subdirectories
- ✅ Categories assigned correctly
- ✅ Filtering works for category and subcategory
- ✅ Sorting by recency accurate
- ✅ No clippy warnings
- ✅ Code is formatted

### Manual Verification

Test the function interactively:

```rust
use silmari_oracle::orchestrator::{Orchestrator, OrchestratorConfig, ThoughtFilter, ThoughtCategory};
use std::path::PathBuf;

fn main() {
    let config = OrchestratorConfig {
        workspace_path: PathBuf::from("."),
    };
    let orchestrator = Orchestrator::new(config);

    // Test 1: Retrieve all thoughts
    match orchestrator.retrieve_thoughts() {
        Ok(thoughts) => {
            println!("✅ Found {} thoughts", thoughts.len());
            for thought in &thoughts {
                println!("   - {} ({:?})", thought.path, thought.category);
                if let Some(ref subcat) = thought.subcategory {
                    println!("     Subcategory: {}", subcat);
                }
                println!("     Size: {} bytes", thought.size_bytes);
            }
        }
        Err(e) => println!("❌ Error retrieving thoughts: {}", e),
    }

    // Test 2: Filter by category (searchable only)
    let filter = ThoughtFilter {
        categories: vec![ThoughtCategory::Searchable],
        subcategories: None,
        max_size: None,
        limit: None,
    };

    match orchestrator.retrieve_thoughts_filtered(&filter) {
        Ok(thoughts) => {
            println!("✅ Found {} searchable thoughts", thoughts.len());
            assert!(thoughts.iter().all(|t| t.category == ThoughtCategory::Searchable));
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 3: Filter by subcategory
    let filter = ThoughtFilter {
        categories: vec![ThoughtCategory::Searchable],
        subcategories: Some(vec!["research".to_string()]),
        max_size: None,
        limit: None,
    };

    match orchestrator.retrieve_thoughts_filtered(&filter) {
        Ok(thoughts) => {
            println!("✅ Found {} research thoughts", thoughts.len());
            for thought in &thoughts {
                assert_eq!(thought.subcategory, Some("research".to_string()));
                println!("   - {}", thought.path);
            }
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 4: Size and limit filtering
    let filter = ThoughtFilter {
        categories: vec![ThoughtCategory::Searchable, ThoughtCategory::UserSpecific],
        subcategories: None,
        max_size: Some(10_000), // Only thoughts under 10KB
        limit: Some(5),         // Only first 5 results
    };

    match orchestrator.retrieve_thoughts_filtered(&filter) {
        Ok(thoughts) => {
            println!("✅ Found {} filtered thoughts (limited to 5)", thoughts.len());
            assert!(thoughts.len() <= 5);
            assert!(thoughts.iter().all(|t| t.size_bytes <= 10_000));

            // Verify sorting by recency
            if thoughts.len() > 1 {
                for i in 0..thoughts.len()-1 {
                    if let (Some(t1), Some(t2)) = (thoughts[i].modified_at, thoughts[i+1].modified_at) {
                        assert!(t1 >= t2, "Thoughts should be sorted by recency");
                    }
                }
                println!("✅ Thoughts sorted by recency");
            }
        }
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 5: No thoughts directory
    let empty_config = OrchestratorConfig {
        workspace_path: PathBuf::from("/tmp/nonexistent-workspace-12345"),
    };
    let empty_orchestrator = Orchestrator::new(empty_config);

    match empty_orchestrator.retrieve_thoughts() {
        Ok(thoughts) => {
            assert_eq!(thoughts.len(), 0);
            println!("✅ Empty list returned for missing thoughts directory");
        }
        Err(e) => println!("❌ Should not error: {}", e),
    }
}
```

**Verification Checklist**:
- [ ] All markdown files in `thoughts/` directory found
- [ ] Nested subdirectories traversed correctly
- [ ] Searchable thoughts (`thoughts/searchable/*`) categorized correctly
- [ ] User-specific thoughts (e.g., `thoughts/user123/`) categorized correctly
- [ ] Archived thoughts (`thoughts/archived/`) categorized correctly
- [ ] Subcategories extracted correctly (e.g., `research`, `plans`)
- [ ] Filtering by category works
- [ ] Filtering by subcategory works
- [ ] Size filtering works (max_size honored)
- [ ] Limit filtering works (results truncated)
- [ ] Thoughts sorted by modification time (most recent first)
- [ ] Missing `thoughts/` directory returns empty list (not error)
- [ ] Empty `thoughts/` directory returns empty list
- [ ] Invalid markdown files skipped gracefully
- [ ] File metadata (size, modified_at) populated correctly

## Implementation Notes

### Key Design Decisions

1. **Walking Directory Tree**: Using `walkdir` crate for robust recursive traversal
2. **Category Inference**: Deriving category from path structure (`thoughts/searchable/`, `thoughts/user123/`)
3. **Subcategory Extraction**: Parsing subdirectory name as subcategory (e.g., `searchable/research/` → subcategory: `research`)
4. **Metadata Capture**: Recording file size and modification time for filtering and sorting
5. **Default Filter**: Sensible defaults (Searchable + UserSpecific) for common use case
6. **Sorting by Recency**: Most recently modified files first for relevance

### Edge Cases Handled

- **No thoughts directory**: Returns empty vector without error
- **Empty thoughts directory**: Returns empty vector
- **Invalid markdown files**: Skipped with error logging (using `.ok()` or `.context()`)
- **Very large files**: Size filtering available to truncate results
- **Deeply nested subdirectories**: `walkdir` handles arbitrary depth
- **Non-markdown files**: Filtered out by extension check (`.md`)
- **Symbolic links**: Not followed (`follow_links(false)`)
- **Missing metadata**: `modified_at` is `Option<u64>`, gracefully handles missing timestamps

### Thought Directory Structure

Expected structure:
```
thoughts/
  searchable/
    research/
      2025-12-01-analysis.md
      2026-01-03-findings.md
    plans/
      2026-01-04-implementation-plan.md
  archived/
    old-research.md
  user123/
    personal-notes.md
  user456/
    drafts.md
```

Categories:
- `Searchable`: `thoughts/searchable/**/*.md`
- `UserSpecific`: `thoughts/<username>/**/*.md`
- `Archived`: `thoughts/archived/**/*.md`
- `Other`: Anything else

### Performance Considerations

- **Lazy Evaluation**: Using iterator chains for efficient filtering
- **File I/O**: Reading entire file content may be slow for large thoughts
  - Future optimization: Add content truncation or lazy loading
- **Sorting**: O(n log n) sort by modification time
- **Metadata Access**: `fs::metadata()` requires extra syscall per file

### Filter Semantics

- **Empty categories list**: Match all categories
- **Specified categories**: Match only those categories
- **Subcategories**: Only match if thought has matching subcategory
- **max_size**: Exclude thoughts exceeding byte limit
- **limit**: Truncate results after sorting

### Future Enhancements

Potential improvements for later:
1. Content truncation (don't load entire file if only metadata needed)
2. Content preview (first N lines only)
3. Relevance scoring (keyword matching)
4. Caching (avoid re-reading unchanged files)
5. Incremental updates (watch filesystem for changes)

### Next Steps

After completing Phase 5, you can proceed to:
- **Phase 4, 6, 7** (parallel): Implement other component behaviors (Active Files, Git, Metadata)
- **Phase 3** (depends on 4-7): Combine components into full context building
