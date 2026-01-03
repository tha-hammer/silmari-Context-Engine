---
date: 2026-01-01T16:07:49-05:00
researcher: Claude
git_commit: 989cd145def817bb5ece02d062844c93653c6801
branch: main
repository: silmari-Context-Engine
topic: "planning_orchestrator.py Integration with orchestrator.py Pipeline"
tags: [research, codebase, planning-pipeline, beads, orchestrator, integration]
status: complete
last_updated: 2026-01-01
last_updated_by: Claude
---

```
┌────────────────────────────────────────────────────────────────────────────┐
│                 PLANNING ORCHESTRATOR INTEGRATION RESEARCH                  │
│                                                                            │
│  How to integrate planning_orchestrator.py with orchestrator.py pipeline  │
│                                                                            │
│  Status: COMPLETE                              Date: 2026-01-01            │
└────────────────────────────────────────────────────────────────────────────┘
```

# Research: planning_orchestrator.py Integration with orchestrator.py Pipeline

**Date**: 2026-01-01T16:07:49-05:00
**Researcher**: Claude
**Git Commit**: 989cd145def817bb5ece02d062844c93653c6801
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

Research how to use the `planning_orchestrator.py` in the `orchestrator.py` pipeline to:
1. Replace `get_project_info_interactive()` with an LLM call using the 'overview.md' file to determine techstack
2. Replace `get_feature_status()` and the feature_file with plan files from planning_orchestrator
3. Modify `sync_features_with_git()` and `get_next_feature()` with beads `bd` commands

---

## 📚 Executive Summary

The integration requires mapping three distinct state systems:

| System | State Storage | Tracking Method |
|--------|--------------|-----------------|
| **orchestrator.py** | `feature_list.json` | JSON file with features array |
| **planning_orchestrator.py** | Phase files + Checkpoints | Markdown files in thoughts/shared/plans/ |
| **beads CLI** | `.beads/issues.jsonl` | Git-native issue database |

The recommended approach is to use:
- **LLM call** to analyze `overview.md` or plan files for techstack detection
- **Phase files** from planning_orchestrator as feature specifications
- **Beads commands** (`bd list`, `bd ready`, `bd close`, `bd sync`) to replace feature_list.json tracking

---

## 📊 Component Analysis

### 1. Current orchestrator.py Functions to Replace

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR.PY FUNCTIONS                             │
├──────────────────────────────┬──────────────────────────────────────────┤
│ Function                     │ Location                                 │
├──────────────────────────────┼──────────────────────────────────────────┤
│ get_project_info_interactive │ orchestrator.py:322-407                  │
│ get_feature_status           │ orchestrator.py:421-444                  │
│ get_next_feature             │ orchestrator.py:487-502                  │
│ sync_features_with_git       │ orchestrator.py:457-485                  │
└──────────────────────────────┴──────────────────────────────────────────┘
```

### 2. planning_orchestrator.py Pipeline Steps

The planning pipeline executes 5 steps in sequence:

```
┌───────────┐   ┌───────────┐   ┌─────────────────┐   ┌────────────────┐   ┌────────────┐
│  STEP 1   │   │  STEP 2   │   │     STEP 3      │   │    STEP 4      │   │  STEP 5    │
│ Research  │──▶│ Planning  │──▶│ Phase Decomp    │──▶│ Beads Integ    │──▶│  Memory    │
└───────────┘   └───────────┘   └─────────────────┘   └────────────────┘   └────────────┘
     │               │                  │                    │
     ▼               ▼                  ▼                    ▼
 research.md     plan.md         phase-*.md files      beads issues
```

**Key Files:**
- `planning_orchestrator.py` - CLI entry point
- `planning_pipeline/__init__.py` - Public API
- `planning_pipeline/pipeline.py` - Main PlanningPipeline class
- `planning_pipeline/steps.py` - Step implementations
- `planning_pipeline/beads_controller.py` - Beads CLI wrapper

---

## 🎯 Detailed Integration Mappings

### A. Replace `get_project_info_interactive()` with LLM Techstack Detection

**Current Implementation** (`orchestrator.py:322-407`):
```python
def get_project_info_interactive(preset_path=None, preset_model=None):
    info = {
        'name': str,          # Project name
        'path': Path,         # Project directory
        'stack': str,         # Tech stack (user selected from 7 options)
        'description': str,   # Multi-line project description
        'model': str          # "sonnet" or "opus"
    }
