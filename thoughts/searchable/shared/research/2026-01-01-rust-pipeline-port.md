# Research: Porting orchestrator.py and planning_orchestrator.py to Rust

**Date**: 2026-01-01
**Scope**: Analysis of Python orchestrator implementations and Rust porting strategy

---

## Executive Summary

The project contains two orchestrator implementations:
1. **orchestrator.py** (1367 lines) - Full-featured project builder with Claude Code integration
2. **planning_orchestrator.py** (242 lines) - Lightweight CLI for the planning pipeline

Both rely heavily on subprocess execution, CLI argument parsing, JSON handling, and terminal output - all of which have mature Rust equivalents.

---

## Source File Analysis

### 1. orchestrator.py (Main Orchestrator)

**Location**: `orchestrator.py:1-1367`

#### Core Components

| Component | Lines | Description |
|-----------|-------|-------------|
| Configuration | 27-33 | Constants (HARNESS_PATH, DEFAULT_MODEL, timeouts) |
| Feature Complexity | 39-143 | Heuristic-based complexity detection for features |
| Color Output | 148-173 | ANSI color codes and formatting helpers |
| MCP Setup | 175-292 | Interactive MCP server configuration |
| Project Setup | 297-407 | Harness setup, project info collection |
| Feature Tracking | 421-503 | JSON-based feature_list.json management |
| Claude Integration | 508-1093 | Subprocess calls to `claude` CLI |
| Session Logging | 1099-1128 | JSON session logging |
| Orchestration Loop | 1133-1274 | Main implementation loop |
| CLI Interface | 1279-1367 | argparse-based CLI |

#### Key Functions to Port

```
orchestrator.py:39   - get_feature_complexity(feature: Dict) -> str
orchestrator.py:103  - get_subagent_instructions(complexity, feature_id, description) -> str
orchestrator.py:158  - print_header(text: str)
orchestrator.py:163  - print_status(text: str, status: str)
orchestrator.py:168  - print_progress(completed, total, label)
orchestrator.py:297  - setup_harness(project_path: Path) -> bool
orchestrator.py:421  - get_feature_status(project_path: Path) -> Dict
orchestrator.py:487  - get_next_feature(project_path: Path) -> Optional[Dict]
orchestrator.py:905  - run_claude_code(project_path, prompt, model, timeout) -> Dict
orchestrator.py:962  - run_claude_code_interactive(project_path, prompt, model) -> Dict
orchestrator.py:1133 - orchestrate_new_project(info, max_sessions)
orchestrator.py:1171 - orchestrate_implementation(project_path, model, start_session, max_sessions)
```

#### External Dependencies

- **subprocess**: Execute `claude`, `git`, `bash`, `which` commands
- **argparse**: CLI argument parsing with subcommands
- **json**: feature_list.json read/write, session logging
- **pathlib.Path**: File path handling
- **datetime**: Timestamps for logging
- **time**: Session timing, retry delays
- **sys**: Exit codes, TTY detection

---

### 2. planning_orchestrator.py (Planning CLI)

**Location**: `planning_orchestrator.py:1-242`

#### Core Components

| Component | Lines | Description |
|-----------|-------|-------------|
| Argument Parsing | 20-58 | argparse for --project, --ticket, --auto-approve |
| Prompt Collection | 61-79 | Multi-line stdin input |
| Prerequisites | 82-104 | Check for `claude` and `bd` CLI tools |
| Pipeline Runner | 107-134 | Delegates to PlanningPipeline class |
| Result Display | 137-176 | Color-formatted output |
| Exit Codes | 179-188 | 0 for success, 1 for failure |

#### Key Functions to Port

```
planning_orchestrator.py:20  - parse_args(args: list[str]) -> argparse.Namespace
planning_orchestrator.py:61  - collect_prompt() -> str
planning_orchestrator.py:82  - check_prerequisites() -> dict[str, Any]
planning_orchestrator.py:107 - run_pipeline(project_path, prompt, ticket_id, auto_approve) -> dict
planning_orchestrator.py:147 - display_result(result: dict)
planning_orchestrator.py:179 - get_exit_code(result: dict) -> int
planning_orchestrator.py:191 - main() -> int
```

---

### 3. planning_pipeline Module

**Location**: `planning_pipeline/`

