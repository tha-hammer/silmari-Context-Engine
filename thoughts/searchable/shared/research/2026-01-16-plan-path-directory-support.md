---
date: 2026-01-16T11:26:15-05:00
researcher: Claude
git_commit: 3463ec9f7f7fda574c4c30713a61e733fb4bb005
branch: main
repository: silmari-Context-Engine
topic: "How to enable directory support for --plan-path CLI argument"
tags: [research, codebase, cli, plan-path, directory-support]
status: complete
last_updated: 2026-01-16
last_updated_by: Claude
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PLAN-PATH DIRECTORY SUPPORT RESEARCH                     │
│                          silmari-codewriter-rlm CLI                          │
│                                                                              │
│  Status: COMPLETE                                   Date: 2026-01-16        │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Enabling Directory Support for `--plan-path` CLI Argument

**Date**: 2026-01-16T11:26:15-05:00
**Researcher**: Claude
**Git Commit**: 3463ec9f7f7fda574c4c30713a61e733fb4bb005
**Branch**: main
**Repository**: silmari-Context-Engine

---

## Research Question

How can the `--plan-path` argument in `silmari_rlm_act/cli.py` be modified to accept a directory containing multiple plan files instead of requiring each filename to be specified individually?

---

## Summary

The current `--plan-path` implementation accepts only single files due to `dir_okay=False` in the Click option definition. However, the downstream pipeline code in `BEADS_SYNC` phase already contains logic to discover multiple `.md` files from a directory when given a path. The codebase has established patterns for directory-based file discovery that can be applied to enable this feature with minimal changes.

---

## Detailed Findings

### 1. Current `--plan-path` Implementation

| Aspect | Current State | Location |
|--------|---------------|----------|
| Click Option | `file_okay=True, dir_okay=False` | `cli.py:79-84` |
| File Types | Markdown (`.md`) or JSON (`.json`) | `cli.py:83-84` |
| Passed As | `hierarchy_path=plan_path` | `cli.py:219` |

**Current Definition** (`silmari_rlm_act/cli.py:79-84`):
```python
@click.option(
    "--plan-path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to existing plan document (Markdown or JSON)...",
)
```

The `dir_okay=False` explicitly prevents directory input.

---

### 2. How Plan Paths Flow Through the Pipeline

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   CLI.py     │ ──► │  pipeline.run()  │ ──► │ Format Detection│
│ --plan-path  │     │  hierarchy_path  │     │ _is_markdown_?  │
└──────────────┘     └──────────────────┘     └────────┬────────┘
                                                       │
                     ┌─────────────────────────────────┴─────────────────────────┐
                     ▼                                                           ▼
              ┌──────────────┐                                           ┌──────────────┐
              │  MARKDOWN    │                                           │    JSON      │
              │   Plan       │                                           │  Hierarchy   │
              └──────┬───────┘                                           └──────┬───────┘
                     │                                                          │
                     ▼                                                          ▼
              ┌──────────────┐                                           ┌──────────────┐
              │ Skip to      │                                           │ Validate &   │
              │ BEADS_SYNC   │                                           │ Parse JSON   │
              └──────────────┘                                           └──────────────┘
```

#### Format Detection (`pipeline.py:313-332`)

| Extension | Detected As |
|-----------|-------------|
| `.md`, `.markdown` | Markdown plan |
| `.json` | JSON hierarchy |
| Other | Content-based detection |

#### Processing Paths

| Input Type | Skipped Phases | Entry Phase |
|------------|----------------|-------------|
| Markdown Plan | RESEARCH, DECOMPOSITION, TDD_PLANNING, MULTI_DOC | BEADS_SYNC |
| JSON Hierarchy | RESEARCH, DECOMPOSITION | TDD_PLANNING |

---

### 3. Existing Directory Handling in BEADS_SYNC Phase

**Key Discovery**: The pipeline already contains logic to discover multiple `.md` files from a directory.

**Location**: `silmari_rlm_act/pipeline.py:242-251`

```python
elif kwargs.get("hierarchy_path"):
    # Markdown plan: find phase docs in the same directory
    hierarchy_path = Path(kwargs["hierarchy_path"])
    plan_dir = hierarchy_path.parent              # Get parent directory
    phase_docs = sorted(
        str(p) for p in plan_dir.glob("*.md")     # Find all .md files
        if p.name != hierarchy_path.name           # Exclude overview
    )
    phase_docs = [str(hierarchy_path)] + phase_docs  # Prepend overview
```

This code:
1. Gets the parent directory of the provided file
2. Discovers all `.md` files in that directory
3. Sorts them alphabetically
4. Prepends the original file as the "overview"

---

### 4. Established Directory Scanning Patterns

The codebase uses consistent patterns for directory-based file discovery:

#### Pattern A: Simple Glob with Sort (`pipeline.py:246-249`)
```python
phase_docs = sorted(
    str(p) for p in plan_dir.glob("*.md")
    if p.name != hierarchy_path.name
)
```

#### Pattern B: Click Directory Parameter (`cli.py:42-44`)
```python
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
)
```

#### Pattern C: Numbered Phase Discovery (`plan_discovery.py:54-63`)
```python
pattern = re.compile(rf"^{re.escape(prefix)}-(\d{{2}})-(.+)\.md$")
phases = []
for file in plan_dir.glob(f"{prefix}-*.md"):
    match = pattern.match(file.name)
    if match:
        order = int(match.group(1))
        name = match.group(2)
        phases.append(PlanPhase(path=file, order=order, name=name))