```

**Replacement Strategy**:

Use an LLM call to analyze existing project files and determine techstack automatically:

```python
def get_project_info_from_llm(project_path: Path) -> dict:
    """Detect project info using LLM analysis of overview/plan files."""

    # Priority order for techstack detection:
    sources = [
        project_path / "thoughts/shared/plans" / f"*-00-overview.md",
        project_path / "thoughts/searchable/shared/plans" / "*.md",
        project_path / "sprints" / "*.md",  # Contains Tech Stack sections
        project_path / "docs" / "ARCHITECTURE.md",
        project_path / "README.md"
    ]

    # Find first available source
    content = ""
    for pattern in sources:
        files = list(Path(project_path).glob(str(pattern)))
        if files:
            content = files[0].read_text()[:5000]  # First 5KB
            break

    prompt = f"""Analyze this project documentation and extract:
    1. Project name
    2. Tech stack (language, framework, database, etc.)
    3. Brief description

    Documentation:
    {content}

    Return as JSON: {{"name": "", "stack": "", "description": ""}}
    """

    result = run_claude_sync(prompt=prompt, timeout=60)
    info = json.loads(result["output"])
    info['path'] = project_path
    info['model'] = "sonnet"  # Default
    return info
```

**Techstack Sources Found in Codebase**:

| Location | Format | Example |
|----------|--------|---------|
| `sprints/sprint_04_web_ui_shell.md:54-64` | Code block | `Framework: Next.js 14` |
| `sprints/sprint_23_mobile_mvp.md:38` | Code block | `Platform: React Native` |
| `docs/ARCHITECTURE.md` | Markdown sections | Architecture overview |
| Phase overview files | Markdown | Contains tech context |

---

### B. Replace `get_feature_status()` and feature_file with Plan Files + Beads

**Current Implementation** (`orchestrator.py:421-444`):
```python
def get_feature_status(project_path):
    feature_file = project_path / "feature_list.json"
    features = data.get("features", [])
    return {
        "total": len(features),
        "completed": sum(1 for f in features if f.get("passes", False)),
        "remaining": len(features) - completed,
        "blocked": sum(1 for f in features if f.get("blocked", False)),
        "features": features
    }
```

**Replacement Strategy Using Beads**:

```python
from planning_pipeline.beads_controller import BeadsController

def get_feature_status_from_beads(project_path: Path) -> dict:
    """Get feature status from beads issue tracker."""
    bd = BeadsController(project_path)

    # Get all issues as JSON
    all_issues = bd.list_issues()
    open_issues = bd.list_issues(status="open")
    closed_issues = bd.list_issues(status="closed")

    # Note: blocked needs to be derived from dependencies
    # Issues with unmet dependencies are blocked
    blocked_count = 0
    if all_issues["success"]:
        for issue in all_issues["data"]:
            deps = issue.get("dependencies", [])
            if deps:
                # Check if any dependency is still open
                for dep in deps:
                    dep_id = dep.get("depends_on_id")
                    if not any(i["id"] == dep_id and i.get("status") == "closed"
                              for i in all_issues["data"]):
                        blocked_count += 1
                        break

    return {
        "total": len(all_issues.get("data", [])),
        "completed": len(closed_issues.get("data", [])),
        "remaining": len(open_issues.get("data", [])),
        "blocked": blocked_count,
        "features": all_issues.get("data", [])
    }
```

**Beads Command Equivalents**:

| orchestrator.py | Beads Command | Output |
|----------------|---------------|--------|
| `get_feature_status()` | `bd list --json` | All issues with status |
| Count completed | `bd list --status=closed --json` | Closed issues |
| Count remaining | `bd list --status=open --json` | Open issues |
| Count blocked | `bd blocked` (if exists) or derive from deps | Blocked issues |

**Plan Files as Feature Specs**:

The phase files created by `step_phase_decomposition()` contain feature specifications:

```
thoughts/shared/plans/{date}-{feature}/
├── 00-overview.md       # Epic overview with all phases
├── 01-phase-1-name.md   # Phase 1 details
├── 02-phase-2-name.md   # Phase 2 details
└── 03-phase-3-name.md   # Phase 3 details
```

**Phase File Structure** (from `steps.py:272-277`):
```markdown
# Phase N: [Name]

## Overview
## Dependencies (requires/blocks)
## Changes Required with file:line
## Success Criteria
```

---

### C. Replace `sync_features_with_git()` with `bd sync`

**Current Implementation** (`orchestrator.py:457-485`):
```python
def sync_features_with_git(project_path):
    """Scan git history for completion markers, update feature_list.json"""
    for feat in features:
        if is_feature_in_git_history(project_path, feature_id):
            feat["passes"] = True
    json.dump(data, open(feature_file, "w"), indent=2)
