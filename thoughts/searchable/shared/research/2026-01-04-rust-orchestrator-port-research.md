---
date: 2026-01-04 12:45:44 -05:00
researcher: tha-hammer
git_commit: abd540e60fa99dcc598e34ebecfa70525cf22bb2
branch: main
repository: silmari-Context-Engine
topic: "Porting Python Orchestrators to Rust"
tags: [research, rust, python, orchestrator, planning-pipeline, porting, cli, subprocess, architecture]
status: complete
last_updated: 2026-01-04
last_updated_by: tha-hammer
---

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│          RUST ORCHESTRATOR PORT: RESEARCH & STRATEGY                    │
│                                                                         │
│             Porting Python CLI Orchestrators to Rust                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Date**: 2026-01-04 12:45:44 -05:00
**Researcher**: tha-hammer
**Git Commit**: `abd540e60fa99dcc598e34ebecfa70525cf22bb2`
**Branch**: `main`
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

How to port the Python orchestrator files (`orchestrator.py` and `planning_orchestrator.py`) into Rust, including:
- Architecture analysis of existing Python implementation
- Rust crate recommendations for equivalent functionality
- Implementation patterns and best practices
- Project structure and module organization
- Porting strategy and roadmap

---

## 📊 Executive Summary

This research documents a comprehensive strategy for porting two Python CLI orchestrators to Rust. The Python implementation consists of 1,963 lines of subprocess-based CLI orchestration code that manages feature tracking, session logging, and Claude Code integration.

**Key Finding**: The codebase is well-suited for Rust porting. There is currently **no Rust code** in the repository, but extensive research documentation exists for the port strategy. The Python code follows clear patterns with subprocess execution, JSON handling, and CLI argument parsing - all with mature Rust equivalents.

**Recommended Rust Stack**:
- **CLI**: `clap` v4.5+ with derive macros
- **Subprocess**: `duct` for shell-like pipelines
- **JSON**: `serde` + `serde_json`
- **Error Handling**: `anyhow` (applications) or `thiserror` (libraries)
- **Interactive Prompts**: `inquire` or `dialoguer`
- **Terminal Colors**: `owo-colors`
- **Configuration**: `config` crate + `dotenv`
- **Logging**: `tracing` (modern) or `log` + `env_logger` (simple)
- **Testing**: `assert_cmd` + `assert_fs`

---

## 🎯 Current Python Implementation Analysis

### File Overview

| File | Lines | Purpose | Key Features |
|------|-------|---------|--------------|
| `orchestrator.py` | 1,367 | Autonomous project builder | Feature complexity detection, MCP setup, session orchestration, git integration, QA test generation |
| `planning_orchestrator.py` | 596 | Planning pipeline CLI | Resume/checkpoint support, interactive prompts, beads integration, multi-step pipeline execution |
| **Total** | **1,963** | **Full orchestration system** | **Complete CLI tooling for automated development** |

### 📦 Core Data Structures

<details>
<summary><strong>orchestrator.py Data Structures (Click to expand)</strong></summary>

**Configuration Constants**:
```python
HARNESS_PATH: Path          # From CONTEXT_ENGINE_PATH env or script dir
DEFAULT_MODEL: str          # "sonnet" or "opus"
MAX_SESSIONS: int           # 100 (safety limit)
SESSION_TIMEOUT: int        # 3600 seconds
RETRY_DELAY: int           # 5 seconds
DEBUG: bool                 # Global flag via CLI
```

**Project Info Dictionary**:
```python
info = {
    'name': str,           # Project name
    'path': Path,          # Project directory
    'stack': str,          # Tech stack description
    'description': str,    # Multi-line description
    'model': str,          # "sonnet" or "opus"
    'mcp_preset': str,     # Optional MCP preset
    'include_qa': bool     # Generate QA features
}
```

**Feature Dictionary** (from `feature_list.json`):
```python
feature = {
    'id': str,              # e.g., "feature-001"
    'name': str,
    'description': str,
    'category': str,
    'priority': int,        # Lower = earlier
    'dependencies': List[str],  # Feature IDs
    'tests': List[str],
    'passes': bool,         # Completed
    'blocked': bool,
    'complexity': str       # 'high', 'medium', 'low'
}
```

**Claude Code Result**:
```python
result = {
    'success': bool,      # returncode == 0
    'output': str,        # stdout
    'error': str,         # stderr
    'elapsed': float,     # Seconds
    'returncode': int
}
```

</details>

<details>
<summary><strong>planning_orchestrator.py Data Structures (Click to expand)</strong></summary>

**CLI Arguments**:
```python
args = argparse.Namespace(
    project: Path,
    ticket: str,
    auto_approve: bool,
    prompt_text: str,
    resume: bool,
    resume_step: str,      # "planning", "requirement_decomposition", "phase_decomposition"
    research_path: str,
    plan_path: str
)
```

