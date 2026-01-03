---
date: 2026-01-01T09:19:03-05:00
researcher: maceo
git_commit: 8601c76bcfb334f2188194a771c215a0d3eb4312
branch: main
repository: silmari-Context-Engine
topic: "BAML Integration Research"
tags: [research, baml, llm-integration, structured-outputs, type-safety]
status: complete
last_updated: 2026-01-01
last_updated_by: maceo
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BAML INTEGRATION RESEARCH                              │
│                   Silmari Context Engine Project                            │
│                          2026-01-01                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Adding BAML to the Context Engine

**Date**: 2026-01-01T09:19:03-05:00
**Researcher**: maceo
**Git Commit**: `8601c76bcfb334f2188194a771c215a0d3eb4312`
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

How can we add BAML to this project? Based on the python-fastapi-starter example, what patterns should we follow?

### Open Questions to Address:
1. BAML doesn't provide Claude's tool access (Read, Write, Bash) - is that needed?
2. Should BAML replace the regex parsing in `helpers.py` first as a pilot?

---

## 📊 Summary

BAML (Boundary Markup Language) is a declarative framework for type-safe LLM interactions. It provides structured output extraction with Pydantic model generation, testing infrastructure, and multi-provider support.

**Key Finding**: BAML is designed for **direct LLM API calls** with structured outputs, while the Context Engine currently uses **Claude Code CLI** via subprocess. These are fundamentally different integration patterns:

| Aspect | Current System | BAML Approach |
|--------|---------------|---------------|
| LLM Access | Claude Code CLI (subprocess) | Direct API calls |
| Output Parsing | Regex patterns | Schema-validated types |
| Tool Access | Full (Read, Write, Bash) | None (pure LLM) |
| Use Case | Agentic workflows | Structured extraction |

---

## 🎯 Detailed Findings

### 1. Current Architecture: Claude Code CLI Integration

The Context Engine uses Claude Code CLI via subprocess for all LLM interactions:

**Primary Integration Point**: `planning_pipeline/claude_runner.py:30-36`
```python
cmd = [
    "claude",
    "--print",
    "--permission-mode", "bypassPermissions",
    "--output-format", "text",
    "-p", prompt
]
```

**Key Characteristics**:
- Subprocess-based execution with timeout management
- Full tool access (Read, Write, Bash) through Claude Code
- Markdown-formatted free-text outputs
- No direct API calls to OpenAI/Anthropic

**Why This Matters**: The Context Engine is an **agentic system** that relies on Claude Code's tool-using capabilities to:
- Research codebases (Glob, Grep, Read tools)
- Create files (Write tool)
- Execute commands (Bash tool)
- Manage tasks (TodoWrite, beads)

BAML cannot replace this - it's designed for structured extraction, not agentic workflows.

### 2. Current Output Parsing: `helpers.py`

**File**: `planning_pipeline/helpers.py`

Three regex-based extraction functions:

| Function | Purpose | Regex Pattern |
|----------|---------|---------------|
| `extract_file_path()` | Extract markdown file paths | `(thoughts/[^\s]+{file_type}[^\s]*\.md)` |
| `extract_open_questions()` | Parse bullet/numbered lists | `^[-*]\s*(.+)$` and `^\d+\.\s*(.+)$` |
| `extract_phase_files()` | Find numbered phase files | `(thoughts/[^\s]+/\d{2}-[^\s]+\.md)` |

**Observations**:
- Simple, targeted patterns
- Work on free-text Claude output
- No schema validation
- No type generation

### 3. BAML Architecture from Example Project

**Source**: `python-fastapi-starter` repository

**Directory Structure**:
```
baml_src/           # BAML source definitions
├── clients.baml    # LLM provider configuration
├── extract_resume.baml
├── classify_message.baml
└── ...
baml_client/        # Auto-generated Python code
fast_api_starter/   # Application code
```

**Client Configuration** (`clients.baml`):
```baml
client<llm> GPT4 {
  provider openai
  options {
    model gpt-4
    api_key env.OPENAI_API_KEY
  }
}
```