```

**Replacement Strategy**:

```python
def sync_features_with_git(project_path: Path) -> int:
    """Sync beads with git remote."""
    bd = BeadsController(project_path)
    result = bd.sync()

    if result["success"]:
        print(f"Beads synced: {result.get('output', '')}")
        return 0  # No "fixes" needed - beads tracks state automatically
    else:
        print(f"Sync failed: {result.get('error', '')}")
        return -1
```

**Key Difference**: Beads tracks state through CLI commands (`bd close`, `bd update`), not by scanning git history. The state is already correct; `bd sync` just pushes changes.

---

### D. Replace `get_next_feature()` with `bd ready`

**Current Implementation** (`orchestrator.py:487-502`):
```python
def get_next_feature(project_path):
    status = get_feature_status(project_path)

    for feat in sorted(status["features"], key=lambda x: x.get("priority", 99)):
        if not feat.get("passes", False) and not feat.get("blocked", False):
            deps = feat.get("dependencies", [])
            deps_met = all(...)  # Check dependencies
            if deps_met or not deps:
                return feat
    return None
```

**Replacement Strategy**:

```python
def get_next_feature(project_path: Path) -> dict | None:
    """Get next ready issue from beads (no blockers, dependencies met)."""
    bd = BeadsController(project_path)

    # bd ready already handles:
    # - Status = open
    # - All dependencies closed
    # - Not explicitly blocked
    # - Sorted by priority
    result = bd._run_bd('ready', '--limit', '1')

    if result["success"] and result.get("data"):
        issues = result["data"]
        if isinstance(issues, list) and len(issues) > 0:
            return issues[0]
        elif isinstance(issues, dict):
            return issues

    return None
```

**Add to BeadsController** (`beads_controller.py`):
```python
def get_ready_issue(self, limit: int = 1) -> dict[str, Any]:
    """Get next ready issue (no blockers)."""
    return self._run_bd('ready', f'--limit={limit}')
```

---

## 📋 State Variable Mapping

### orchestrator.py → Beads Mapping

| orchestrator.py Field | Beads Equivalent | Notes |
|-----------------------|------------------|-------|
| `feature["id"]` | `issue["id"]` | e.g., `silmari-Context-Engine-2wg` |
| `feature["name"]` | `issue["title"]` | Phase title |
| `feature["description"]` | `issue["description"]` or phase file content | Full markdown |
| `feature["passes"]` | `issue["status"] == "closed"` | Boolean → status |
| `feature["blocked"]` | Derived from dependencies | Check if deps are open |
| `feature["dependencies"]` | `issue["dependencies"][].depends_on_id` | List of issue IDs |
| `feature["priority"]` | `issue["priority"]` | 0-4 scale |
| `feature["category"]` | `issue["issue_type"]` | task/bug/feature/epic |

### Session State Mapping

| orchestrator.py | planning_orchestrator.py | Notes |
|----------------|-------------------------|-------|
| `session_num` | Not tracked | Could use beads comments |
| `consecutive_failures` | Checkpoint system | Different approach |
| `.agent/sessions/` logs | `results["steps"]` dict | In-memory vs file |
| Git commits | `bd sync` | Automatic |

---

## 🔧 Complete Integration Code

### Integrated Orchestration Loop

```python
from pathlib import Path
from planning_pipeline import PlanningPipeline, BeadsController
from planning_pipeline.claude_runner import run_claude_sync

