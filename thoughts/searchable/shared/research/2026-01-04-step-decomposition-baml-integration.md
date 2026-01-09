---
date: 2026-01-04T13:18:20-05:00
researcher: Claude
git_commit: d38b4444f903ee130a853b8cf1adf9af4fcc5660
branch: main
repository: silmari-Context-Engine
topic: "step_decomposition.py BAML Integration and Requirements Hierarchy Structure"
tags: [research, codebase, step-decomposition, baml, requirements-hierarchy, gate1]
status: complete
last_updated: 2026-01-04
last_updated_by: Claude
related_beads: ["silmari-Context-Engine-4hi"]
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  RESEARCH: Step Decomposition BAML Integration & Requirements Hierarchy     │
│  Status: Complete | Date: 2026-01-04                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: step_decomposition.py BAML Integration and Requirements Hierarchy Structure

**Date**: 2026-01-04T13:18:20-05:00
**Researcher**: Claude
**Git Commit**: d38b4444f903ee130a853b8cf1adf9af4fcc5660
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📋 Research Question

The user asked to document:
1. How `step_decomposition.py` works and its current output structure
2. The expected requirements hierarchy format (from `test-002-alpha.02.json`)
3. The BAML functions that should be used: `ProcessGate1InitialExtractionPrompt` and `ProcessGate1SubprocessDetailsPrompt`
4. The pattern from `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/requirements_processor.py`: `add_requirement()` (line 146) and `add_child()` (line 173)

---

## 📊 Summary

The research documents three key components that form the requirement decomposition system:

| Component | Location | Purpose |
|-----------|----------|---------|
| `step_decomposition.py` | `planning_pipeline/step_decomposition.py` | Pipeline step orchestrator |
| `decomposition.py` | `planning_pipeline/decomposition.py` | BAML-based decomposition engine |
| `requirements_processor.py` | CodeWriter5 `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/requirements_processor.py` | Reference implementation pattern |

The current implementation produces a 2-level hierarchy (parent → sub_process), while the expected output format (`test-002-alpha.02.json`) shows a 3-level hierarchy (parent → sub_process → implementation) with richer fields including `function_id` and `implementation` components.

---

## 🔍 Detailed Findings

### 1. Current step_decomposition.py Implementation

**File**: `planning_pipeline/step_decomposition.py`

The `step_requirement_decomposition()` function (lines 41-213) orchestrates the decomposition pipeline:

```
Pipeline Position: step_research() → [step_requirement_decomposition()] → step_planning()
```

#### Current Flow

```
┌──────────────────────┐
│  Read Research Doc   │  (lines 117-124)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ decompose_requirements() │  (line 128)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Generate Mermaid    │  (line 167)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Generate Tests      │  (lines 177-199)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Write JSON Output   │  (lines 156-164)
└──────────────────────┘
```

#### Key Points

- **Input**: Research document path (relative to project)
- **Output Directory**: `{project}/thoughts/searchable/shared/plans/{date}-requirements/`
- **Output Files**:
  - `requirements_hierarchy.json` - Full hierarchy with metadata
  - `requirements_diagram.mmd` - Mermaid flowchart
  - `property_tests_skeleton.py` - Hypothesis test stubs (if acceptance criteria exist)

---

### 2. decompose_requirements() Implementation

**File**: `planning_pipeline/decomposition.py:133-291`

The core decomposition function uses two BAML calls:

#### Step 1: Initial Extraction (lines 186-200)

```python
initial_response = b.ProcessGate1InitialExtractionPrompt(
    scope_text=research_content,
    analysis_framework=DEFAULT_ANALYSIS_FRAMEWORK,
    user_confirmation=True
)
```

**Client**: `HaikuWithOllamaFallback` (tries Claude Haiku, falls back to local Ollama)

**Returns** `InitialExtractionResponse`:
```baml
class InitialExtractionResponse {
  requirements Requirement[]
  metadata ResponseMetadata
}
```