**Type Definition** (`extract_resume.baml`):
```baml
class Resume {
  name string
  education Education[]
  skills string[]
}

function ExtractResume(raw_text: string) -> Resume {
  client GPT4o
  prompt #"
    Parse the following resume and return a structured
    representation of the data in the schema below.
    {{ ctx.output_format }}
    {{ raw_text }}
  "#
}
```

**Usage in FastAPI** (`app.py`):
```python
from baml_client import b

@app.get("/")
async def extract_resume():
    result = b.stream.ExtractResume(resume_text)
    return StreamingResponse(stream_resume())
```

**Key BAML Benefits**:
- Type-safe outputs (Pydantic models generated)
- Schema validation at extraction time
- Built-in testing framework
- Multi-provider support (20+ LLMs)
- Streaming support

### 4. Compatibility Analysis

#### What BAML Can Do
- Define structured output schemas as types
- Generate validated Pydantic models
- Test extraction functions with sample data
- Support multiple LLM providers
- Stream responses with type safety

#### What BAML Cannot Do
- Execute tools (Read, Write, Bash)
- Maintain conversation state across tool calls
- Perform agentic multi-step workflows
- Replace Claude Code CLI functionality

---

## 🔄 Integration Options

### Option A: Hybrid Architecture (Recommended)

Use BAML for **structured extraction** tasks while keeping Claude Code CLI for **agentic workflows**.

```
┌──────────────────────────────────────────────────────────────────┐
│                    HYBRID ARCHITECTURE                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐        ┌─────────────────────────────┐ │
│  │   Agentic Tasks     │        │   Extraction Tasks          │ │
│  │   (Claude Code)     │        │   (BAML)                    │ │
│  ├─────────────────────┤        ├─────────────────────────────┤ │
│  │ • Research codebase │        │ • Parse structured output   │ │
│  │ • Create files      │        │ • Extract metadata          │ │
│  │ • Run commands      │        │ • Classify content          │ │
│  │ • Multi-step plans  │        │ • Validate responses        │ │
│  └─────────────────────┘        └─────────────────────────────┘ │
│           │                              │                       │
│           └──────────┬───────────────────┘                       │
│                      ▼                                           │
│              ┌───────────────┐                                   │
│              │ Application   │                                   │
│              └───────────────┘                                   │
└──────────────────────────────────────────────────────────────────┘
```

**Use Cases for BAML in This Codebase**:

| Current Function | BAML Benefit | Migration Complexity |
|-----------------|--------------|---------------------|
| `extract_file_path()` | Type-safe path extraction | Low |
| `extract_open_questions()` | Validated list structure | Medium |
| `extract_phase_files()` | Schema-validated paths | Low |
| Future: Parse structured plans | Strong typing, validation | High value |

### Option B: Full BAML Migration (Not Recommended)

Would require replacing Claude Code CLI with direct API calls, losing all tool access. This would fundamentally change the architecture from an **agentic system** to a **structured extraction system**.

### Option C: BAML for Post-Processing Only

Use BAML to post-process Claude Code CLI output for better type safety.

```python
# Current: regex extraction
path = extract_file_path(claude_output, "research")

# With BAML post-processing
from baml_client import b
result = b.ExtractResearchOutput(claude_output)
path = result.file_path  # Type-safe, validated
```

---

## ✅ Answer to Open Questions

### Q1: BAML doesn't provide Claude's tool access - is that needed?

**Answer: Yes, tool access is essential for this codebase.**

The Context Engine is fundamentally an **agentic system** that requires:
- **Read tool**: Codebase exploration, reading files
- **Write tool**: Creating research documents, plans, phase files
- **Bash tool**: Running tests, git operations, beads commands
- **Glob/Grep**: Searching codebases

These capabilities cannot be replaced by BAML. BAML is designed for **structured extraction**, not **agentic workflows**.

**Recommendation**: Keep Claude Code CLI for agentic tasks, use BAML for structured output parsing where it adds value.

### Q2: Should BAML replace the regex parsing in `helpers.py` first as a pilot?

**Answer: Maybe - but with caveats.**