class IntegratedOrchestrator:
    """Orchestrator using planning_pipeline and beads for state management."""

    def __init__(self, project_path: Path):
        self.project_path = project_path.resolve()
        self.bd = BeadsController(project_path)

    def get_project_info(self) -> dict:
        """Detect project info from overview.md or plan files via LLM."""
        # Find overview or plan file
        plan_files = list(self.project_path.glob("thoughts/**/plans/*-overview.md"))
        if not plan_files:
            plan_files = list(self.project_path.glob("thoughts/**/plans/*.md"))

        if not plan_files:
            # Fallback to README or return defaults
            return {
                'name': self.project_path.name,
                'path': self.project_path,
                'stack': 'Unknown',
                'description': '',
                'model': 'sonnet'
            }

        content = plan_files[0].read_text()[:5000]

        prompt = f"""Analyze this project documentation and extract:
1. Project name
2. Tech stack (language, framework, database)
3. Brief description (1-2 sentences)

Documentation:
{content}

Return ONLY valid JSON: {{"name": "...", "stack": "...", "description": "..."}}
"""

        result = run_claude_sync(prompt=prompt, timeout=60, stream=False)
        try:
            import json
            info = json.loads(result["output"])
            info['path'] = self.project_path
            info['model'] = 'sonnet'
            return info
        except:
            return {
                'name': self.project_path.name,
                'path': self.project_path,
                'stack': 'Unknown',
                'description': '',
                'model': 'sonnet'
            }

    def get_feature_status(self) -> dict:
        """Get feature status from beads issues."""
        all_result = self.bd.list_issues()
        open_result = self.bd.list_issues(status="open")
        closed_result = self.bd.list_issues(status="closed")

        all_issues = all_result.get("data", []) if all_result["success"] else []
        open_issues = open_result.get("data", []) if open_result["success"] else []
        closed_issues = closed_result.get("data", []) if closed_result["success"] else []

        # Derive blocked count from dependencies
        blocked = 0
        open_ids = {i["id"] for i in open_issues}
        for issue in all_issues:
            for dep in issue.get("dependencies", []):
                if dep.get("depends_on_id") in open_ids:
                    blocked += 1
                    break

        return {
            "total": len(all_issues),
            "completed": len(closed_issues),
            "remaining": len(open_issues),
            "blocked": blocked,
            "features": all_issues
        }

    def get_next_feature(self) -> dict | None:
        """Get next ready issue from beads."""
        result = self.bd._run_bd('ready', '--limit=1')

        if result["success"] and result.get("data"):
            data = result["data"]
            if isinstance(data, list) and data:
                return data[0]
            elif isinstance(data, dict):
                return data
        return None

    def sync_features_with_git(self) -> int:
        """Sync beads with git remote."""
        result = self.bd.sync()
        return 0 if result["success"] else -1

    def mark_feature_in_progress(self, issue_id: str) -> bool:
        """Mark a feature as in progress."""
        result = self.bd._run_bd('update', issue_id, '--status=in_progress')
        return result["success"]

    def mark_feature_complete(self, issue_id: str, reason: str = "") -> bool:
        """Mark a feature as complete."""
        result = self.bd.close_issue(issue_id, reason=reason)
        return result["success"]

    def run_planning_pipeline(self, research_prompt: str) -> dict:
        """Run the planning pipeline to create phases and beads issues."""
        pipeline = PlanningPipeline(self.project_path)
        return pipeline.run(
            research_prompt=research_prompt,
            auto_approve=False
        )
```

---

## 📁 Code References

### orchestrator.py Functions
- `get_project_info_interactive()` - `orchestrator.py:322-407`
- `get_feature_status()` - `orchestrator.py:421-444`
- `get_next_feature()` - `orchestrator.py:487-502`
- `sync_features_with_git()` - `orchestrator.py:457-485`
- `build_implement_prompt()` - `orchestrator.py:786-874`
- `orchestrate_implementation()` - `orchestrator.py:1171-1246`

### planning_pipeline Components
- `PlanningPipeline.run()` - `planning_pipeline/pipeline.py:27-241`
- `step_research()` - `planning_pipeline/steps.py:12-90`
- `step_planning()` - `planning_pipeline/steps.py:93-236`
- `step_phase_decomposition()` - `planning_pipeline/steps.py:239-296`
- `step_beads_integration()` - `planning_pipeline/steps.py:299-420`
- `BeadsController` - `planning_pipeline/beads_controller.py:9-91`
- `run_claude_sync()` - `planning_pipeline/claude_runner.py:23-81`

### Beads CLI Commands
- `bd list --json` - List all issues
- `bd list --status=open --json` - List open issues
- `bd list --status=closed --json` - List closed issues
- `bd ready --json` - Get next available issue
- `bd update <id> --status=in_progress` - Start work
- `bd close <id> --reason="..."` - Complete work
- `bd sync` - Sync with git remote
- `bd dep add <id> <depends-on>` - Add dependency

### Plan File Locations
- Primary: `thoughts/shared/plans/{date}-{feature}/`
- Searchable: `thoughts/searchable/shared/plans/`
- Phase pattern: `*-phase-*.md`
- Overview pattern: `*-00-overview.md`

---

## ⚠️ Key Considerations

### Missing Beads Commands in BeadsController

The current `BeadsController` class is missing some methods needed for full integration:

```python
# Add to planning_pipeline/beads_controller.py

def get_ready_issue(self, limit: int = 1) -> dict[str, Any]:
    """Get next ready issue (no blockers)."""
    return self._run_bd('ready', f'--limit={limit}')