**Pipeline Result**:
```python
result = {
    'success': bool,
    'plan_dir': str,
    'epic_id': str,
    'stopped_at': str,
    'failed_at': str,
    'error': str,
    'steps': {
        'planning': {...},
        'requirement_decomposition': {...},
        'phase_decomposition': {...},
        'beads': {...}
    }
}
```

</details>

### 🔧 External Dependencies

**Python Libraries**:
- Standard library only (`subprocess`, `json`, `pathlib`, `argparse`, `datetime`, `typing`)
- `dotenv` (planning_orchestrator.py only)
- Local modules: `planning_pipeline` package

**External Tools** (invoked via subprocess):
- `claude` - Claude Code CLI
- `bd` - Beads issue tracker CLI
- `git` - Version control
- `bash` - Shell script execution
- `which` - Command existence checks

**No pip packages for core orchestrator** - Everything is subprocess-based! This is ideal for Rust porting.

---

## 🚀 Rust Crate Recommendations

### Comprehensive Rust Stack Comparison

| Component | Python | Rust Crate | Alternative | Notes |
|-----------|--------|------------|-------------|-------|
| **CLI Parsing** | `argparse` | `clap` v4.5+ | `pico-args` | Use derive macros for declarative CLI |
| **Subprocess (sync)** | `subprocess.run()` | `duct` | `std::process` | Shell-like pipelines with `\|` operator |
| **Subprocess (async)** | N/A | `tokio::process` | - | For concurrent process management |
| **JSON** | `json` module | `serde` + `serde_json` | `simd-json` | Industry standard, zero boilerplate |
| **Error Handling** | Dict returns | `anyhow` | `thiserror` | `anyhow` for apps, `thiserror` for libs |
| **Path Handling** | `pathlib.Path` | `std::path::PathBuf` | - | Standard library |
| **Terminal Colors** | ANSI codes | `owo-colors` | `colored` | Zero-allocation, zero dependencies |
| **Interactive Prompts** | `input()` | `inquire` | `dialoguer` | Autocomplete, validation, theming |
| **Timestamps** | `datetime` | `chrono` | - | Date/time handling |
| **Regex** | `re` | `regex` | - | Pattern matching |
| **Configuration** | Env vars | `config` + `dotenv` | `envconfig` | Multi-format support |
| **Logging** | Print statements | `tracing` | `log` + `env_logger` | Structured, async-aware |
| **Testing** | `pytest` | `assert_cmd` | - | CLI integration testing |

### 🎨 Detailed Crate Analysis

#### 1️⃣ **clap** - CLI Framework

