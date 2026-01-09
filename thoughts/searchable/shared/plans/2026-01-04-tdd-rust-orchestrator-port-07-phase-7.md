# Phase 7: Project Metadata

## Overview

Implement project metadata extraction to identify project types, build systems, dependencies, and monorepo configurations. This enables context-aware behavior based on the project environment.

**Human-Testable Function**: `extract_project_metadata()`

## Dependencies

**Requires**: None (independent component)
**Blocks**: Phase 3 (Context Building)

## Changes Required

### File: silmari-oracle/src/orchestrator.rs

#### Lines 2334-2443: Test Cases (Red Phase)
- Add test module imports: `tempfile::TempDir`, `std::fs`
- Test: `test_extract_project_metadata_rust` - Verifies Rust project detection from `Cargo.toml` with name, type, build system, and dependencies
- Test: `test_extract_project_metadata_nodejs` - Verifies Node.js project detection from `package.json` with dependencies
- Test: `test_extract_project_metadata_none` - Verifies `None` returned for empty workspace
- Test: `test_extract_project_metadata_monorepo` - Verifies monorepo flag detection from workspace configurations

#### Lines 2452-2572: Minimal Implementation (Green Phase)
- Enum: `ProjectType` with variants `Rust`, `NodeJS`, `Python`, `Unknown` (with `PartialEq`, `Debug`, `Clone`)
- Struct: `ProjectMetadata` with fields:
  - `name: String` - Project name from config file
  - `project_type: ProjectType` - Detected project type
  - `build_system: Option<String>` - Build tool (Cargo, npm, pip, etc.)
  - `dependencies: Vec<String>` - List of dependency names
  - `is_monorepo: bool` - Workspace/monorepo flag
- Method: `Orchestrator::extract_project_metadata()` - Entry point that tries each extractor
- Method: `try_extract_rust_metadata()` - Parse `Cargo.toml` for Rust projects
- Method: `try_extract_nodejs_metadata()` - Parse `package.json` for Node.js projects
- Method: `try_extract_python_metadata()` - Placeholder (returns `None`)

#### Lines 2581-2850: Refactored Implementation (Blue Phase)
- Extend `ProjectType` enum with `Go`, `Ruby` variants
- Add `ProjectType::as_str()` method for display names
- Add `root_path: PathBuf` field to `ProjectMetadata`
- Refactor `extract_project_metadata()` to use function pointer array
- Implement `try_extract_python_metadata()` with support for:
  - `pyproject.toml` (PEP 621 and Poetry formats)
  - `requirements.txt` fallback
- Implement `try_extract_go_metadata()` with `go.mod` parsing
- Extract helper methods:
  - `workspace_name()` - Get workspace directory name
  - `extract_toml_string()` - Navigate nested TOML values
  - `extract_toml_dependencies()` - Parse TOML dependency tables
  - `extract_json_dependencies()` - Parse JSON dependencies (including devDependencies)
  - `extract_python_dependencies()` - Handle multiple Python dependency formats
  - `extract_requirements_txt_dependencies()` - Parse requirements.txt
- Improve error handling with `.context()` calls
- Add graceful fallback to workspace name when project name not found

### File: silmari-oracle/Cargo.toml
- Add dependency: `toml = "0.8"` - For parsing Cargo.toml and pyproject.toml
- Add dependency: `serde_json = "1.0"` - For parsing package.json
- Add dependency: `tempfile = "3.8"` (dev-dependency) - For test fixtures

## Success Criteria

### Automated Tests

Run these commands to verify implementation:

```bash
# Red phase - tests fail for right reason
cargo test --lib orchestrator::tests::test_extract_project_metadata -- --nocapture

# Green phase - tests pass
cargo test --lib orchestrator::tests::test_extract_project_metadata

# Blue phase - all tests pass after refactor
cargo test --lib orchestrator::tests

# Additional verification
cargo test --lib orchestrator::tests::test_extract_project_metadata_rust
cargo test --lib orchestrator::tests::test_extract_project_metadata_nodejs
cargo test --lib orchestrator::tests::test_extract_project_metadata_none
cargo test --lib orchestrator::tests::test_extract_project_metadata_monorepo

# Code quality checks
cargo clippy -- -D warnings
cargo fmt -- --check
```