This is the core logic that planning_orchestrator.py wraps:

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py:1-26` | Exports | Public API surface |
| `pipeline.py:1-157` | PlanningPipeline class | 5-step orchestration with revise/restart |
| `steps.py:1-234` | Step implementations | Research (20min timeout), planning, decomposition, beads |
| `claude_runner.py:1-75` | Claude subprocess | Execute `claude --print` |
| `beads_controller.py:1-92` | Beads CLI wrapper | JSON-based bd commands |
| `helpers.py:1-69` | Regex extractors | Parse Claude output |
| `checkpoints.py:1-91` | Interactive prompts | User confirmation with revise/restart/exit options |

---

## Rust Porting Strategy

### Recommended Crate Stack

| Python Dependency | Rust Equivalent | Crate |
|-------------------|-----------------|-------|
| subprocess | Command execution | `std::process::Command` or `subprocess` |
| subprocess (async) | Async processes | `tokio::process` |
| subprocess (timeout) | Timeout handling | `tokio::time::timeout` |
| argparse | CLI arguments | `clap` (v4.5+ with derive) |
| json | JSON serde | `serde` + `serde_json` |
| pathlib.Path | Path handling | `std::path::PathBuf` |
| ANSI colors | Terminal colors | `colored` or `termcolor` |
| input() prompts | Interactive input | `dialoguer` or `inquire` |
| datetime | Timestamps | `chrono` |
| time.sleep | Delays | `std::thread::sleep` or `tokio::time::sleep` |
| re (regex) | Pattern matching | `regex` |

### Suggested Cargo.toml

```toml
[package]
name = "silmari-orchestrator"
version = "0.1.0"
edition = "2021"

[dependencies]
# CLI Framework
clap = { version = "4.5", features = ["derive"] }

# Async Runtime (for timeouts)
tokio = { version = "1", features = ["process", "time", "rt-multi-thread", "macros"] }

# JSON Handling
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Terminal Output
colored = "2.0"
indicatif = "0.17"  # Progress bars

# Interactive Prompts
dialoguer = "0.11"

# Regex for output parsing
regex = "1.10"

# Timestamps
chrono = "0.4"

# Error Handling
eyre = "0.6"
color-eyre = "0.6"
thiserror = "1.0"

# Logging
tracing = "0.1"
tracing-subscriber = "0.3"
```

---

## Architecture Recommendations

### 1. Module Structure

```
src/
├── main.rs                 # Entry point, CLI dispatch
├── cli/
│   ├── mod.rs
│   ├── orchestrator.rs     # Full orchestrator CLI
│   └── planning.rs         # Planning-only CLI
├── orchestrator/
│   ├── mod.rs
│   ├── config.rs           # Configuration constants
│   ├── complexity.rs       # Feature complexity detection
│   ├── features.rs         # feature_list.json handling
│   ├── session.rs          # Session logging
│   └── loop.rs             # Main implementation loop
├── planning/
│   ├── mod.rs
│   ├── pipeline.rs         # PlanningPipeline equivalent
│   ├── steps.rs            # Step implementations
│   ├── checkpoints.rs      # Interactive prompts (revise/restart/exit)
│   └── helpers.rs          # Output parsing with regex
├── runners/
│   ├── mod.rs
│   ├── claude.rs           # Claude CLI wrapper
│   └── beads.rs            # Beads CLI wrapper
├── output/
│   ├── mod.rs
│   ├── colors.rs           # ANSI color helpers
│   └── progress.rs         # Progress bar helpers
└── error.rs                # Error types
```

### 2. Type Definitions

The Python code uses dictionaries extensively. Rust should use strongly-typed structs:

```rust
// features.rs
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Feature {
    pub id: String,
    pub name: String,
    pub description: String,
    #[serde(default)]
    pub priority: i32,
    #[serde(default)]
    pub category: String,
    #[serde(default)]
    pub passes: bool,
    #[serde(default)]
    pub blocked: bool,
    #[serde(default)]
    pub dependencies: Vec<String>,
    #[serde(default)]
    pub complexity: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FeatureList {
    pub features: Vec<Feature>,
}

// pipeline.rs
#[derive(Debug)]
pub struct PipelineResult {
    pub success: bool,
    pub started: chrono::DateTime<chrono::Utc>,
    pub completed: Option<chrono::DateTime<chrono::Utc>>,
    pub steps: HashMap<String, StepResult>,
    pub plan_dir: Option<PathBuf>,
    pub epic_id: Option<String>,
    pub failed_at: Option<String>,
    pub stopped_at: Option<String>,
}

#[derive(Debug)]
pub struct StepResult {
    pub success: bool,
    pub output: String,
    pub error: Option<String>,
    pub elapsed: Duration,
}

// checkpoints.rs - New enum for checkpoint actions
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum ResearchAction {
    Continue,
    Revise,
    Restart,
    Exit,
}
```

### 3. Claude Runner Implementation

Sync version using `std::process::Command`:

```rust
// runners/claude.rs
use std::process::Command;
use std::time::Duration;

pub struct ClaudeRunner {
    timeout: Duration,
}

impl ClaudeRunner {
    pub fn new(timeout: Duration) -> Self {
        Self { timeout }
    }

    pub fn run_sync(&self, prompt: &str) -> Result<ClaudeOutput, ClaudeError> {
        let output = Command::new("claude")
            .args(["--print", "--permission-mode", "bypassPermissions",
                   "--output-format", "text", "-p", prompt])
            .output()?;

        Ok(ClaudeOutput {
            success: output.status.success(),
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        })
    }
}
```

For timeout support (needed for 20-minute research phase), use `tokio::time::timeout`:

```rust
use tokio::process::Command;
use tokio::time::{timeout, Duration};

pub async fn run_with_timeout(
    prompt: &str,
    duration: Duration
) -> Result<ClaudeOutput, ClaudeError> {
    let child = Command::new("claude")
        .args(["--print", "-p", prompt])
        .output();

    match timeout(duration, child).await {
        Ok(Ok(output)) => Ok(ClaudeOutput::from(output)),
        Ok(Err(e)) => Err(ClaudeError::Io(e)),
        Err(_) => Err(ClaudeError::Timeout),
    }
}
```

### 4. CLI with Clap

```rust
// cli/planning.rs
use clap::Parser;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(name = "planning-orchestrator")]
#[command(about = "Planning Pipeline Orchestrator")]
pub struct PlanningArgs {
    /// Project path
    #[arg(short, long, default_value = ".")]
    pub project: PathBuf,

