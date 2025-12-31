---
date: 2025-12-31T00:00:00-06:00
researcher: Claude
git_commit: b1e0e420ecc789aee0c14d10a5d0497f6783d9b6
branch: main
repository: silmari-Context-Engine
topic: "Planning Command Architecture for 4-Layer Memory Integration"
tags: [research, codebase, planning, memory-architecture, commands, beads]
status: complete
last_updated: 2025-12-31
last_updated_by: Claude
---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   RESEARCH: PLANNING COMMAND ARCHITECTURE                    │
│                     for 4-Layer Memory Integration                           │
│                                                                              │
│  Status: ✅ Complete                              Date: 2025-12-31          │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Research: Planning Command Architecture for 4-Layer Memory Integration

**Date**: 2025-12-31T00:00:00-06:00
**Researcher**: Claude
**Git Commit**: b1e0e420ecc789aee0c14d10a5d0497f6783d9b6
**Branch**: main
**Repository**: silmari-Context-Engine

---

## 📚 Research Question

How to add a new planning file that:
1. Uses the codebase's "4 factor memory" (4-layer memory architecture)
2. Leverages `/research_codebase` for initial research
3. Leverages `/create_tdd_plan` to create the plan
4. Directs the LLM to review the plan and create phases with separate files
5. Adds `bd` commands from the beads CLI for task tracking

---

## 📊 Summary

The silmari-Context-Engine codebase implements a sophisticated **four-layer memory architecture** for autonomous agents, with a command system in `.claude/commands/` that orchestrates research, planning, and implementation workflows. Creating a new planning command requires:

| Component | Implementation Pattern |
|-----------|----------------------|
| **Memory Integration** | Use `compile-context.sh` hooks and `.agent/` directory structure |
| **Research Phase** | Spawn `codebase-locator`, `codebase-analyzer`, `thoughts-locator` agents |
| **Planning Phase** | Generate structured plan with phases and success criteria |
| **Task Tracking** | Integrate `bd` commands for issue creation and dependency management |

---

## 🎯 Detailed Findings

### 1. Four-Layer Memory Architecture

The system implements four storage layers with distinct purposes:

```
┌───────────────────────────────────────────────────────────────────────────┐
│  Layer 1: WORKING CONTEXT (.agent/working-context/)                       │
│  ├─ Ephemeral, computed view for each LLM call                           │
│  ├─ Hard-capped at 8000 tokens                                            │
│  └─ Regenerated fresh each step via compile-context.sh                   │
├───────────────────────────────────────────────────────────────────────────┤
│  Layer 2: SESSIONS (.agent/sessions/)                                     │
│  ├─ Full structured event log (JSONL format)                             │
│  ├─ Source of truth for reconstruction                                    │
│  └─ Never sent directly to model                                          │
├───────────────────────────────────────────────────────────────────────────┤
│  Layer 3: MEMORY (.agent/memory/)                                         │
│  ├─ strategies/  → Approaches that worked                                 │
│  ├─ constraints/ → Active rules and requirements                          │
│  ├─ failures/    → Approaches to avoid                                    │
│  └─ entities/    → Key references and identifiers                         │
├───────────────────────────────────────────────────────────────────────────┤
│  Layer 4: ARTIFACTS (.agent/artifacts/)                                   │
│  ├─ tool-outputs/  → Large command outputs                                │
│  ├─ documents/     → Generated documentation                              │
│  └─ code-snapshots/→ Diff summaries                                       │
└───────────────────────────────────────────────────────────────────────────┘
```

**Key Files**:
- `setup-context-engineered.sh:21-34` - Architecture definition
- `setup-context-engineered.sh:169-301` - compile-context.sh implementation
- `setup-context-engineered.sh:507-564` - memory-manager.sh implementation
- `setup-context-engineered.sh:687-772` - capture-feedback.sh implementation

### 2. Command File Structure Patterns

Existing commands in `.claude/commands/` follow consistent patterns:

#### Pattern A: Sequential Steps with Sub-tasks
```markdown
## Process Steps

### Step 1: Context Gathering
1. Read mentioned files FULLY (no limit/offset)
2. Spawn parallel research tasks
3. Read files identified by research

### Step 2: Analysis
1. Present findings
2. Ask clarifying questions
...
```

**Found in**: `create_plan.md:31-141`, `create_tdd_plan.md:27-87`