**Expected Results**:
- ✅ All 4 tests pass
- ✅ Rust projects detected correctly
- ✅ Node.js projects detected correctly
- ✅ Monorepo flag set appropriately
- ✅ Empty workspaces return None
- ✅ No clippy warnings
- ✅ Code is formatted

### Manual Verification

Test project detection interactively:

```rust
use silmari_oracle::orchestrator::{Orchestrator, OrchestratorConfig, ProjectType};
use std::path::PathBuf;

fn main() {
    // Test 1: Detect Rust project
    let rust_config = OrchestratorConfig {
        workspace_path: PathBuf::from("/path/to/rust/project"),
    };
    let rust_orchestrator = Orchestrator::new(rust_config);

    match rust_orchestrator.extract_project_metadata() {
        Ok(Some(metadata)) => {
            println!("✅ Rust Project Detected");
            println!("   Name: {}", metadata.name);
            println!("   Type: {}", metadata.project_type.as_str());
            println!("   Build System: {:?}", metadata.build_system);
            println!("   Dependencies: {} found", metadata.dependencies.len());
            println!("   Monorepo: {}", metadata.is_monorepo);
        }
        Ok(None) => println!("❌ No project detected"),
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 2: Detect Node.js project
    let node_config = OrchestratorConfig {
        workspace_path: PathBuf::from("/path/to/node/project"),
    };
    let node_orchestrator = Orchestrator::new(node_config);

    match node_orchestrator.extract_project_metadata() {
        Ok(Some(metadata)) => {
            println!("✅ Node.js Project Detected");
            println!("   Name: {}", metadata.name);
            assert_eq!(metadata.project_type, ProjectType::NodeJS);
            println!("   Dependencies: {:?}", metadata.dependencies);
        }
        Ok(None) => println!("❌ No project detected"),
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 3: Detect Python project
    let python_config = OrchestratorConfig {
        workspace_path: PathBuf::from("/path/to/python/project"),
    };
    let python_orchestrator = Orchestrator::new(python_config);

    match python_orchestrator.extract_project_metadata() {
        Ok(Some(metadata)) => {
            println!("✅ Python Project Detected");
            println!("   Name: {}", metadata.name);
            assert_eq!(metadata.project_type, ProjectType::Python);
            println!("   Build System: {:?}", metadata.build_system);
        }
        Ok(None) => println!("ℹ️  No Python config files found"),
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 4: Empty workspace
    let empty_config = OrchestratorConfig {
        workspace_path: PathBuf::from("/tmp/empty"),
    };
    let empty_orchestrator = Orchestrator::new(empty_config);

    match empty_orchestrator.extract_project_metadata() {
        Ok(None) => println!("✅ Correctly returns None for empty workspace"),
        Ok(Some(_)) => println!("❌ Should not detect project in empty workspace"),
        Err(e) => println!("❌ Error: {}", e),
    }

    // Test 5: Monorepo detection
    let monorepo_config = OrchestratorConfig {
        workspace_path: PathBuf::from("/path/to/monorepo"),
    };
    let monorepo_orchestrator = Orchestrator::new(monorepo_config);

    match monorepo_orchestrator.extract_project_metadata() {
        Ok(Some(metadata)) if metadata.is_monorepo => {
            println!("✅ Monorepo detected correctly");
        }
        Ok(Some(_)) => println!("❌ Monorepo flag not set"),
        Ok(None) => println!("❌ No project detected"),
        Err(e) => println!("❌ Error: {}", e),
    }
}
```