phases.sort(key=lambda p: p.order)
```

---

### 5. Plan File Organization Conventions

Plans in `thoughts/searchable/shared/plans/` follow these structures:

| Structure | Example | Discovery Method |
|-----------|---------|------------------|
| Single File | `2026-01-01-tdd-baml-integration.md` | Direct path |
| Multi-Phase Directory | `2026-01-04-1-baml-integration/` | Directory glob |
| Numbered Phases | `00-overview.md`, `01-phase-1-setup.md` | Sorted glob |

**Typical Multi-Phase Directory Structure**:
```
2026-01-04-1-baml-integration/
├── 00-overview.md
├── 01-phase-1-project-setup.md
├── 02-phase-2-schema-definitions.md
├── 03-phase-3-parsing-functions.md
└── 04-phase-4-helper-integration.md
```

---

### 6. Implementation Path Analysis

To enable directory support, the following changes would be needed:

#### Change 1: CLI Option Definition (`cli.py:79-84`)

| Current | Required Change |
|---------|-----------------|
| `file_okay=True, dir_okay=False` | `file_okay=True, dir_okay=True` |

```python
@click.option(
    "--plan-path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),  # Changed
    default=None,
    help="Path to plan document or directory containing plan files",
)
```

#### Change 2: Format Detection (`pipeline.py:549-554`)

Current detection checks file extension. For directories:

| Input | Detection Logic |
|-------|-----------------|
| File with `.md` | Markdown plan |
| File with `.json` | JSON hierarchy |
| Directory | Check for `*-overview.md` or `requirements_hierarchy.json` |

#### Change 3: Directory Resolution Logic

New logic would be needed to:
1. Detect if input is a directory (`Path.is_dir()`)
2. Find overview file (e.g., `00-overview.md` or `*-overview.md`)
3. Pass directory path downstream where existing glob logic handles file discovery

---

### 7. Existing Utilities for Plan Discovery

| Utility | Location | Purpose |
|---------|----------|---------|
| `find_plan_phases()` | `plan_discovery.py:39` | Discovers phases by prefix |
| `discover_plan_phases()` | `plan_discovery.py:86` | Discovers today's plan phases |
| `iterate_plan_phases()` | `plan_discovery.py:142` | Iterator over phases |
| `resolve_thought_path()` | `helpers.py:97` | Resolves paths with fuzzy matching |

---

## Code References

| File | Lines | Description |
|------|-------|-------------|
| `silmari_rlm_act/cli.py` | 79-84 | `--plan-path` option definition |
| `silmari_rlm_act/cli.py` | 219 | Passes `hierarchy_path` to pipeline |
| `silmari_rlm_act/pipeline.py` | 242-251 | Directory glob logic in BEADS_SYNC |
| `silmari_rlm_act/pipeline.py` | 313-332 | Format detection method |
| `silmari_rlm_act/pipeline.py` | 549-554 | Format detection invocation |
| `planning_pipeline/phase_execution/plan_discovery.py` | 39-95 | Plan phase discovery utilities |
| `planning_pipeline/helpers.py` | 97-175 | Path resolution with fuzzy matching |

---

## Architecture Documentation

### Current Data Flow

```
User Input                    Pipeline Processing              File Discovery
─────────────────────────────────────────────────────────────────────────────
--plan-path /path/to/file.md  ──►  _is_markdown_plan()  ──►  Single file used
                                         │
                                         ▼
                              BEADS_SYNC phase discovers
                              siblings via .parent.glob("*.md")
```

### With Directory Support

```
User Input                    Pipeline Processing              File Discovery
─────────────────────────────────────────────────────────────────────────────
--plan-path /path/to/dir/     ──►  is_dir() check       ──►  Find overview.md
                                         │                    or first .md file
                                         ▼
                              Pass to existing BEADS_SYNC
                              glob logic
```

---

## Historical Context (from thoughts/)

| Document | Relevance |
|----------|-----------|
| `thoughts/shared/research/2026-01-14-03-48-cli-arguments-research-planning-documents.md` | Previous CLI arguments research |
| `thoughts/shared/research/2026-01-14-09-14-silmari-Context-Engine-bc6v-plan-path-naming-research.md` | Plan path naming conventions |

---

## Related Research

- `thoughts/searchable/shared/research/2026-01-14-03-48-cli-arguments-research-planning-documents.md`
- `thoughts/searchable/shared/research/2026-01-14-09-14-silmari-Context-Engine-bc6v-plan-path-naming-research.md`

---

## Open Questions

1. **Overview Detection**: How should the "overview" or "entry" file be identified when given a directory?
   - Option A: Look for `*-overview.md` or `00-*.md`
   - Option B: Look for `requirements_hierarchy.json` for JSON directories
   - Option C: Use first file alphabetically

2. **Mixed Content**: Should a directory containing both `.md` and `.json` files be supported?

3. **Validation**: Should validation ensure the directory contains expected plan structure?

---

## Key Implementation Insight

The most efficient implementation path leverages the existing `BEADS_SYNC` glob logic at `pipeline.py:242-251`. This code already:
- Gets parent directory from a file path
- Discovers all `.md` files via glob
- Sorts them for consistent ordering
- Handles overview separation

The primary change needed is allowing directories in the CLI option and adding logic to find an entry point file when given a directory instead of a file.
