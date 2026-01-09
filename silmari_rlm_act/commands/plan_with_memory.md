# Plan with Memory

Comprehensive planning command that leverages the 4-layer memory architecture to research, plan, and track implementation phases with beads integration.

## Initial Response

When this command is invoked:

1. **Check if parameters were provided**:
   - If a file path or ticket reference was provided, skip the default message
   - Immediately read any provided files FULLY
   - Begin the research process

2. **If no parameters provided**, respond with:
```
I'll help you create a memory-integrated implementation plan.

Please provide:
1. Task description or ticket reference
2. Relevant context or constraints
3. Links to related research

Tip: `/plan_with_memory thoughts/maceo/tickets/eng_1234.md`
```

Then wait for the user's input.

## Process Steps

### Step 1: Memory Context Compilation

Before any research, compile and review the current memory state:

1. **Compile fresh working context**:
   ```bash
   .agent/hooks/compile-context.sh
   ```

2. **Review compiled context**:
   ```bash
   cat .agent/working-context/current.md
   ```

3. **Check past failures** (prevent repeating mistakes):
   ```bash
   .agent/commands.sh recall failures
   ```

4. **Check existing strategies** (leverage what worked):
   ```bash
   .agent/commands.sh recall strategies
   ```

5. **Check active constraints**:
   ```bash
   .agent/commands.sh recall constraints
   ```

### Step 2: Research Phase

1. **Read all mentioned files FULLY**:
   - Ticket files (e.g., `thoughts/maceo/tickets/eng_XXXX.md`)
   - Research documents
   - Related implementation plans
   - **IMPORTANT**: Use the Read tool WITHOUT limit/offset parameters
   - **CRITICAL**: Read files in main context before spawning sub-tasks

2. **Spawn parallel research agents**:
   - Use **codebase-locator** to find all files related to the task
   - Use **codebase-analyzer** to understand current implementation
   - Use **thoughts-locator** to find existing thoughts documents
   - Use **codebase-pattern-finder** to find similar implementations

3. **Read all files identified by research tasks**:
   - After research tasks complete, read ALL files they identified
   - Read them FULLY into the main context

4. **Present informed understanding**:
   ```
   Based on the task and my research of the codebase, I understand we need to [summary].

   Memory context shows:
   - Past failures to avoid: [list from failures]
   - Strategies that worked: [list from strategies]
   - Active constraints: [list from constraints]

   I've found that:
   - [Current implementation detail with file:line reference]
   - [Relevant pattern or constraint discovered]

   Questions that need clarification:
   - [Specific question that requires human judgment]
   ```

### Step 3: Planning Phase (TDD-Focused)

After getting initial clarifications:

1. **Identify testable behaviors**:
   - Break task into smallest observable behaviors
   - Use "Given X, when Y, then Z" format
   - Identify inputs, outputs, and edge cases

2. **Create plan structure**:
   ```
   Here's my proposed plan structure:

   ## Overview
   [1-2 sentence summary]

   ## Implementation Phases:
   1. [Phase name] - [what it accomplishes]
   2. [Phase name] - [what it accomplishes]
   3. [Phase name] - [what it accomplishes]

   Does this phasing make sense?
   ```

3. **Get feedback on structure** before writing details

### Step 4: Phase Decomposition

After structure approval:

1. **Create plan directory**:
   ```
   thoughts/searchable/plans/YYYY-MM-DD-ENG-XXXX-description/
   ```

2. **Generate overview file** (`00-overview.md`):
   ```markdown
   ---
   date: [ISO timestamp]
   author: Claude
   git_commit: [current hash]
   branch: [current branch]
   ticket: ENG-XXXX
   type: implementation-plan
   status: draft
   ---

   # [Feature Name] Implementation Plan

   ## Overview
   [Brief description]

   ## Memory Context at Planning Time
   - Failures to avoid: [from memory]
   - Strategies to leverage: [from memory]
   - Active constraints: [from memory]

   ## Phases
   1. [Phase 1 summary] - see `01-phase-1-name.md`
   2. [Phase 2 summary] - see `02-phase-2-name.md`
   3. [Phase 3 summary] - see `03-phase-3-name.md`

   ## What We're NOT Doing
   [Explicit out-of-scope items]
   ```