Where `Requirement`:
```baml
class Requirement {
  description string
  sub_processes string[]
  related_concepts string[]
}
```

#### Step 2: Subprocess Expansion (lines 234-265)

For each `sub_process` in each requirement:

```python
details_response = b.ProcessGate1SubprocessDetailsPrompt(
    sub_process=sub_process,
    parent_description=requirement.description,
    scope_text=research_content,
    user_confirmation=True
)
```

**Client**: `EnvironmentOllama` (local Ollama only)

**Returns** `SubprocessDetailsResponse`:
```baml
class SubprocessDetailsResponse {
  implementation_details ImplementationDetail[]
  metadata ResponseMetadata
}
```

Where `ImplementationDetail`:
```baml
class ImplementationDetail {
  function_id string
  description string
  related_concepts string[]
  acceptance_criteria string[]
  implementation ImplementationComponents
}
```

And `ImplementationComponents`:
```baml
class ImplementationComponents {
  frontend string[]
  backend string[]
  middleware string[]
  shared string[]
}
```

---

### 3. Current Output Structure

The current `_create_child_from_details()` helper (lines 294-347) produces nodes with:

```json
{
  "id": "REQ_001.1",
  "description": "...",
  "type": "sub_process",
  "parent_id": "REQ_001",
  "children": [],
  "acceptance_criteria": ["..."],
  "implementation": {
    "frontend": ["..."],
    "backend": ["..."],
    "middleware": ["..."],
    "shared": ["..."]
  }
}
```

**Missing from current output**:
- `function_id` field
- Deep nesting (e.g., `REQ_001.2.3.1`)
- `related_concepts` at child level

---

### 4. Expected Output Format (test-002-alpha.02.json)

**File**: `/home/maceo/Dev/CodeWriter5/code-writer/output/aatest01/test-002-alpha.02.json`

The expected format shows a **3-tier hierarchy**:

```
REQ_001 (parent)
├── REQ_001.2 (sub_process)
│   ├── REQ_001.2.1 (implementation)
│   ├── REQ_001.2.2 (implementation)
│   └── REQ_001.2.3 (implementation)
│       ├── REQ_001.2.3.1 (implementation - 4th level!)
│       ├── REQ_001.2.3.2 (implementation)
│       └── ...
```

#### Expected Requirement Structure

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Hierarchical ID (e.g., "REQ_001.2.3") |
| `description` | string | Requirement text |
| `type` | string | "parent", "sub_process", "implementation", or "requirement" |
| `parent_id` | string? | Parent requirement ID |
| `children` | string[] | Array of child IDs |
| `acceptance_criteria` | string[] | Testable criteria |
| `related_concepts` | string[] | Technologies/concepts |
| `implementation` | object | Component breakdown |
| `function_id` | string | Semantic identifier (e.g., "Data.Codebase") |

#### Example Implementation Object

```json
{
  "implementation": {
    "frontend": [
      "UI component: Input field for user query.",
      "UI component: Display area for the parsed query."
    ],
    "backend": [
      "API endpoint: /api/code-exploration/initiate",
      "Service: CodeQueryService"
    ],
    "middleware": [
      "Authentication middleware",
      "Request validation middleware"
    ],
    "shared": [
      "Data model: CodeQuery"
    ]
  }
}
```

#### Example function_id Values

```
User.Store, Data.Codebase, Data.Query, Data.Code, Data.Task,
Data.Execution, Data.Permissions, Data.Configuration, Data.Audit,
Service.Agent, Validator.Validate, Implementation.Display
```

---

### 5. requirements_processor.py Pattern

**File**: `/home/maceo/Dev/CodeWriter5/code-writer/src2/scope/requirements_processor.py`

#### add_requirement() (lines 146-171)

Creates top-level requirements:

```python
def add_requirement(
    self,
    description: str,
    category: str = "functional",
    acceptance_criteria: Optional[List[str]] = None,
    related_concepts: Optional[List[str]] = None,
    implementation: Optional[Dict[str, Any]] = None,
    function_id: Optional[str] = None,
) -> str:
```