    /// Ticket ID for tracking
    #[arg(short, long)]
    pub ticket: Option<String>,

    /// Skip interactive checkpoints
    #[arg(short = 'y', long)]
    pub auto_approve: bool,

    /// Research prompt (non-interactive)
    #[arg(long)]
    pub prompt_text: Option<String>,
}
```

### 5. Interactive Checkpoints with dialoguer

```rust
// planning/checkpoints.rs
use dialoguer::{Select, Input, Confirm};

pub fn interactive_checkpoint_research(
    research_result: &ResearchResult
) -> Result<CheckpointResult, CheckpointError> {
    println!("\n{}", "=".repeat(60));
    println!("RESEARCH COMPLETE");
    println!("{}", "=".repeat(60));
    println!("\nResearch document: {}", research_result.research_path
        .as_deref().unwrap_or("N/A"));

    // Collect answers to open questions
    let mut answers = Vec::new();
    if !research_result.open_questions.is_empty() {
        println!("\nOpen Questions:");
        for (i, q) in research_result.open_questions.iter().enumerate() {
            println!("  {}. {}", i + 1, q);
        }

        println!("\nProvide answers (empty to stop):");
        loop {
            let answer: String = Input::new()
                .with_prompt(">")
                .allow_empty(true)
                .interact_text()?;
            if answer.is_empty() {
                break;
            }
            answers.push(answer);
        }
    }

    // Prompt for action
    let options = &[
        "Continue to planning",
        "Revise research with additional context",
        "Start over with new prompt",
        "Exit pipeline",
    ];

    let selection = Select::new()
        .with_prompt("What would you like to do?")
        .items(options)
        .default(0)
        .interact()?;

    let action = match selection {
        0 => ResearchAction::Continue,
        1 => ResearchAction::Revise,
        2 => ResearchAction::Restart,
        _ => ResearchAction::Exit,
    };

    let mut revision_context = String::new();
    if action == ResearchAction::Revise {
        println!("\nWhat additional context or refinements would you like?");
        revision_context = collect_multiline_input()?;
    }

    Ok(CheckpointResult {
        action,
        answers,
        revision_context,
        research_path: research_result.research_path.clone(),
    })
}
```

### 6. Regex Helpers

```rust
// planning/helpers.rs
use regex::Regex;

pub fn extract_file_path(output: &str, file_type: &str) -> Option<String> {
    let pattern = format!(r"(thoughts/[^\s]+{}[^\s]*\.md)", regex::escape(file_type));
    let re = Regex::new(&pattern).ok()?;
    re.captures(output)
        .and_then(|caps| caps.get(1))
        .map(|m| m.as_str().to_string())
}

pub fn extract_open_questions(output: &str) -> Vec<String> {
    let mut questions = Vec::new();
    let mut in_questions = false;

    let bullet_re = Regex::new(r"^[-*]\s*(.+)$").unwrap();
    let numbered_re = Regex::new(r"^\d+\.\s*(.+)$").unwrap();

    for line in output.lines() {
        let stripped = line.trim();

        if stripped.to_lowercase().contains("open question") {
            in_questions = true;
            continue;
        }

        if in_questions {
            if stripped.starts_with('#') {
                break;
            }

            for re in [&bullet_re, &numbered_re] {
                if let Some(caps) = re.captures(stripped) {
                    if let Some(q) = caps.get(1) {
                        questions.push(q.as_str().trim().to_string());
                        break;
                    }
                }
            }
        }
    }

    questions
}