3. **Generate phase files** (e.g., `01-phase-1-setup.md`):
   ```markdown
   ---
   phase: 1
   title: [Phase Name]
   status: pending
   beads_issue: [to be filled]
   depends_on: []
   blocks: [phase-2]
   ---

   # Phase 1: [Name]

   ## Overview
   [What this phase accomplishes]

   ## Dependencies
   - Requires: None (first phase)
   - Blocks: Phase 2

   ## Changes Required

   ### File Group 1: [Component Name]
   **File**: `path/to/file.ext`
   **Changes**: [Summary]

   ```[language]
   // Specific code to add/modify
   ```

   ### File Group 2: [Component Name]
   ...

   ## TDD Cycle

   ### Test First (Red)
   ```[language]
   // Test code
   ```

   ### Implementation (Green)
   [Minimal implementation to pass]

   ### Refactor (Blue)
   [Cleanup and optimization]

   ## Success Criteria

   ### Automated Verification
   - [ ] Tests pass: `make test`
   - [ ] Lint passes: `make lint`
   - [ ] Type check passes: `make typecheck`

   ### Manual Verification
   - [ ] Feature works as expected
   - [ ] Edge cases handled
   ```

### Step 5: Beads Integration

After writing all phase files:

1. **Check for existing beads issues**:
   ```bash
   bd list --status=open
   ```

2. **Create epic for the plan**:
   ```bash
   bd create --title="[Feature Name]" --type=epic --priority=2
   ```
   Note the epic ID (e.g., `beads-xxxxx`)

3. **Create issues for each phase**:
   ```bash
   bd create --title="Phase 1: [Name]" --type=task --priority=2
   bd create --title="Phase 2: [Name]" --type=task --priority=2
   bd create --title="Phase 3: [Name]" --type=task --priority=2
   ```

4. **Link dependencies between phases**:
   ```bash
   bd dep add <phase-2-id> <phase-1-id>  # Phase 2 depends on Phase 1
   bd dep add <phase-3-id> <phase-2-id>  # Phase 3 depends on Phase 2
   ```

5. **Update phase files with beads IDs**:
   - Edit each phase file's frontmatter to add `beads_issue: beads-xxxxx`

6. **Sync beads**:
   ```bash
   bd sync
   ```

### Step 6: Memory Capture

Record planning decisions in memory:

1. **Record planning constraints discovered**:
   ```bash
   .agent/commands.sh constraint "plan-id" "Key constraint: [description]"
   ```

2. **Store plan summary as artifact**:
   ```bash
   .agent/hooks/artifact-manager.sh store "plan-YYYY-MM-DD-summary.md" documents
   ```

3. **Recompile working context**:
   ```bash
   .agent/hooks/compile-context.sh
   ```

### Step 7: Sync and Present

1. **Sync thoughts directory**:
   ```bash
   silmari-oracle sync -m "Add implementation plan for [feature]"
   ```

2. **Present the plan**:
   ```
   I've created the implementation plan at:
   `thoughts/searchable/plans/YYYY-MM-DD-ENG-XXXX-description/`

   Files created:
   - `00-overview.md` - Plan overview and context
   - `01-phase-1-name.md` - Phase 1 details
   - `02-phase-2-name.md` - Phase 2 details
   - `03-phase-3-name.md` - Phase 3 details

   Beads issues created:
   - Epic: beads-xxxxx - [Feature Name]
   - Phase 1: beads-yyyyy (ready)
   - Phase 2: beads-zzzzz (blocked by Phase 1)
   - Phase 3: beads-aaaaa (blocked by Phase 2)

   Please review and let me know:
   - Are the phases properly scoped?
   - Are the success criteria specific enough?
   - Any technical details that need adjustment?
   ```

3. **Iterate based on feedback**:
   - Update phase files as needed
   - Run `silmari-oracle sync` after changes
   - Update beads issues if scope changes

## Important Guidelines

1. **Memory First**: Always check memory layers before planning
2. **Be Skeptical**: Question vague requirements, verify with code
3. **Be Interactive**: Get buy-in at each major step
4. **Be Thorough**: Read all context files COMPLETELY
5. **Track Progress**: Use TodoWrite throughout planning
6. **No Open Questions**: Resolve all questions before finalizing
7. **Beads Integration**: Create issues for all phases
8. **Sync Always**: Run `bd sync` and `silmari-oracle sync` at end

## Output Structure

```
thoughts/searchable/plans/YYYY-MM-DD-ENG-XXXX-description/
├── 00-overview.md           # Plan overview, memory context
├── 01-phase-1-name.md       # Phase 1 with beads ID
├── 02-phase-2-name.md       # Phase 2 with beads ID
├── 03-phase-3-name.md       # Phase 3 with beads ID
└── ...                      # Additional phases as needed
```

## Success Criteria Format

**Always separate into two categories:**

### Automated Verification
Commands that can be run by execution agents:
- `make test`, `npm run lint`, etc.
- Specific files that should exist
- Code compilation/type checking

### Manual Verification
Requires human testing:
- UI/UX functionality
- Performance under real conditions
- Edge cases hard to automate