- Generates ID: `REQ_{counter:03d}` (e.g., `REQ_001`)
- Sets `type: "requirement"` and `parent_id: None`
- Generates semantic `function_id` from description if not provided

#### add_child() (lines 173-205)

Creates child requirements:

```python
def add_child(
    self,
    parent_id: str,
    description: str,
    category: str = "functional",
    acceptance_criteria: Optional[List[str]] = None,
    related_concepts: Optional[List[str]] = None,
    implementation: Optional[Dict[str, Any]] = None,
    function_id: Optional[str] = None,
) -> str:
```

- Generates ID: `{parent_id}.{next_seq}` (e.g., `REQ_001.2`)
- Sets `type: "implementation"` and `parent_id: parent_id`
- Updates parent's `children` array

#### create_sub_process_requirements() (lines 281-364)

Creates 3-tier hierarchy:

```python
async def create_sub_process_requirements(
    self,
    requirement: Dict[str, Any],
    parent_id: str,
    requirements: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
```

**Flow**:
1. Create parent requirement (type: "parent")
2. For each sub_process:
   - Create sub-process requirement (type: "sub_process")
   - Call `analyze_sub_process_details()` for implementation details
   - For each detail, create implementation requirement (type: "implementation")

#### analyze_sub_process_details() (lines 366-540)

Makes BAML call for implementation details:

```python
response = await asyncio.to_thread(
    baml_client.ProcessGate1SubprocessDetailsPrompt,
    sub_process=sub_process,
    parent_description=parent_description,
    scope_text=self.scope_text,
    user_confirmation=True
)
```

---

### 6. BAML Client Configuration

**File**: `baml_src/clients.baml`

#### HaikuWithOllamaFallback (lines 113-118)

```baml
client<llm> HaikuWithOllamaFallback {
  provider fallback
  options {
    strategy [CustomHaiku, EnvironmentOllama]
  }
}
```

#### CustomHaiku (lines 71-81)

```baml
client<llm> CustomHaiku {
  provider anthropic
  retry_policy Constant
  options {
    model "claude-haiku-4-5-20251001"
    api_key env.ANTHROPIC_API_KEY
    temperature 0.3
    max_tokens 64000
  }
}
```

#### EnvironmentOllama (lines 29-37)

```baml
client<llm> EnvironmentOllama {
  provider "openai-generic"
  options {
    model env.OLLAMA_MODEL
    base_url "http://localhost:11434/v1"
    temperature 0.5
    max_tokens 32015
  }
}
```

---

## 📂 Code References

### silmari-Context-Engine

| File | Lines | Description |
|------|-------|-------------|
| `planning_pipeline/step_decomposition.py` | 41-213 | Main pipeline step |
| `planning_pipeline/decomposition.py` | 133-291 | BAML decomposition |
| `planning_pipeline/decomposition.py` | 294-347 | `_create_child_from_details()` helper |
| `planning_pipeline/models.py` | 102-184 | `RequirementNode` class |
| `planning_pipeline/models.py` | 187-267 | `RequirementHierarchy` class |
| `baml_src/functions.baml` | 369-454 | `ProcessGate1InitialExtractionPrompt` |
| `baml_src/functions.baml` | 579-621 | `ProcessGate1SubprocessDetailsPrompt` |
| `baml_src/Gate1SharedClasses.baml` | 10-31 | Requirement, ImplementationDetail, ImplementationComponents |
| `baml_src/schema/InitialExtractionSchema.baml` | 9-13 | InitialExtractionResponse |
| `baml_src/schema/SubprocessDetailsSchema.baml` | 9-13 | SubprocessDetailsResponse |
| `baml_src/clients.baml` | 29-37 | EnvironmentOllama |
| `baml_src/clients.baml` | 71-81 | CustomHaiku |
| `baml_src/clients.baml` | 113-118 | HaikuWithOllamaFallback |

### CodeWriter5 (Reference Implementation)

