---
date: 2026-01-01T08:27:35-05:00
researcher: maceo
git_commit: 66ba4d0695d8b15d575488ce5faf57113ad08346
branch: main
repository: silmari-Context-Engine
topic: "BAML Integration Research for Context Engine"
tags: [research, baml, llm-integration, python, type-safety]
status: complete
last_updated: 2026-01-01
last_updated_by: maceo
last_updated_note: "Added detailed code examples from python-fastapi-starter and installation instructions"
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                     BAML INTEGRATION RESEARCH                               │
│                     Silmari Context Engine                                  │
│                                                                             │
│                     Status: COMPLETE | 2026-01-01                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: BAML Integration for Context Engine

**Date**: 2026-01-01T08:27:35-05:00
**Researcher**: maceo
**Git Commit**: 66ba4d0695d8b15d575488ce5faf57113ad08346
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

Research how we can add BAML to this project, using the [python-fastapi-starter](https://github.com/BoundaryML/baml-examples/tree/main/python-fastapi-starter) as a reference implementation.

---

## 📊 Summary

BAML (Boundary AI Markup Language) is a domain-specific language for defining type-safe LLM prompts with automatic client code generation. The key findings:

| Aspect | Current State | BAML Approach |
|--------|---------------|---------------|
| **LLM Execution** | Claude CLI subprocess | Direct API calls |
| **Output Parsing** | Regex extraction | Type-safe schema |
| **Type Safety** | `dict[str, Any]` | Pydantic models |
| **Dependencies** | Standard library only | `baml-py` package |

BAML represents a **different execution paradigm** from the current project architecture. Integration requires understanding both the benefits and the architectural changes needed.

---

## 🎯 Detailed Findings

### 1. BAML Architecture Overview

BAML operates on a fundamentally different model from the current Context Engine:

```
╔═════════════════════════════════════════════════════════════════════════╗
║                        BAML WORKFLOW                                     ║
╠═════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   baml_src/*.baml  ──→  baml-cli generate  ──→  baml_client/           ║
║   (DSL definitions)      (Rust compiler)        (Type-safe Python)      ║
║                                                                          ║
║         │                                            │                   ║
║         ▼                                            ▼                   ║
║   Define prompts +          →            Import & call in Python         ║
║   input/output schemas                   with full type checking         ║
║                                                                          ║
╚═════════════════════════════════════════════════════════════════════════╝
```

#### BAML Project Structure (from python-fastapi-starter)

```
python-fastapi-starter/
├── baml_src/                    # BAML source definitions
│   ├── main.baml               # Generator config
│   ├── clients.baml            # LLM client definitions
│   ├── extract_resume.baml     # Function + schema example
│   ├── classify_message.baml   # Classification function
│   ├── analyze_books.baml      # Analysis function
│   ├── describe_image.baml     # Vision capabilities
│   └── rag.baml                # RAG pattern
├── baml_client/                 # Generated Python code
│   └── (auto-generated)
├── fast_api_starter/
│   └── app.py                  # FastAPI integration
├── pyproject.toml              # Python dependencies
└── tests/
```

---

### 2. BAML Core Concepts

#### 2.1 Generator Configuration (`main.baml`)

```baml
generator lang_python {
  output_type "python/pydantic"
  output_dir "../"
  version "0.207.1"
  default_client_mode "sync"
}

class DynamicOutput {
  @@dynamic
}
```

**Key settings:**
- `output_type`: Generates Pydantic models for type safety
- `default_client_mode`: `"sync"` for synchronous operations

#### 2.2 Client Definitions (`clients.baml`)

```baml
client<llm> GPT4o {
  provider openai
  options {
    model "gpt-4o"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> GPT4Turbo {
  provider openai
  options {
    model "gpt-4-turbo"
    api_key env.OPENAI_API_KEY
  }
}
```

**Providers documented:**
- `openai` - OpenAI API
- `baml-openai-chat` - Alternative OpenAI format
- `anthropic` - Anthropic Claude API (supported but not in starter)

#### 2.3 Function Definitions (`extract_resume.baml`)

```baml
class Education {
  school string
  degree string
  year int
}

class Resume {
  name string
  education Education[]
  skills string[]
}

function ExtractResume(raw_text: string) -> Resume {
  client GPT4o
  prompt #"
    Parse the following resume and extract structured information.

    Resume text:
    {{raw_text}}

    Extract the name, education history, and skills.
  "#
}

test sarah {
  functions [ExtractResume]
  args {
    raw_text "Sarah Johnson, graduated from MIT with a BS in Computer Science..."
  }
}
```

**Function anatomy:**
- **Input types**: Primitive types (`string`, `int`, etc.)
- **Output types**: Custom classes with typed fields
- **Client binding**: Each function specifies which LLM to use
- **Prompt template**: Uses `{{variable}}` syntax for interpolation
- **Tests**: Inline test cases for development

---

### 3. FastAPI Integration Pattern

From `fast_api_starter/app.py`:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from baml_client import b  # Generated client
from dotenv import load_dotenv
import asyncio

load_dotenv()
app = FastAPI()

@app.get("/")
async def extract_resume():
    resume_text = """
    John Doe
    Education: BS Computer Science, MIT 2020
    Skills: Python, TypeScript, Machine Learning
    """

    async def stream_response():
        stream = b.stream.ExtractResume(raw_text=resume_text)
        async for chunk in stream:
            yield chunk.model_dump_json() + "\n"
            await asyncio.sleep(0)

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream"
    )