pub fn extract_phase_files(output: &str) -> Vec<String> {
    let re = Regex::new(r"(thoughts/[^\s]+/\d{2}-[^\s]+\.md)").unwrap();
    re.find_iter(output)
        .map(|m| m.as_str().to_string())
        .collect()
}
```

---

## Porting Complexity Assessment

| Component | Complexity | Notes |
|-----------|------------|-------|
| Argument parsing | Low | Direct clap mapping |
| JSON read/write | Low | serde_json is ergonomic |
| Subprocess execution | Medium | Need timeout handling (tokio) |
| Interactive prompts | Medium | dialoguer/inquire crates |
| Color output | Low | colored crate is simple |
| Feature complexity heuristics | Low | Direct port of string matching |
| Prompt templates | Low | format! macros |
| Session logging | Low | serde + file I/O |
| Main orchestration loop | Medium | State machine, error handling |
| TTY detection | Low | atty crate |
| Regex parsing | Low | regex crate is powerful |

**Estimated Effort**: 3-5 days for a clean port with tests

---

## Key Differences: Python vs Rust

### 1. Error Handling

Python uses dict returns with `{"success": bool, "error": str}`. Rust should use `Result<T, E>`:

```rust
// Instead of: {"success": False, "error": "..."}
// Use: Err(PipelineError::ResearchFailed(reason))

#[derive(Debug, thiserror::Error)]
pub enum PipelineError {
    #[error("Research failed: {0}")]
    ResearchFailed(String),
    #[error("Planning failed: {0}")]
    PlanningFailed(String),
    #[error("Claude timed out after {0:?}")]
    ClaudeTimeout(Duration),
    #[error("Claude CLI not found")]
    ClaudeNotFound,
    #[error("Beads CLI not found")]
    BeadsNotFound,
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}
```

### 2. Dynamic vs Static Typing

Python dict access like `result.get("steps", {}).get("research", {})` needs explicit types:

```rust
// Define all structures explicitly
let research = result.steps.get("research")
    .ok_or(PipelineError::MissingStep("research"))?;
```

### 3. Ownership and Borrowing

Python freely shares references. Rust requires explicit ownership:

```rust
// Clone when needed, or use references with lifetimes
pub fn run_pipeline(
    &self,
    research_prompt: &str,  // borrowed
    ticket_id: Option<&str>,
) -> Result<PipelineResult, PipelineError> {
    // ...
}
```

### 4. Async Considerations

The Python code is synchronous but needs timeouts. Options:

**Option A: Block on async runtime**
```rust
fn main() {
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        run_pipeline().await
    });
}
```

**Option B: Use std::process with timeout thread**
```rust
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;

fn run_with_timeout(cmd: &mut Command, timeout: Duration) -> Result<Output, Error> {
    let child = cmd.spawn()?;
    let handle = thread::spawn(move || child.wait_with_output());

    // Join with timeout
    match handle.join() {
        Ok(result) => result.map_err(Into::into),
        Err(_) => Err(Error::Timeout),
    }
}
```

---

## Rust Crate Quick Reference

### Subprocess Execution
- **subprocess** crate: Python-like API, `wait_timeout()` built-in
- **std::process::Command**: Zero dependencies, basic timeout via threads
- **tokio::process**: Async, native timeout via `tokio::time::timeout`

### CLI Arguments
- **clap** (v4.5): Derive macro, auto-help, subcommands, shell completions

### JSON
- **serde + serde_json**: Type-safe, derive macros, custom serialization

### Terminal Colors
- **colored**: Simple `.red()`, `.bold()` method chaining
- **termcolor**: Cross-platform (Windows console API)

### Interactive Prompts
- **dialoguer**: Select, Input, Confirm, MultiSelect
- **inquire**: Similar API, different styling

### Error Handling
- **eyre + color-eyre**: User-facing error reporting
- **thiserror**: Define custom error types
- **anyhow**: Simple error chaining

### Progress UI
- **indicatif**: Progress bars, spinners

---

## Open Questions

1. **Async vs Sync**: Should the Rust port use async (tokio) throughout, or only for subprocess timeouts? The Python code is fully synchronous except for the 20-minute research timeout.

2. **Single Binary vs Multiple**: Should there be one binary with subcommands (`silmari orchestrate`, `silmari plan`), or separate binaries?

3. **Backwards Compatibility**: Should the Rust CLI maintain identical argument names and JSON formats for drop-in replacement?

4. **Feature Parity**: Which orchestrator.py features are actually used? The QA/Playwright features (lines 561-785) might be dead code.

5. **MCP Setup**: The interactive MCP setup (lines 175-292) spawns shells - is this needed in Rust, or should MCP setup be a separate concern?

6. **Beads Integration**: Is the `bd` CLI stable enough to depend on, or should Rust interact with beads directly via its library?

7. **Configuration**: Should configuration move from constants to a config file (TOML preferred in Rust ecosystem)?

8. **Testing Strategy**: The Python tests use monkeypatching - Rust should use trait-based dependency injection for testability. How to structure test traits?