| File | Lines | Description |
|------|-------|-------------|
| `src2/scope/requirements_processor.py` | 146-171 | `add_requirement()` |
| `src2/scope/requirements_processor.py` | 173-205 | `add_child()` |
| `src2/scope/requirements_processor.py` | 281-364 | `create_sub_process_requirements()` |
| `src2/scope/requirements_processor.py` | 366-540 | `analyze_sub_process_details()` |
| `output/aatest01/test-002-alpha.02.json` | 1-976 | Example expected output |

---

## 🏗️ Architecture Documentation

### Current Decomposition Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     step_requirement_decomposition()                      │
├─────────────────────────────────────────────────────────────────────────┤
│  1. Read research document                                               │
│  2. Call decompose_requirements()                                        │
│     ├── ProcessGate1InitialExtractionPrompt (HaikuWithOllamaFallback)   │
│     │   └── Returns: requirements[] with sub_processes[]                │
│     └── For each sub_process:                                           │
│         ProcessGate1SubprocessDetailsPrompt (EnvironmentOllama)         │
│         └── Returns: implementation_details[]                           │
│  3. Build RequirementHierarchy (2 levels)                               │
│  4. Generate Mermaid diagram                                            │
│  5. Generate property tests                                             │
│  6. Write outputs                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### Expected Flow (from requirements_processor.py pattern)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     create_sub_process_requirements()                    │
├─────────────────────────────────────────────────────────────────────────┤
│  1. ProcessGate1InitialExtractionPrompt → top-level requirements        │
│  2. For EACH requirement:                                                │
│     ├── add_requirement() → REQ_001 (type: "parent")                    │
│     └── For EACH sub_process (NOT bulk):                                │
│         ├── ProcessGate1SubprocessDetailsPrompt → implementation_details │
│         └── add_child() for each detail → REQ_001.2 (type: "sub_process")│
│             └── add_child() for each nested → REQ_001.2.1 (type: "impl")│
│  3. Output to JSON with full hierarchy                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📚 Historical Context (from thoughts/)

### Related Plans

- `thoughts/shared/plans/2026-01-02-tdd-iterative-requirement-decomposition.md` - Main TDD plan
- `thoughts/shared/plans/2026-01-02-tdd-iterative-requirement-decomposition-04-phase-4.md` - Contains Gate1 and hierarchy logic
- `thoughts/shared/plans/2026-01-01-tdd-baml-integration.md` - BAML integration plan

### Related Research

- `thoughts/shared/research/2026-01-02-iterative-requirement-decomposition-loop.md` - Iterative loop research
- `thoughts/shared/research/2026-01-01-baml-integration-research.md` - BAML integration research

### Related Requirements Artifacts

- `thoughts/shared/plans/2026-01-04-requirements/requirements_hierarchy.json` - Latest hierarchy output
- `thoughts/shared/plans/2026-01-04-requirements/requirements_diagram.mmd` - Latest Mermaid diagram

---

## 🔗 Related Research

- [BAML Integration Research](thoughts/shared/research/2026-01-01-baml-integration-research.md)
- [Iterative Requirement Decomposition Loop](thoughts/shared/research/2026-01-02-iterative-requirement-decomposition-loop.md)
- [How to Run Pipeline with BAML](thoughts/shared/docs/2026-01-03-how-to-run-pipeline-with-baml.md)

---

## ❓ Open Questions

1. **Deep nesting**: The expected format shows 4+ levels (REQ_001.2.3.1). Should the decomposition support arbitrary depth?

2. **function_id generation**: The CodeWriter5 `requirements_processor.py` generates semantic `function_id` values. Should this logic be ported to silmari-Context-Engine?

3. **Category organization**: The expected JSON has `functional`, `non_functional`, `security`, `performance`, `usability`, `integration` categories. The current implementation doesn't categorize requirements.

4. **Processing approach**: Should sub-processes be expanded one-at-a-time (as in requirements_processor.py) or in bulk (as currently done)?
