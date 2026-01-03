# CodeWriter5 BAML Context Generation - Overview

## Project Goal
Integrate the CodeWriter5 BAML context generation system into the planning pipeline as step 2.5, running after requirement decomposition to provide LLM-structured context about tech stack and file organization.

## Implementation Phases

### [Phase 1: Tech Stack Extraction](2026-01-03-tdd-codewriter5-baml-context-generation-01-phase-1.md)
**Testable Function**: `extract_tech_stack(project_path: Path) -> TechStack`
- Implement BAML-based tech stack detection
- File collection for analysis
- Error handling and edge cases
- **Human Test**: Run on silmari-Context-Engine and verify Python/pytest/BAML detected

### [Phase 2: File Group Analysis](2026-01-03-tdd-codewriter5-baml-context-generation-02-phase-2.md)
**Testable Function**: `analyze_file_groups(project_path: Path, max_files: int) -> FileGroupAnalysis`
- Implement BAML-based file grouping
- Configurable file limits
- Pattern-based exclusions
- **Human Test**: Run on silmari-Context-Engine and verify planning_pipeline group identified

### [Phase 3: Context Persistence](2026-01-03-tdd-codewriter5-baml-context-generation-03-phase-3.md)
**Testable Function**: `save_context_to_disk(project_name: str, tech_stack: TechStack, file_groups: FileGroupAnalysis, output_root: Path) -> Path`
- Save generated context to output directory
- Project name sanitization
- JSON formatting
- **Human Test**: Verify files created at `output/{project-name}/groups/`

### [Phase 4: Pipeline Step Implementation](2026-01-03-tdd-codewriter5-baml-context-generation-04-phase-4.md)
**Testable Function**: `ContextGenerationStep.execute(context: WorkflowContext) -> WorkflowContext`
- Create pipeline step class
- Configuration handling
- Error resilience
- **Human Test**: Run step in isolation and verify context populated

### [Phase 5: WorkflowContext Extension](2026-01-03-tdd-codewriter5-baml-context-generation-05-phase-5.md)
**Testable Function**: `WorkflowContext.to_dict()` / `WorkflowContext.from_dict()`
- Add tech_stack and file_groups fields
- Serialization support
- Backward compatibility
- **Human Test**: Load old checkpoint and verify it still works

### [Phase 6: Full Pipeline Integration](2026-01-03-tdd-codewriter5-baml-context-generation-06-phase-6.md)
**Testable Function**: `Pipeline.run(context: WorkflowContext) -> WorkflowContext`
- Insert step 2.5 into pipeline
- Step ordering verification
- Configuration flags
- **Human Test**: Run full pipeline and verify context generated between decomposition steps

## Dependency Graph
```
Phase 1 (Tech Stack) ────┐
                          ├──> Phase 3 (Persistence) ──> Phase 4 (Step) ──> Phase 6 (Pipeline)
Phase 2 (File Groups) ───┘                                   ↑
                                                              │
                                     Phase 5 (Context) ───────┘
```

## Testing Strategy
- Unit tests for each phase
- Integration tests for phase combinations
- E2E test in phase 6
- Mock BAML responses where appropriate
- Test with real project structure

## Success Criteria
All phases complete with:
- [x] All unit tests passing (34/34 tests pass)
- [x] All integration tests passing
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] Manual human tests verified
- [x] Context generation runs between decomposition steps (Step 4/7)
- [x] Generated context accessible to downstream steps