**Verification Checklist**:
- [ ] Rust projects detected from `Cargo.toml` (package and workspace)
- [ ] Node.js projects detected from `package.json`
- [ ] Python projects detected from `pyproject.toml` and `requirements.txt`
- [ ] Go projects detected from `go.mod`
- [ ] Project name extracted correctly from config files
- [ ] Project type matches actual project language
- [ ] Build system identified correctly (Cargo, npm, pip, go)
- [ ] Dependencies list populated (top-level names only)
- [ ] Monorepo flag set when workspace/members configuration present
- [ ] Empty workspaces return `None` without error
- [ ] Multiple project types prioritized correctly (Rust > Node.js > Python > Go)
- [ ] Malformed config files handled gracefully with descriptive errors
- [ ] No panics or unwraps in production code

## Implementation Notes

### Key Design Decisions

1. **Multiple Extractors**: Separate methods for each project type (`try_extract_*_metadata()`) allow independent implementation and testing
2. **Priority Order**: Rust > Node.js > Python > Go reflects common use cases and detection reliability
3. **Graceful Fallbacks**: Missing project names default to workspace directory name
4. **Monorepo Detection**: Simple heuristic based on workspace/members fields (can be extended)
5. **Dependency Simplification**: Only extract package names, not versions or specifiers
6. **Helper Method Extraction**: Common parsing logic factored out for reuse across extractors

### Edge Cases Handled

- **Multiple project types**: Returns first match based on priority order
- **No config files**: Returns `None` (not an error)
- **Monorepo configurations**: Sets `is_monorepo` flag and uses workspace name
- **Malformed config files**: Propagates parse errors with context
- **Missing project name**: Falls back to workspace directory name
- **Multiple Python formats**: Checks PEP 621, Poetry, and requirements.txt in order
- **Dependency version specifiers**: Strips version info to get package name only
- **Dev dependencies**: Node.js extractor includes both regular and dev dependencies

### Project Type Detection Logic

| Project Type | Config File(s) | Monorepo Indicator |
|--------------|----------------|-------------------|
| Rust | `Cargo.toml` | `[workspace]` table |
| Node.js | `package.json` | `"workspaces"` field |
| Python | `pyproject.toml`, `requirements.txt` | N/A |
| Go | `go.mod` | N/A |

### Dependency Extraction

**Rust** (`Cargo.toml`):
```toml
[dependencies]
serde = "1.0"        # Extracts: "serde"
tokio = { version = "1.0", features = ["full"] }  # Extracts: "tokio"
```

**Node.js** (`package.json`):
```json
{
  "dependencies": {
    "express": "^4.18.0"  // Extracts: "express"
  },
  "devDependencies": {
    "typescript": "^5.0.0"  // Extracts: "typescript"
  }
}
```

**Python** (`pyproject.toml` PEP 621):
```toml
[project]
dependencies = [
  "requests>=2.28",  # Extracts: "requests"
  "pydantic==2.0.0"  # Extracts: "pydantic"
]
```

**Python** (`pyproject.toml` Poetry):
```toml
[tool.poetry.dependencies]
requests = "^2.28"  # Extracts: "requests"
```

**Python** (`requirements.txt`):
```
requests>=2.28.0  # Extracts: "requests"
pydantic==2.0.0   # Extracts: "pydantic"
```

**Go** (`go.mod`):
```
module github.com/user/project  # Extracts: "github.com/user/project" as name
// Dependencies not extracted in minimal version
```

### Performance Considerations

- **Early Exit**: Returns on first config file match (no unnecessary parsing)
- **Lazy Evaluation**: Only reads files that exist
- **No External Commands**: Pure file parsing (no `cargo metadata` or `npm list`)
- **Minimal Allocations**: Direct string extraction without intermediate structures

### Future Extensions

Potential enhancements for later phases:
- Extract dependency versions and version constraints
- Parse `dev-dependencies` separately
- Detect test frameworks (pytest, Jest, cargo test)
- Extract `scripts` section from `package.json`
- Detect CI/CD configuration files
- Parse workspace members for monorepos
- Identify language version requirements (rustc, node, python)

### Next Steps

After completing Phase 7, you can proceed to:
- **Phase 3** (requires 4-7): Combine all component behaviors into full context building
- **Other parallel phases** (4-6): Implement remaining independent components (Active Files, Thoughts, Git)