#### Pattern B: Beads Integration Points
```markdown
### Step 4.5: Beads Issue Tracking (Recommended)

After writing the plan file:
1. Check for existing issues: `bd list --status=open`
2. Create or update: `bd create --title="..." --type=feature`
3. Link dependencies: `bd dep add <this-issue> <depends-on>`
```

**Found in**: `create_plan.md:272-291`, `create_tdd_plan.md:199-218`

#### Pattern C: Parallel Agent Spawning
```markdown
Spawn initial research tasks to gather context:
- Use **codebase-locator** to find files
- Use **codebase-analyzer** to understand implementation
- Use **thoughts-locator** to find existing documents
- Use **linear-ticket-reader** for ticket details
```

**Found in**: `create_plan.md:44-51`, `research_codebase.md:52-82`

### 3. Command Workflow Integration

The commands chain together through file artifacts:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  /research_     │────▶│  /create_tdd_   │────▶│  /implement_    │
│  codebase       │     │  plan           │     │  plan           │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
 thoughts/shared/        thoughts/shared/       Updates plan with
 research/*.md           plans/*.md             checkmarks [x]
```

### 4. bd (beads) CLI Commands Reference

| Command | Purpose | Usage |
|---------|---------|-------|
| `bd ready` | Find work without blockers | Discovery phase |
| `bd create` | Create new issue | `bd create --title="..." --type=task --priority=2` |
| `bd update` | Update issue status | `bd update <id> --status=in_progress` |
| `bd close` | Mark work complete | `bd close <id> --reason="Done"` |
| `bd dep add` | Add dependency | `bd dep add <issue> <depends-on>` |
| `bd sync` | Sync with git remote | End of session |
| `bd list` | List issues | `bd list --status=open` |
| `bd show` | Show issue details | `bd show <id>` |

**Priority Values**: 0 (critical) → 4 (backlog)
**Issue Types**: bug, feature, task, epic, chore

---

## 🏗️ Architecture for New Planning Command

Based on the research, here's the recommended structure for a new `/plan_with_memory` command:

### File: `.claude/commands/plan_with_memory.md`

```markdown
# Plan with Memory

Comprehensive planning command that leverages the 4-layer memory
architecture to research, plan, and track implementation phases.

## Initial Response

If no parameters provided:
```
I'll help you create a memory-integrated implementation plan.

Please provide:
1. Task description or ticket reference
2. Relevant context or constraints
3. Links to related research

Tip: `/plan_with_memory thoughts/maceo/tickets/eng_1234.md`
```

## Process Steps

### Step 1: Research Phase (via /research_codebase)

1. **Read mentioned files FULLY**
2. **Compile fresh context**:
   ```bash
   .agent/hooks/compile-context.sh
   cat .agent/working-context/current.md
   ```
3. **Check past failures**:
   ```bash
   .agent/commands.sh recall failures
   ```
4. **Spawn research agents**:
   - codebase-locator
   - codebase-analyzer
   - thoughts-locator

### Step 2: Planning Phase (via /create_tdd_plan)

1. **Present understanding** with file:line references
2. **Identify testable behaviors**
3. **Create TDD plan structure**

### Step 3: Phase Decomposition

1. **Review the plan** for phase boundaries
2. **Create separate phase files**:
   ```
   thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX/
   ├── 00-overview.md
   ├── 01-phase-1-setup.md
   ├── 02-phase-2-implementation.md
   └── 03-phase-3-verification.md
   ```
3. **Each phase file contains**:
   - Overview
   - Changes Required (with file:line)
   - Success Criteria (automated + manual)
   - Dependencies on other phases

### Step 4: Beads Integration

1. **Check existing issues**:
   ```bash
   bd list --status=open
   ```

2. **Create epic for the plan**:
   ```bash
   bd create --title="[Feature Name]" --type=epic --priority=2
   ```

3. **Create issues for each phase**:
   ```bash
   bd create --title="Phase 1: Setup" --type=task --priority=2
   bd create --title="Phase 2: Implementation" --type=task --priority=2
   bd create --title="Phase 3: Verification" --type=task --priority=2
   ```

4. **Link dependencies**:
   ```bash
   bd dep add <phase-2-id> <phase-1-id>  # Phase 2 depends on Phase 1
   bd dep add <phase-3-id> <phase-2-id>  # Phase 3 depends on Phase 2
   ```

5. **Sync**:
   ```bash
   bd sync
   ```

### Step 5: Memory Capture

1. **Record planning constraints**:
   ```bash
   .agent/commands.sh constraint "plan-id" "Key constraint discovered"
   ```

2. **Store plan as artifact**:
   ```bash
   .agent/hooks/artifact-manager.sh store "plan-summary.md" documents
   ```

3. **Update working context**:
   ```bash
   .agent/hooks/compile-context.sh
   ```

## Output Structure

### Main Plan Overview
`thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX/00-overview.md`

### Phase Files
Each phase file follows the template:

```markdown
# Phase N: [Name]

## Overview
[What this phase accomplishes]

## Dependencies
- Requires: Phase N-1 complete
- Blocks: Phase N+1

## Changes Required

### File Group 1
**File**: `path/to/file.ext`
**Changes**: [Summary]

### File Group 2
...

## Success Criteria

### Automated Verification
- [ ] Tests pass: `make test`
- [ ] Lint passes: `make lint`

### Manual Verification
- [ ] Feature works in UI
- [ ] Performance acceptable

## Beads Issue
- Issue ID: bd-XXXXX
- Dependencies: bd-YYYYY
```

## Guidelines

1. **Use TodoWrite** to track research and planning tasks
2. **Spawn agents in parallel** for efficiency
3. **Wait for all agents** before synthesizing
4. **No open questions** in final plan
5. **Always sync beads** at session end
```

---

## 📋 Code References

| File | Lines | Description |
|------|-------|-------------|
| `orchestrator.py` | 541-559 | Init prompt referencing 4-layer memory |
| `orchestrator.py` | 786-873 | Implement prompt with subagent instructions |
| `setup-context-engineered.sh` | 21-34 | 4-layer architecture definition |
| `setup-context-engineered.sh` | 169-301 | compile-context.sh implementation |
| `setup-context-engineered.sh` | 507-564 | memory-manager.sh implementation |
| `setup-context-engineered.sh` | 687-772 | capture-feedback.sh implementation |
| `setup-context-engineered.sh` | 1415-1492 | commands.sh unified interface |
| `.claude/commands/research_codebase.md` | 1-307 | Research command with agent spawning |
| `.claude/commands/create_tdd_plan.md` | 1-272 | TDD planning with behaviors |
| `.claude/commands/create_plan.md` | 1-580 | General implementation planning |
| `.claude/commands/implement_plan.md` | 1-74 | Plan execution with checkmarks |
| `~/Dev/silmari-beads/docs/CLI_REFERENCE.md` | 1-611 | Full bd CLI reference |

---

## 🚫 What We're NOT Doing

| Out of Scope | Instead |
|--------------|---------|
| Modifying core orchestrator.py | Creating command file only |
| Changing existing command files | New standalone command |
| Implementing new memory storage | Using existing 4-layer system |
| Modifying bd CLI | Using existing bd commands |

---

## 🚀 Implementation Recommendations

### Phase 1: Create Command File
1. Create `.claude/commands/plan_with_memory.md`
2. Follow existing command patterns
3. Integrate memory hooks

### Phase 2: Add Phase Decomposition
1. Template for phase files
2. Directory structure convention
3. Cross-referencing between phases

### Phase 3: Beads Integration
1. Epic creation for plans
2. Phase-to-issue mapping
3. Dependency linking

### Phase 4: Testing & Documentation
1. Test with sample planning task
2. Document in README
3. Add to skill list if needed

---

## 📚 Historical Context (from thoughts/)

No existing research documents found on this specific topic. This is the initial research for planning command architecture.

---

## 🔗 Related Research

- `README.md` - Project overview with 4-layer memory explanation
- `docs/ARCHITECTURE.md` - Deeper architecture documentation
- `AGENTS.md` - Agent workflow instructions

---

## ❓ Open Questions

1. **Phase file storage**: Should phase files be in a subdirectory or flat with naming convention?
   - **Recommendation**: Subdirectory for organization

2. **Beads epic linking**: Should the epic ID be stored in phase files?
   - **Recommendation**: Yes, in YAML frontmatter

3. **Memory persistence**: How long should planning constraints persist?
   - **Recommendation**: Until explicitly removed or plan completed

---

## ✅ Success Criteria

### Automated Verification
- [ ] Command file parses correctly as markdown
- [ ] All referenced memory hooks exist
- [ ] bd commands are valid syntax

### Manual Verification
- [ ] Command workflow produces expected artifacts
- [ ] Beads issues created correctly
- [ ] Phase files link properly to each other