**Links**:
- [crates.io](https://crates.io/crates/clap)
- [docs.rs](https://docs.rs/clap)
- [Derive tutorial](https://docs.rs/clap/latest/clap/_derive/_tutorial/index.html)

**Why clap?**
- De-facto standard for Rust CLI applications
- Derive macros for declarative definitions
- Automatic help generation
- Subcommands, validation, auto-completion

**Example**:
```rust
use clap::Parser;

#[derive(Parser)]
#[command(name = "orchestrator")]
#[command(about = "Autonomous project builder", long_about = None)]
struct Cli {
    #[arg(short, long)]
    project: Option<PathBuf>,

    #[arg(short, long, default_value = "sonnet")]
    model: String,

    #[arg(long)]
    auto_approve: bool,
}
```

#### 2️⃣ **duct** - Subprocess Pipelines

**Links**:
- [crates.io](https://crates.io/crates/duct)
- [docs.rs](https://docs.rs/duct)

**Why duct?**
- Shell-like command pipelines with `|` operator
- Automatic error handling (non-zero = error)
- Cross-platform reliability
- IO redirection

**Example**:
```rust
use duct::cmd;

// Python: subprocess.run(["claude", "--print", ...])
// Rust:
let output = cmd!("claude", "--print", "--model", model)
    .read()?;

// Pipeline
let filtered = cmd!("ls", "-la")
    .pipe(cmd!("grep", "txt"))
    .read()?;
```

#### 3️⃣ **serde + serde_json** - JSON Handling

**Links**:
- [serde_json crates.io](https://crates.io/crates/serde_json)
- [docs.rs](https://docs.rs/serde_json/latest/serde_json/)
- [Serde website](https://serde.rs/json.html)

**Why serde?**
- Most battle-tested JSON library
- Zero boilerplate with derive macros
- Compile-time type checking
- Massive ecosystem support

**Example**:
```rust
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
struct Feature {
    id: String,
    name: String,
    description: String,
    category: String,
    priority: u32,
    #[serde(default)]
    dependencies: Vec<String>,
    #[serde(default)]
    passes: bool,
    #[serde(default)]
    blocked: bool,
    complexity: Option<String>,
}

#[derive(Serialize, Deserialize)]
struct FeatureList {
    features: Vec<Feature>,
}

// Read JSON
let data = std::fs::read_to_string("feature_list.json")?;
let feature_list: FeatureList = serde_json::from_str(&data)?;

// Write JSON
let json = serde_json::to_string_pretty(&feature_list)?;
std::fs::write("feature_list.json", json)?;
```

#### 4️⃣ **anyhow** - Error Handling

**Links**:
- [crates.io](https://crates.io/crates/anyhow)
- [docs.rs](https://docs.rs/anyhow)
- [GitHub](https://github.com/dtolnay/anyhow)

**Why anyhow?**
- Perfect for CLI applications
- Context-rich error messages
- `.context()` for semantic error traces
- Dynamic error types

**Example**:
```rust
use anyhow::{Context, Result};

fn load_feature_list(path: &Path) -> Result<FeatureList> {
    let data = std::fs::read_to_string(path)
        .context("Failed to read feature_list.json")?;

    let features: FeatureList = serde_json::from_str(&data)
        .context("Failed to parse feature_list.json")?;

    Ok(features)
}
```

**Error Handling Comparison**:

| Python Pattern | Rust Pattern |
|----------------|--------------|
| `try/except` with dict returns | `Result<T, E>` types |
| `if result.returncode != 0: return {"success": False, ...}` | `cmd.read().context("Command failed")?` |
| Silent bare `except:` | Not possible - must handle all cases |
| Error messages in dicts | `.context()` for semantic traces |

#### 5️⃣ **inquire** - Interactive Prompts

**Links**:
- [crates.io](https://crates.io/crates/inquire)
- [docs.rs](https://docs.rs/inquire)
- [GitHub](https://github.com/mikaelmello/inquire)

**Why inquire?**
- Feature-rich (autocomplete, custom types, validation)
- Replaces Python's `input()` with better UX
- Built-in multi-select, date pickers, confirmation

**Example**:
```rust
use inquire::{Confirm, Select, Text};

// Python: choice = input("Continue? [Y/n]: ").strip().lower()
// Rust:
let continue = Confirm::new("Continue?")
    .with_default(true)
    .prompt()?;

// Menu selection
let options = vec!["Python", "Rust", "Go"];
let choice = Select::new("Select stack:", options).prompt()?;

// Multi-line input
let description = Text::new("Project description:")
    .with_help_message("Enter a blank line to finish")
    .prompt()?;
```

#### 6️⃣ **owo-colors** - Terminal Colors

**Links**:
- [crates.io](https://crates.io/crates/owo-colors)
- [docs.rs](https://docs.rs/owo-colors)

**Why owo-colors?**
- Zero-allocation, zero-cost abstractions
- Zero dependencies
- Automatic NO_COLOR/FORCE_COLOR support
- TTY detection

**Example**:
```rust
use owo_colors::OwoColorize;

// Python: print(f"{Colors.GREEN}Success{Colors.END}")
// Rust:
println!("{}", "Success".green());
println!("{}", "Error".red().bold());
println!("{}", "Warning".yellow());
```

---

## 🏗️ Proposed Rust Project Structure

Based on the Python implementation and Rust best practices:

```
src/
├── main.rs                          # Entry point, CLI dispatch
├── lib.rs                           # Library exports
├── cli/
│   ├── mod.rs
│   ├── orchestrator.rs              # Full orchestrator CLI (orchestrator.py)
│   └── planning.rs                  # Planning-only CLI (planning_orchestrator.py)
├── orchestrator/
│   ├── mod.rs
│   ├── config.rs                    # Configuration constants (lines 27-33)
│   ├── complexity.rs                # Feature complexity detection (lines 39-101)
│   ├── features.rs                  # feature_list.json handling (lines 421-502)
│   ├── session.rs                   # Session logging (lines 1099-1127)
│   └── loop.rs                      # Main implementation loop (lines 1171-1245)
├── planning/
│   ├── mod.rs
│   ├── pipeline.rs                  # PlanningPipeline wrapper
│   ├── steps.rs                     # Step implementations
│   ├── checkpoints.rs               # Interactive checkpoint prompts
│   └── helpers.rs                   # Output parsing, file discovery
├── runners/
│   ├── mod.rs
│   ├── claude.rs                    # Claude CLI wrapper (lines 905-1093)
│   └── beads.rs                     # Beads CLI wrapper
├── output/
│   ├── mod.rs
│   ├── colors.rs                    # ANSI color helpers (lines 148-166)
│   └── progress.rs                  # Progress bar rendering (lines 168-173)
├── types.rs                         # Core type definitions
└── error.rs                         # Error types

tests/
├── integration/
│   ├── test_orchestrator.rs
│   └── test_planning.rs
└── fixtures/
    ├── feature_list.json
    └── sample_project/

Cargo.toml                           # Dependencies
```

### 📋 Module Breakdown

<details>
<summary><strong>Core Modules (Click to expand)</strong></summary>

**types.rs** - Core Type Definitions:
```rust
pub struct ProjectInfo {
    pub name: String,
    pub path: PathBuf,
    pub stack: String,
    pub description: String,
    pub model: String,
    pub mcp_preset: Option<String>,
    pub include_qa: bool,
}

pub struct Feature {
    pub id: String,
    pub name: String,
    pub description: String,
    pub category: String,
    pub priority: u32,
    pub dependencies: Vec<String>,
    pub tests: Vec<String>,
    pub passes: bool,
    pub blocked: bool,
    pub complexity: Option<Complexity>,
}

pub enum Complexity {
    High,
    Medium,
    Low,
}

pub struct FeatureStatus {
    pub total: usize,
    pub completed: usize,
    pub remaining: usize,
    pub blocked: usize,
    pub features: Vec<Feature>,
}

pub struct ClaudeResult {
    pub success: bool,
    pub output: String,
    pub error: String,
    pub elapsed: Duration,
    pub returncode: i32,
}
```

**orchestrator/complexity.rs**:
```rust
use crate::types::{Complexity, Feature};

pub fn detect_complexity(feature: &Feature) -> Complexity {
    // Port lines 39-101 from orchestrator.py
    if let Some(complexity) = &feature.complexity {
        return complexity.clone();
    }

    let mut signals = 0;

    // High complexity keywords
    let high_keywords = ["security", "crypto", "encrypt", "auth", ...];
    for keyword in &high_keywords {
        if feature.description.to_lowercase().contains(keyword) {
            signals += 2;
            break;
        }
    }

    // ... rest of algorithm

    match signals {
        s if s >= 3 => Complexity::High,
        s if s <= 0 => Complexity::Low,
        _ => Complexity::Medium,
    }
}
```

**orchestrator/features.rs**:
```rust
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use crate::types::{Feature, FeatureStatus};

#[derive(Serialize, Deserialize)]
struct FeatureList {
    features: Vec<Feature>,
}

pub fn load_features(path: &Path) -> Result<FeatureStatus> {
    let data = std::fs::read_to_string(path)
        .context("Failed to read feature_list.json")?;

    let list: FeatureList = serde_json::from_str(&data)
        .context("Failed to parse feature_list.json")?;

    let completed = list.features.iter().filter(|f| f.passes).count();
    let blocked = list.features.iter().filter(|f| f.blocked).count();

    Ok(FeatureStatus {
        total: list.features.len(),
        completed,
        remaining: list.features.len() - completed,
        blocked,
        features: list.features,
    })
}

pub fn save_features(path: &Path, features: &[Feature]) -> Result<()> {
    let list = FeatureList {
        features: features.to_vec(),
    };

    let json = serde_json::to_string_pretty(&list)?;
    std::fs::write(path, json).context("Failed to write feature_list.json")?;

    Ok(())
}

pub fn get_next_feature(status: &FeatureStatus) -> Option<&Feature> {
    // Port lines 487-502
    status.features
        .iter()
        .filter(|f| !f.passes && !f.blocked)
        .min_by_key(|f| f.priority)
        .filter(|f| dependencies_met(f, &status.features))
}

fn dependencies_met(feature: &Feature, all_features: &[Feature]) -> bool {
    feature.dependencies.iter().all(|dep_id| {
        all_features
            .iter()
            .any(|f| &f.id == dep_id && f.passes)
    })
}
```

**runners/claude.rs**:
```rust
use anyhow::{Context, Result};
use duct::cmd;
use std::time::{Duration, Instant};
use crate::types::ClaudeResult;

pub fn run_claude(
    project_path: &Path,
    prompt: &str,
    model: &str,
    timeout: Duration,
) -> Result<ClaudeResult> {
    let start = Instant::now();

    // Write prompt to file
    let prompt_file = project_path.join(".agent/current-prompt.md");
    std::fs::create_dir_all(prompt_file.parent().unwrap())?;
    std::fs::write(&prompt_file, prompt)?;

    // Run claude
    let output = cmd!(
        "claude",
        "--print",
        "--model", model,
        "--permission-mode", "bypassPermissions",
        "--output-format", "text",
        prompt
    )
    .dir(project_path)
    .read()
    .context("Failed to run claude")?;

    let elapsed = start.elapsed();

    Ok(ClaudeResult {
        success: true,
        output,
        error: String::new(),
        elapsed,
        returncode: 0,
    })
}

pub fn run_claude_interactive(
    project_path: &Path,
    prompt: &str,
    model: &str,
) -> Result<ClaudeResult> {
    // Port lines 962-1093
    // Use std::process::Command with inherit stdio
    use std::process::Command;

    let prompt_file = project_path.join(".agent/current-prompt.md");
    std::fs::create_dir_all(prompt_file.parent().unwrap())?;
    std::fs::write(&prompt_file, prompt)?;

    let start = Instant::now();

    let status = Command::new("claude")
        .args(&["--model", model, "--permission-mode", "bypassPermissions"])
        .arg(prompt_file)
        .current_dir(project_path)
        .status()?;

    let elapsed = start.elapsed();

    Ok(ClaudeResult {
        success: status.success(),
        output: "Interactive session completed".to_string(),
        error: String::new(),
        elapsed,
        returncode: status.code().unwrap_or(-1),
    })
}
```

</details>

---

## 🔄 Architecture Comparison

### Python vs Rust Pattern Mapping

| Python Pattern | Rust Equivalent | Notes |
|----------------|----------------|-------|
| **Dicts for data** | Strongly-typed structs with `#[derive(Serialize, Deserialize)]` | Compile-time safety |
| **Dict returns for errors** | `Result<T, E>` with `anyhow` | Proper error propagation |
| **`subprocess.run()`** | `duct::cmd!()` or `std::process::Command` | More ergonomic in Rust |
| **`json.load()` / `json.dump()`** | `serde_json::from_str()` / `to_string_pretty()` | Zero boilerplate |
| **`input()` for prompts** | `inquire::Confirm`, `Text`, `Select` | Better UX, validation |
| **ANSI color codes** | `owo_colors::OwoColorize` | Zero-allocation |
| **`argparse`** | `clap` with derive macros | Declarative CLI |
| **`pathlib.Path`** | `std::path::PathBuf` | Similar API |
| **`try/except`** | `Result` + `?` operator + `.context()` | Ergonomic error handling |
| **`datetime`** | `chrono` | Comprehensive date/time |
| **Global `DEBUG` flag** | `lazy_static!` or CLI config struct | Thread-safe |

### Subprocess Handling Comparison

**Python (orchestrator.py:927-960)**:
```python
result = subprocess.run(
    cmd,
    cwd=project_path,
    capture_output=True,
    text=True,
    timeout=timeout
)
return {
    "success": result.returncode == 0,
    "output": result.stdout,
    "error": result.stderr,
    "elapsed": elapsed,
    "returncode": result.returncode
}
```

**Rust Equivalent**:
```rust
let start = Instant::now();

let output = cmd!("claude", "--print", ...)
    .dir(project_path)
    .read()
    .context("Claude command failed")?;

let elapsed = start.elapsed();

Ok(ClaudeResult {
    success: true,
    output,
    error: String::new(),
    elapsed,
    returncode: 0,
})
```

**Benefits in Rust**:
1. ✅ Type-safe result struct instead of dict
2. ✅ `duct` automatically handles non-zero exit codes
3. ✅ `.context()` provides semantic error traces
4. ✅ Compile-time verification of all fields

---

## 🛣️ Implementation Roadmap

### Phase 1: Core Types & Configuration ⏱️ 1 day

**Goal**: Establish type-safe foundation

**Tasks**:
- [ ] Define core structs in `types.rs` (`ProjectInfo`, `Feature`, `FeatureStatus`, `ClaudeResult`)
- [ ] Implement `config.rs` with constants (port lines 27-33)
- [ ] Set up `error.rs` with `anyhow` integration
- [ ] Create `Cargo.toml` with dependencies
- [ ] Basic CLI skeleton in `main.rs` with `clap`

**Success Criteria**:
- All types compile
- CLI accepts `--help` and basic flags
- No runtime dependencies on Python code

---

### Phase 2: Feature Management ⏱️ 1 day

**Goal**: Port feature tracking and JSON handling

**Tasks**:
- [ ] Implement `orchestrator/features.rs`:
  - `load_features()` - Read `feature_list.json`
  - `save_features()` - Write `feature_list.json`
  - `get_next_feature()` - Dependency-aware selection (port lines 487-502)
- [ ] Implement `orchestrator/complexity.rs`:
  - `detect_complexity()` - Algorithm port (lines 39-101)
- [ ] Add tests with fixture JSON files
- [ ] Git history sync function (port lines 446-485)

**Success Criteria**:
- Can read and parse `feature_list.json`
- Complexity detection matches Python behavior
- Next feature selection respects dependencies
- Tests pass with sample data

---

### Phase 3: Subprocess Runners ⏱️ 1 day

**Goal**: CLI tool wrappers for `claude`, `bd`, `git`

**Tasks**:
- [ ] Implement `runners/claude.rs`:
  - `run_claude()` - Captured output mode (port lines 905-960)
  - `run_claude_interactive()` - Interactive TTY mode (port lines 962-1093)
- [ ] Implement `runners/beads.rs`:
  - `create_issue()`, `update_issue()`, `list_issues()`
  - JSON command parsing
- [ ] Implement `runners/git.rs`:
  - `is_feature_in_history()` (port lines 446-455)
  - `sync_features()` (port lines 457-485)
- [ ] Add timeout support with `tokio::time::timeout`

**Success Criteria**:
- Can execute `claude` commands
- Can parse `bd --json` output
- Can query git history
- Timeouts work correctly

---

### Phase 4: Session Orchestration ⏱️ 1 day

**Goal**: Main orchestration loop

**Tasks**:
- [ ] Implement `orchestrator/session.rs`:
  - `log_session()` - JSON and text logs (port lines 1099-1127)
- [ ] Implement `orchestrator/loop.rs`:
  - `orchestrate_implementation()` - Main loop (port lines 1171-1245)
  - Consecutive failure tracking
  - Progress display
- [ ] Implement `output/progress.rs`:
  - Progress bar rendering (port lines 168-173)
- [ ] Implement `output/colors.rs`:
  - `print_header()`, `print_status()` (port lines 158-166)

**Success Criteria**:
- Can run full orchestration loop
- Session logs are created
- Progress updates display
- Failure tracking works

---

### Phase 5: Planning Pipeline Integration ⏱️ 1 day

**Goal**: Port `planning_orchestrator.py`

**Tasks**:
- [ ] Implement `cli/planning.rs`:
  - Argument parsing (port lines 24-88)
  - Resume flow (port lines 295-416)
- [ ] Implement `planning/checkpoints.rs`:
  - Checkpoint detection (port lines 315-347)
  - Cleanup prompts (port lines 251-266)
- [ ] Implement `planning/helpers.rs`:
  - File discovery (port lines 419-451)
  - Interactive selection loops
- [ ] Implement `planning/pipeline.rs`:
  - Wrapper for Python `planning_pipeline` module (temporary bridge)
  - Execute from step (port lines 454-590)

**Success Criteria**:
- Can run planning pipeline from Rust CLI
- Resume functionality works
- Checkpoint cleanup works
- Interactive prompts match Python UX

---

### Phase 6: Interactive Prompts ⏱️ 0.5 day

**Goal**: Port all interactive prompts

**Tasks**:
- [ ] Replace all `input()` calls with `inquire`:
  - Project setup wizard (port lines 322-407)
  - MCP setup prompts (port lines 175-291)
  - Multi-line input (port lines 91-109)
  - Confirmation prompts (port lines 232, 402)
- [ ] Menu selections (port lines 354, 391)
- [ ] Error handling for Ctrl+C

**Success Criteria**:
- All interactive flows work
- Ctrl+C handled gracefully
- Default values work correctly

---

### Phase 7: Testing & Documentation ⏱️ 1 day

**Goal**: Comprehensive test coverage

**Tasks**:
- [ ] Integration tests with `assert_cmd`:
  - Test `--help` output
  - Test feature selection
  - Test session logging
  - Test error handling
- [ ] Unit tests for:
  - Complexity detection
  - Feature dependency resolution
  - JSON parsing edge cases
- [ ] Documentation:
  - README.md with usage examples
  - Inline doc comments
  - Migration guide from Python

**Success Criteria**:
- All tests pass
- Code coverage > 80%
- Documentation complete

---

### Phase 8: Performance & Polish ⏱️ 0.5 day

**Goal**: Optimize and finalize

**Tasks**:
- [ ] Profile subprocess execution
- [ ] Add progress bars with `indicatif`
- [ ] Implement parallel subprocess execution (if beneficial)
- [ ] Add shell completion generation (clap feature)
- [ ] Binary size optimization (release profile)

**Success Criteria**:
- Performance matches or exceeds Python
- Binary size reasonable
- Shell completions work

---

### Total Estimated Effort: **7 days**

**Phases 1-3**: Core foundation (3 days)
**Phases 4-5**: Orchestration logic (2 days)
**Phases 6-8**: UX & polish (2 days)

---

## 📝 Code References

### Python Orchestrator Files

**orchestrator.py** (`/home/maceo/Dev/silmari-Context-Engine/orchestrator.py`):
- **Lines 27-33**: Configuration constants (port to `config.rs`)
- **Lines 39-101**: Feature complexity detection algorithm (port to `complexity.rs`)
- **Lines 148-166**: Color output classes (port to `output/colors.rs` with `owo-colors`)
- **Lines 168-173**: Progress bar rendering (port to `output/progress.rs`)
- **Lines 175-291**: MCP setup interactive flow (port with `inquire`)
- **Lines 322-407**: Project setup wizard (port with `inquire`)
- **Lines 421-444**: `get_feature_status()` - Read feature_list.json (port to `features.rs`)
- **Lines 446-485**: Git history sync (port to `runners/git.rs`)
- **Lines 487-502**: `get_next_feature()` - Dependency-aware selection (port to `features.rs`)
- **Lines 905-960**: `run_claude_code()` - Captured output (port to `runners/claude.rs`)
- **Lines 962-1093**: `run_claude_code_interactive()` - Interactive TTY (port to `runners/claude.rs`)
- **Lines 1099-1127**: Session logging (port to `session.rs`)
- **Lines 1171-1245**: Main orchestration loop (port to `loop.rs`)
- **Lines 1279-1363**: CLI argument parsing (port to `cli/orchestrator.rs` with `clap`)

**planning_orchestrator.py** (`/home/maceo/Dev/silmari-Context-Engine/planning_orchestrator.py`):
- **Lines 24-88**: Argument parsing (port to `cli/planning.rs` with `clap`)
- **Lines 91-109**: `collect_prompt()` - Multi-line input (port with `inquire`)
- **Lines 112-134**: Prerequisite checks (port to `planning/helpers.rs`)
- **Lines 167-174**: Color class (port to `output/colors.rs`)
- **Lines 295-416**: Resume flow handling (port to `cli/planning.rs`)
- **Lines 419-451**: Interactive file selection loop (port to `planning/helpers.rs`)
- **Lines 454-590**: Execute from step (port to `planning/pipeline.rs`)

---

## 🗂️ Historical Context (from thoughts/)

### Existing Rust Porting Research

**Primary Resource**: `thoughts/shared/research/2026-01-01-rust-pipeline-port.md` (611 lines)
- Comprehensive analysis of porting opportunities
- Recommended Rust stack (matches this research)
- Proposed project structure
- Estimated effort: 3-5 days (similar to our 7-day estimate)

This document validates our findings and provides additional implementation details.

### Related Implementation Plans

**TDD Plans** (found via research):
- `thoughts/shared/plans/2026-01-01-tdd-integrated-orchestrator.md` - 8-phase TDD plan
- `thoughts/shared/plans/2026-01-01-tdd-loop-runner-orchestrator-00-overview.md` - 7-phase plan with resume state
- `thoughts/shared/plans/2026-01-01-tdd-resume-pipeline-integration-00-overview.md` - Checkpoint management plan

These plans provide test-driven development guidance for the Python implementation, which can inform Rust test design.

### CLI Documentation

**How-To Guides**:
- `thoughts/shared/docs/2026-01-01-how-to-use-cli-commands.md` - Complete CLI usage guide
- `thoughts/shared/docs/2025-12-31-how-to-run-planning-pipeline.md` - Pipeline execution guide

These documents describe expected behavior that Rust port must match.

---

## 🔗 Related Research

### Web Research Findings

**Rust CLI Best Practices** (from web-search-researcher agent):
- [Rust CLI Book](https://rust-cli.github.io/book/) - Official comprehensive guide
- [Rain's Rust CLI Recommendations](https://rust-cli-recommendations.sunshowers.io/) - Opinionated best practices
- [Command-Line Rust (O'Reilly)](https://github.com/kyclark/command-line-rust) - Book with examples

**Key Insights**:
1. **clap is the standard** - 97M+ downloads/month, used by cargo, ripgrep, bat
2. **owo-colors recommended over termcolor** - Zero dependencies, better API
3. **anyhow for applications, thiserror for libraries** - Clear guidance on error handling
4. **inquire over dialoguer** - More features (autocomplete, custom types)
5. **tracing over log** - Modern, async-aware structured logging

### Crate Ecosystem Analysis

| Crate | Downloads/Month | Maturity | Recommendation |
|-------|-----------------|----------|----------------|
| clap | 97M+ | Stable | ✅ Use |
| serde_json | 170M+ | Stable | ✅ Use |
| anyhow | 65M+ | Stable | ✅ Use |
| owo-colors | 3M+ | Stable | ✅ Use |
| inquire | 400K+ | Growing | ✅ Use |
| duct | 2M+ | Stable | ✅ Use |
| chrono | 110M+ | Stable | ✅ Use |

---

## ❓ Open Questions

1. **Python Bridge vs Full Rewrite**:
   - Should we keep Python `planning_pipeline` module and call from Rust?
   - Or port the entire `planning_pipeline/` package to Rust?
   - **Recommendation**: Phase 1 uses Python bridge, Phase 2 ports to pure Rust

2. **Async vs Sync**:
   - Current Python is synchronous with timeouts
   - Should Rust use `tokio` for async subprocess management?
   - **Recommendation**: Start with sync (`duct`), add async later if needed

3. **Binary Distribution**:
   - Single binary or separate binaries for orchestrator/planning?
   - **Recommendation**: Single binary with subcommands (`orchestrator new`, `orchestrator plan`)

4. **Configuration Format**:
   - Keep Python's dict-based approach or use Rust's config crates?
   - **Recommendation**: Use `config` crate with TOML for better type safety

5. **Testing Strategy**:
   - How to test subprocess calls without mocking?
   - **Recommendation**: Use `assert_cmd` for integration tests, mock for unit tests

---

## 🎯 Next Steps

### Immediate Actions (Priority Order)

1. **Create Rust Project Skeleton** (30 minutes)
   ```bash
   cargo init --name silmari-orchestrator
   # Add dependencies to Cargo.toml
   # Create src/ directory structure
   ```

2. **Port Core Types** (2 hours)
   - Define structs in `types.rs`
   - Add serde derives
   - Write JSON parsing tests

3. **Implement Feature Management** (4 hours)
   - Port `features.rs` functions
   - Port complexity detection
   - Add integration tests

4. **Build Claude Runner** (3 hours)
   - Implement subprocess execution
   - Add timeout support
   - Test with real Claude CLI

5. **Create Basic CLI** (2 hours)
   - Add clap argument parsing
   - Implement `--help` and `--version`
   - Wire up to feature loading

### Decision Points

**After Phase 2** (Day 2):
- ✅ If JSON parsing and feature selection work → Continue
- ❌ If significant issues → Re-evaluate approach

**After Phase 4** (Day 4):
- ✅ If orchestration loop works → Continue with planning integration
- ⚠️ If performance issues → Consider async rewrite

**After Phase 6** (Day 6):
- ✅ If all tests pass → Proceed to polish
- ❌ If major gaps → Extend timeline

---

## 📚 Additional Resources

### Documentation Links

**Rust Fundamentals**:
- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)

**CLI Development**:
- [Command Line Applications in Rust](https://rust-cli.github.io/book/)
- [Clap Derive Tutorial](https://docs.rs/clap/latest/clap/_derive/_tutorial/index.html)
- [Testing CLI Apps with assert_cmd](https://alexwlchan.net/2025/testing-rust-cli-apps-with-assert-cmd/)

**Error Handling**:
- [anyhow vs thiserror](https://www.shakacode.com/blog/thiserror-anyhow-or-how-i-handle-errors-in-rust-apps/)
- [Comprehensive Rust Error Handling](https://google.github.io/comprehensive-rust/error-handling/thiserror-and-anyhow.html)

**JSON & Serialization**:
- [Serde JSON Documentation](https://serde.rs/json.html)
- [JSON in Rust Best Practices](https://blog.logrocket.com/json-and-rust-why-serde_json-is-the-top-choice/)

### Example Projects

**Reference Implementations**:
- [ripgrep](https://github.com/BurntSushi/ripgrep) - High-performance CLI with clap
- [bat](https://github.com/sharkdp/bat) - Terminal tool with colors
- [fd](https://github.com/sharkdp/fd) - Fast find alternative
- [exa](https://github.com/ogham/exa) - Modern ls replacement

---

## ✅ Success Criteria

### Functional Requirements

| Requirement | Python Behavior | Rust Must Match |
|-------------|-----------------|-----------------|
| **Feature Loading** | Parses `feature_list.json` | ✅ Identical parsing |
| **Complexity Detection** | Keyword-based algorithm | ✅ Same algorithm |
| **Next Feature** | Dependency-aware selection | ✅ Same logic |
| **Claude Execution** | Subprocess with timeout | ✅ Same behavior |
| **Session Logging** | JSON + text logs | ✅ Same format |
| **Git Sync** | Query git history | ✅ Same queries |
| **Interactive Prompts** | Python `input()` | ✅ Better UX with inquire |
| **Error Handling** | Dict returns | ✅ Type-safe Results |

### Non-Functional Requirements

| Aspect | Target | Measurement |
|--------|--------|-------------|
| **Performance** | ≤ Python speed | Benchmark subprocess calls |
| **Binary Size** | < 20 MB | Check release build |
| **Memory Usage** | < 50 MB RSS | Profile during execution |
| **Compile Time** | < 2 minutes (clean) | Measure `cargo build` |
| **Test Coverage** | > 80% | `cargo tarpaulin` |
| **Documentation** | Complete | All public APIs documented |

### Acceptance Tests

- [ ] Can run `orchestrator --help` and see all options
- [ ] Can load and parse `feature_list.json` from test fixtures
- [ ] Complexity detection produces same results as Python for 10 test features
- [ ] Can execute `claude` command and capture output
- [ ] Session logs created with correct format
- [ ] Interactive prompts work in terminal
- [ ] All integration tests pass
- [ ] Binary runs on Linux, macOS, Windows

---

## 🏁 Conclusion

**Key Takeaways**:

1. ✅ **Codebase is well-suited for Rust porting** - Clear separation of concerns, subprocess-based, no complex Python-specific patterns
2. ✅ **Mature Rust ecosystem exists** - Every Python component has a robust Rust equivalent
3. ✅ **7-day implementation timeline is realistic** - Phased approach with clear milestones
4. ✅ **Type safety will improve correctness** - Compile-time guarantees replace runtime dict checks
5. ✅ **Performance should match or exceed Python** - Rust's zero-cost abstractions + compiled code

**Recommended Next Action**: Begin Phase 1 (Core Types & Configuration) to validate the approach with a minimal proof-of-concept.

**Risk Mitigation**:
- Keep Python implementation running in parallel during Rust development
- Use Python as integration test oracle (compare outputs)
- Incremental migration: start with orchestrator.py, then planning_orchestrator.py

This research provides a complete blueprint for porting the Python orchestrators to Rust with confidence and clear implementation guidance.

---

**Research Status**: ✅ Complete
**Last Updated**: 2026-01-04
**Next Review**: After Phase 2 completion
