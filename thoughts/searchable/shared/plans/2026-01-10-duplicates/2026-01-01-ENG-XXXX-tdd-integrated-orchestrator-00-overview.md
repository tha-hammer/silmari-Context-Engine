# IntegratedOrchestrator TDD Implementation - Overview

## Summary

Create a new `IntegratedOrchestrator` class that bridges `planning_orchestrator.py` with `orchestrator.py`, replacing JSON file-based state tracking with beads CLI commands while maintaining session logging to `.agent/sessions/`. Uses Claude SDK for LLM-powered techstack detection.

## Phase Index

| Phase | Title | Human-Testable Function | Status |
|-------|-------|------------------------|--------|
| [Phase 1](./2026-01-01-ENG-XXXX-tdd-integrated-orchestrator-01-techstack-detection.md) | LLM-Powered Techstack Detection | `orchestrator.get_project_info()` | ✅ Complete |
| [Phase 2](./2026-01-01-ENG-XXXX-tdd-integrated-orchestrator-02-feature-status.md) | Feature Status from Beads | `orchestrator.get_feature_status()` | ✅ Complete |
| [Phase 3](./2026-01-01-ENG-XXXX-tdd-integrated-orchestrator-03-next-feature.md) | Get Next Feature | `orchestrator.get_next_feature()` | ✅ Complete |
| [Phase 4](./2026-01-01-ENG-XXXX-tdd-integrated-orchestrator-04-sync-features.md) | Sync Features with Git | `orchestrator.sync_features_with_git()` | ✅ Complete |
| [Phase 5](./2026-01-01-ENG-XXXX-tdd-integrated-orchestrator-05-phase-priority.md) | Phase Priority from Order | `orchestrator.create_phase_issues()` | ✅ Complete |
| [Phase 6](./2026-01-01-ENG-XXXX-tdd-integrated-orchestrator-06-session-logging.md) | Session Logging | `orchestrator.log_session()` | ✅ Complete |
| [Phase 7](./2026-01-01-ENG-XXXX-tdd-integrated-orchestrator-07-beads-extensions.md) | BeadsController Extensions | `bd.get_ready_issue()`, `bd.update_status()` | ✅ Complete |
| [Phase 8](./2026-01-01-ENG-XXXX-tdd-integrated-orchestrator-08-integration.md) | Integration Testing | Full workflow end-to-end | ✅ Complete |

## Dependency Graph

```
Phase 1: Techstack Detection (no deps)
    ↓
Phase 7: BeadsController Extensions (can run parallel with 1)
    ↓
Phase 2: Feature Status (requires Phase 7)
    ↓
Phase 3: Next Feature (requires Phase 7)
    ↓
Phase 4: Sync Features (requires Phase 7)
    ↓
Phase 5: Phase Priority (requires Phase 2, 3, 4)
    ↓
Phase 6: Session Logging (requires Phase 1-5)
    ↓
Phase 8: Integration (requires all phases)
```

## Key Files

| File | Purpose |
|------|---------|
| `planning_pipeline/integrated_orchestrator.py` | New orchestrator class |
| `planning_pipeline/beads_controller.py` | Extended with new methods |
| `planning_pipeline/tests/test_integrated_orchestrator.py` | Unit tests |
| `planning_pipeline/tests/test_beads_controller.py` | BeadsController tests |

## Testing Strategy

- **Framework**: pytest with subprocess mocking
- **Test Types**:
  - Unit tests for each method
  - Integration tests for LLM calls (mocked)
  - Integration tests for bd CLI (mocked subprocess)
- **Mocking**: Use `unittest.mock` for subprocess.run, file I/O

## References

- Original plan: `thoughts/searchable/shared/plans/2026-01-01-tdd-integrated-orchestrator.md`
- Research: `thoughts/searchable/shared/research/2026-01-01-planning-orchestrator-integration.md`
- Patterns:
  - `planning_pipeline/pipeline.py:12-241` - PlanningPipeline class structure
  - `planning_pipeline/beads_controller.py:9-91` - BeadsController patterns
  - `orchestrator.py:322-502` - Original functions being replaced