def update_status(self, issue_id: str, status: str) -> dict[str, Any]:
    """Update issue status."""
    return self._run_bd('update', issue_id, f'--status={status}')

def show_issue(self, issue_id: str) -> dict[str, Any]:
    """Get full issue details."""
    return self._run_bd('show', issue_id)
```

### Directory Path Discrepancy

There's a discrepancy between where code expects files and where they exist:

| Expected | Actual |
|----------|--------|
| `thoughts/shared/plans/` | `thoughts/searchable/shared/plans/` |

The `searchable/` directory contains symlinks for grep/glob operations. Code should use the non-searchable path for writing.

### Prompt Modification for Phase-Based Features

The `build_implement_prompt()` function expects feature objects with specific fields. When using beads issues, the prompt needs adaptation:

```python
def build_implement_prompt_from_issue(issue: dict, session_num: int) -> str:
    """Build implementation prompt from beads issue."""
    # Map issue fields to feature format
    feature = {
        "id": issue["id"],
        "name": issue["title"],
        "description": issue.get("description", ""),
        "priority": issue.get("priority", 2),
        "category": issue.get("issue_type", "task"),
        "passes": issue.get("status") == "closed",
        "blocked": False,  # Derived from bd ready already filtering
        "dependencies": [d["depends_on_id"] for d in issue.get("dependencies", [])]
    }
    return build_implement_prompt(feature, session_num)
```

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         INTEGRATED ARCHITECTURE                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────┐  │
│  │ orchestrator.py │────▶│ IntegratedOrch  │────▶│ planning_pipeline   │  │
│  │  (entry point)  │     │   (new class)   │     │   (PlanningPipeline)│  │
│  └─────────────────┘     └─────────────────┘     └─────────────────────┘  │
│                                 │                         │                │
│                                 ▼                         ▼                │
│                    ┌────────────────────┐     ┌───────────────────────┐   │
│                    │  BeadsController   │     │     Phase Files       │   │
│                    │  (bd CLI wrapper)  │     │ (thoughts/shared/plans)│   │
│                    └────────────────────┘     └───────────────────────┘   │
│                                 │                         │                │
│                                 ▼                         ▼                │
│                    ┌────────────────────────────────────────────────────┐ │
│                    │               .beads/issues.jsonl                  │ │
│                    │               (git-tracked state)                  │ │
│                    └────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

Data Flow:
1. orchestrator.py → calls IntegratedOrchestrator
2. IntegratedOrchestrator → uses BeadsController for state
3. BeadsController → executes bd CLI commands
4. bd CLI → manages .beads/issues.jsonl
5. planning_pipeline → creates phase files
6. step_beads_integration → links phases to beads issues
```

---

## ✅ Summary

### Replace `get_project_info_interactive()`

Use LLM call to analyze overview/plan files:
```python
result = run_claude_sync(prompt=f"Analyze: {content}", timeout=60)
info = json.loads(result["output"])
```

### Replace `get_feature_status()`

Use beads list commands:
```python
bd = BeadsController(project_path)
all_issues = bd.list_issues()
closed = bd.list_issues(status="closed")
open_issues = bd.list_issues(status="open")
```

### Replace `get_next_feature()`

Use beads ready command:
```python
result = bd._run_bd('ready', '--limit=1')
next_issue = result["data"][0] if result["data"] else None
```

### Replace `sync_features_with_git()`

Use beads sync:
```python
result = bd.sync()
```

### Plan Files as Feature Source

Phase files created by `step_phase_decomposition()` serve as feature specifications. Each phase becomes a beads issue via `step_beads_integration()`.

---

## 🔍 Open Questions

1. **Session Logging**: Should session logs still be written to `.agent/sessions/` or replaced with beads comments/notes?

2. **Epic Tracking**: How to link multiple planning sessions under different epics?

3. **Priority Mapping**: All phases currently get `priority=2`. Should priority be derived from phase order?

4. **Complexity Detection**: Should `get_feature_complexity()` be adapted to analyze phase file content instead of feature JSON?

5. **QA Features**: How should QA features (priority 100+) be represented in the phase/beads system?

---

## 📚 Related Research

- `thoughts/shared/research/2025-12-31-planning-command-architecture.md` - Original planning architecture
- `thoughts/shared/research/2025-12-31-python-deterministic-pipeline-control.md` - Pipeline control design
- `thoughts/shared/research/2026-01-01-resume-pipeline-integration.md` - Resume functionality research
