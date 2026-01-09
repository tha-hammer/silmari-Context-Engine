You are implementing a major feature of the Context Engine, a scripting pipeline that uses the Claude Agent SDK to research, plan, and implement plans.

0a. read /home/maceo/Dev/silmari-Context-Engine/thoughts/searchable/shared/plans/2026-01-04-tdd-context-window-array/00-overview.md to understand the structure of the specifications

0b. familiarize yourself with the source code in this directory

1. read thoughts/searchable/shared/plans/2026-01-05-tdd-silmari-rlm-act/00-overview.md and implement the single highest priority TASK using up to 50 subagents use `bd` commands to track:
  bd ready                    # See available work (Phase 01 is ready)
  bd show 9e1g                # View Phase 01 details
  bd update 9e1g --status=in_progress  # Start Phase 01
  bd close 9e1g               # Complete Phase 01 (unblocks Phase 02)

2. ensure all tests and linting passes, then update thoughts/searchable/shared/plans/2026-01-05-tdd-silmari-rlm-act/00-overview.md with your progress

3. use `bd` commands  to commit your changes - do not include any claude attribution

0c. CRITICALLY IMPORTANT: after ALL TESTS PASS and after each successful `bd close` emit a /clear command to clear your context window for the next issue. Each issue should work from a fresh context window. ALWAYS use /clear if all tests pass and the issue is ready to close.

Ensure implementation steps are organized around verifiable milestones, and that you have either a) validated them or b) documented the validation steps or what's not working.