**Arguments For**:
- Type safety for extracted values
- Schema validation catches malformed outputs
- Testing infrastructure for extraction functions
- Self-documenting output structure

**Arguments Against**:
- Current regex patterns are simple and working
- Adding BAML introduces a new dependency and build step
- Requires `baml-cli generate` in development workflow
- May be over-engineering for 3 simple extraction functions

**Recommendation**: A good pilot would be adding **new** structured extraction, not replacing working code. Consider:

```baml
// Example: New structured output for research results
class ResearchResult {
  file_path string @description("Path to the research document")
  open_questions string[] @description("Questions needing follow-up")
  key_findings string[] @description("Main discoveries")
  code_references CodeRef[] @description("File:line references")
}

class CodeRef {
  file string
  line int
  description string
}

function ExtractResearchResult(output: string) -> ResearchResult {
  client Claude  // Would need Anthropic client config
  prompt #"
    Extract structured research results from this output:
    {{ output }}

    {{ ctx.output_format }}
  "#
}
```

---

## 📁 Code References

| File | Line | Description |
|------|------|-------------|
| `planning_pipeline/claude_runner.py` | 30-36 | Claude CLI command construction |
| `planning_pipeline/helpers.py` | 7-21 | `extract_file_path()` function |
| `planning_pipeline/helpers.py` | 24-55 | `extract_open_questions()` function |
| `planning_pipeline/helpers.py` | 58-68 | `extract_phase_files()` function |
| `planning_pipeline/steps.py` | 74-77 | Claude invocation with timeout |
| `planning_pipeline/pipeline.py` | 12-21 | `PlanningPipeline` class |

---

## 🏗️ Implementation Roadmap (If Proceeding)

### Phase 1: Setup & Configuration
1. Add `baml-py` to project dependencies
2. Run `baml-cli init` to create `baml_src/` directory
3. Configure Anthropic client in `baml_src/clients.baml`
4. Set up `ANTHROPIC_API_KEY` environment variable

### Phase 2: Define Types
1. Create `baml_src/extraction.baml` with output types
2. Define `ResearchOutput`, `PlanOutput`, `PhaseFile` classes
3. Add extraction functions with prompts

### Phase 3: Generate Client
1. Run `baml-cli generate` to create `baml_client/`
2. Add to `.gitignore` or commit generated code
3. Update development workflow documentation

### Phase 4: Integrate
1. Create new module `planning_pipeline/baml_extraction.py`
2. Import and use generated client
3. Keep existing `helpers.py` for backward compatibility
4. Add feature flag to switch between implementations

### Phase 5: Testing
1. Write BAML test cases in `.baml` files
2. Add pytest integration tests
3. Validate against real Claude Code outputs

---

## ⚠️ Considerations

### Dependencies
```toml
# Would need to add to pyproject.toml (if created)
[dependencies]
baml-py = ">=0.80.0"
```

### Build Step
```bash
# Development workflow addition
baml-cli generate  # Run after changing .baml files
```

### Environment
```bash
# Required for BAML direct API calls
export ANTHROPIC_API_KEY="sk-..."  # If using Anthropic
export OPENAI_API_KEY="sk-..."     # If using OpenAI
```

---

## 📖 Sources

- [BAML Documentation](https://docs.boundaryml.com)
- [BAML GitHub](https://github.com/BoundaryML/baml)
- [Python FastAPI Starter](https://github.com/BoundaryML/baml-examples/tree/main/python-fastapi-starter)
- [BAML Python Installation](https://docs.boundaryml.com/guide/installation-language/python)

---

## 🔗 Related Research

- `thoughts/shared/research/2025-12-31-codebase-architecture.md` - Architecture overview
- `thoughts/shared/research/2025-12-31-python-deterministic-pipeline-control.md` - Pipeline design

---

## ❓ Open Questions

1. **API Key Management**: How should ANTHROPIC_API_KEY be managed alongside Claude Code CLI usage?
2. **Build Pipeline**: Should `baml-cli generate` be a pre-commit hook or manual step?
3. **Feature Flag**: How to toggle between regex and BAML extraction?
4. **Testing**: How to test BAML functions without making actual API calls?