```

**Integration patterns:**
- Import generated client: `from baml_client import b`
- Call functions: `b.ExtractResume(...)` (sync) or `b.stream.ExtractResume(...)` (streaming)
- Type-safe returns: Function returns the defined class (`Resume`)

---

### 4. Dependencies (`pyproject.toml`)

```toml
[project]
name = "fastapi-starter"
version = "0.1.0"
requires-python = "~=3.11"

dependencies = [
    "fastapi>=0.115.0,<0.116",
    "uvicorn[standard]>=0.31.0,<0.32",
    "baml-py==0.80.2",
    "python-dotenv>=1.0.1,<2",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Key dependency:** `baml-py` - the Python runtime for BAML

---

### 5. Current Context Engine Architecture

#### 5.1 Execution Model

The Context Engine uses a **subprocess-based execution model**:

| Component | Location | Purpose |
|-----------|----------|---------|
| `claude_runner.py` | `planning_pipeline/claude_runner.py:9` | Claude CLI subprocess wrapper |
| `beads_controller.py` | `planning_pipeline/beads_controller.py:9` | Beads CLI wrapper |
| `steps.py` | `planning_pipeline/steps.py:12` | Pipeline step implementations |
| `helpers.py` | `planning_pipeline/helpers.py:7` | Regex-based output parsing |

```python
# Current pattern: claude_runner.py:30-36
cmd = [
    "claude",
    "--print",
    "--permission-mode", "bypassPermissions",
    "--output-format", "text",
    "-p", prompt
]
result = subprocess.run(cmd, ...)
```

#### 5.2 Output Parsing

Current regex-based extraction (`helpers.py:7-21`):

```python
def extract_file_path(output: str, file_type: str) -> Optional[str]:
    pattern = rf'(thoughts/[^\s]+{re.escape(file_type)}[^\s]*\.md)'
    match = re.search(pattern, output, re.IGNORECASE)
    return match.group(1) if match else None
```

**Limitations:**
- Fragile regex patterns
- No type validation
- Manual extraction logic
- No IDE support for output structure

#### 5.3 Return Types

Current pattern uses untyped dictionaries (`steps.py:85-90`):

```python
return {
    "success": True,
    "research_path": research_path,
    "output": result["output"],
    "open_questions": open_questions
}
```

---

## 🔄 Integration Considerations

### Architectural Differences

<table>
<tr>
<th width="50%">Current Architecture</th>
<th width="50%">BAML Architecture</th>
</tr>
<tr>
<td>

```
Python Script
    │
    ▼
subprocess.run(["claude", ...])
    │
    ▼
Claude CLI
    │
    ▼
Parse text output (regex)
    │
    ▼
dict[str, Any]
```

</td>
<td>

```
Python Script
    │
    ▼
from baml_client import b
    │
    ▼
b.FunctionName(input)
    │
    ▼
Direct API call (HTTP)
    │
    ▼
Typed Pydantic model
```

</td>
</tr>
</table>

### Key Differences

| Aspect | Current | BAML |
|--------|---------|------|
| **Execution** | Claude CLI subprocess | Direct API calls |
| **Permissions** | `--permission-mode bypassPermissions` | API key only |
| **Tool Usage** | Claude selects/uses tools | No tool access |
| **Context Window** | Full CLI features | API-only features |
| **Output Format** | Unstructured text | Typed schema |
| **Type Safety** | None | Full Pydantic |
| **Dependencies** | Standard library | baml-py package |

---

### Potential Integration Approaches

#### Approach A: Hybrid Architecture

Use BAML for **structured output parsing** while keeping Claude CLI for execution:

```
╔════════════════════════════════════════════════════════════════════╗
║                    HYBRID APPROACH                                  ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║   Claude CLI  ──→  Text Output  ──→  BAML Parser  ──→  Typed Data ║
║   (execution)      (unstructured)     (extraction)     (Pydantic)  ║
║                                                                     ║
╚════════════════════════════════════════════════════════════════════╝
```

**Pros:**
- Keeps Claude CLI tool access
- Adds type safety to outputs
- Incremental adoption

**Cons:**
- Two LLM paradigms in one project
- BAML extraction requires separate API call

#### Approach B: Full BAML Migration

Replace Claude CLI with direct API calls via BAML:

```
╔════════════════════════════════════════════════════════════════════╗
║                    FULL MIGRATION                                   ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║   BAML Functions  ──→  Claude API  ──→  Typed Pydantic Models      ║
║   (definitions)        (direct)         (automatic)                 ║
║                                                                     ║
╚════════════════════════════════════════════════════════════════════╝
```

**Pros:**
- Full type safety
- Single execution model
- Better testing with BAML playground

**Cons:**
- Loses Claude CLI tool access (Read, Write, Bash, etc.)
- Major architectural change
- Different capability set

#### Approach C: Separate Use Cases

Use Claude CLI for **agentic tasks** (file operations, research) and BAML for **structured extraction**:

```
╔════════════════════════════════════════════════════════════════════╗
║                    SEPARATION OF CONCERNS                           ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║   Agentic Tasks              │  Structured Extraction              ║
║   ─────────────              │  ────────────────────               ║
║   Claude CLI subprocess      │  BAML direct API                    ║
║   • Research codebase        │  • Parse research output            ║
║   • Create files             │  • Extract phases from plan         ║
║   • Run commands             │  • Classify content                 ║
║                                                                     ║
╚════════════════════════════════════════════════════════════════════╝
```

**Pros:**
- Best of both worlds
- Clear separation of concerns
- Gradual adoption

**Cons:**
- Two API keys needed
- Increased complexity
- Additional costs

---

## 📁 Code References

### Current Project Files

| File | Purpose |
|------|---------|
| `planning_pipeline/claude_runner.py:9` | Subprocess execution wrapper |
| `planning_pipeline/helpers.py:7` | `extract_file_path()` regex parser |
| `planning_pipeline/helpers.py:24` | `extract_open_questions()` regex parser |
| `planning_pipeline/helpers.py:58` | `extract_phase_files()` regex parser |
| `planning_pipeline/steps.py:12` | `step_research()` pipeline step |
| `planning_pipeline/steps.py:93` | `step_planning()` pipeline step |
| `planning_pipeline/steps.py:188` | `step_phase_decomposition()` step |

### BAML Example Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependency configuration |
| `baml_src/main.baml` | Generator configuration |
| `baml_src/clients.baml` | LLM client definitions |
| `baml_src/extract_resume.baml` | Function + schema example |
| `fast_api_starter/app.py` | FastAPI integration |

---

## 📖 Historical Context (from thoughts/)

No prior BAML research exists in the thoughts/ directory. Related documents:

| Document | Relevance |
|----------|-----------|
| `thoughts/shared/research/2025-12-31-python-deterministic-pipeline-control.md` | Claude Agent SDK integration research |
| `thoughts/shared/research/2025-12-31-context-engine-codebase.md` | Current architecture documentation |
| `thoughts/shared/plans/2025-12-31-tdd-python-deterministic-pipeline.md` | Pipeline implementation plan |

---

## 🔗 Related Resources

### Official Documentation
- [BAML Documentation](https://docs.boundaryml.com/home)
- [BAML GitHub Repository](https://github.com/BoundaryML/baml)
- [BAML Examples](https://github.com/BoundaryML/baml-examples)
- [Python FastAPI Starter](https://github.com/BoundaryML/baml-examples/tree/main/python-fastapi-starter)

### Setup Requirements
- **Python**: 3.11+ recommended
- **Package**: `baml-py` (version 0.80.2 in starter)
- **CLI**: `baml-cli` for code generation
- **Environment**: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- **IDE**: VSCode extension recommended

---

## ❓ Open Questions

1. **Tool Access**: Does the project need Claude CLI's tool access (Read, Write, Bash, etc.)? BAML doesn't provide this.

2. **API vs CLI**: Is direct API access acceptable, or is the CLI subprocess model required for the workflow?

3. **Anthropic Support**: BAML supports Anthropic, but the starter example uses OpenAI. Need to verify Anthropic client configuration.

4. **Streaming**: Current project streams Claude output to terminal. BAML streaming works differently (async iterators).

5. **Testing**: How would BAML's built-in testing integrate with the existing pytest suite in `planning_pipeline/tests/`?

6. **Incremental Adoption**: Should BAML replace regex parsing first, or should there be a full architectural migration?

---

## 📋 Setup Steps (if proceeding)

```bash
# 1. Create pyproject.toml with baml-py dependency
# 2. Initialize BAML
baml-cli init

# 3. Create baml_src/ directory structure
mkdir -p baml_src

# 4. Define clients (clients.baml) with Anthropic configuration
# 5. Define functions and schemas
# 6. Generate client code
baml-cli generate

# 7. Import and use in Python
from baml_client import b
result = b.FunctionName(input)
```

---

## Follow-up Research 2026-01-01T08:45:00-05:00

### Additional Details from python-fastapi-starter

#### Message Classification Pattern (classify_message.baml)

```baml
enum Category {
  Refund
  CancelOrder
  TechnicalSupport
  AccountIssue
  Question
}

enum Role {
  Customer
  Assistant
}

class Message {
  role Role
  content string
}

function ClassifyMessage(messages: Message[]) -> Category[] {
  client GPT4
  prompt #"
    Classify the following conversation into categories.

    {% for message in messages %}
    {{ message.role }}: {{ message.content }}
    {% endfor %}

    Return the matching categories in JSON format:
    {{ ctx.output_format }}
  "#
}
```

**Key patterns:**
- Jinja2-style templating with `{% for %}` and `{{ }}`
- `ctx.output_format` auto-injects the expected JSON schema
- Enums define valid classification values

#### Streaming Pattern (app.py)

```python
from baml_client import b
from fastapi.responses import StreamingResponse
import asyncio

@app.get("/")
async def extract_resume():
    resume = "Sarah Chen, MIT CS 2020..."

    async def stream_resume():
        stream = b.stream.ExtractResume(resume)
        async for chunk in stream:
            yield chunk.model_dump_json()
            await asyncio.sleep(0)  # Prevent blocking

    return StreamingResponse(stream_resume(), media_type="text/event-stream")
```

### Complete Installation Steps

```bash
# 1. Install BAML Python package
pip install baml-py
# or with uv: uv add baml-py
# or with poetry: poetry add baml-py

# 2. Initialize BAML project (creates baml_src/ directory)
baml-cli init
# or with uv: uv run baml-cli init

# 3. Configure environment variables
echo 'OPENAI_API_KEY=sk-...' >> .env
echo 'ANTHROPIC_API_KEY=sk-ant-...' >> .env

# 4. Generate Python client from BAML definitions
baml-cli generate
# or with uv: uv run baml-cli generate

# 5. Import and use in Python
# from baml_client import b
# result = b.FunctionName(input)
```

### VSCode Configuration

Add to `settings.json` for better autocomplete:
```json
{
  "python.analysis.typeCheckingMode": "basic"
}
```

Install the BAML extension from the VSCode marketplace for:
- Syntax highlighting
- Real-time prompt preview
- Interactive testing (< 5 seconds)
- Auto-generate on save

### Anthropic Client Configuration

While the starter example uses OpenAI, BAML supports Anthropic:

```baml
client<llm> Claude3Opus {
  provider anthropic
  options {
    model "claude-3-opus-20240229"
    api_key env.ANTHROPIC_API_KEY
  }
}

client<llm> Claude3Sonnet {
  provider anthropic
  options {
    model "claude-3-5-sonnet-20241022"
    api_key env.ANTHROPIC_API_KEY
  }
}
```

### Project-Specific Structured Output Examples

Potential BAML functions for Context Engine:

```baml
class ResearchOutput {
  research_path string @description("Path to created research document")
  open_questions string[] @description("Unanswered questions discovered")
  summary string @description("Brief summary of findings")
}

class PlanOutput {
  plan_path string @description("Path to created plan document")
  phases Phase[] @description("List of implementation phases")
  estimated_complexity string @description("low, medium, or high")
}

class Phase {
  number int
  name string
  dependencies string[]
  success_criteria string[]
}

function ParseResearchOutput(raw_output: string) -> ResearchOutput {
  client Claude3Sonnet
  prompt #"
    Parse the following research output and extract structured information.

    Raw output:
    {{ raw_output }}

    {{ ctx.output_format }}
  "#
}
```

This would replace the regex-based extraction in `helpers.py`.

---

*Research conducted: 2026-01-01*
*Researcher: maceo*
*Status: Complete*
