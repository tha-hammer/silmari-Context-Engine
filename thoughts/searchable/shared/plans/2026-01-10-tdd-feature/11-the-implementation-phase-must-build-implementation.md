# Phase 11: The Implementation Phase must build implementation...

## Requirements

### REQ_010: The Implementation Phase must build implementation prompts w

The Implementation Phase must build implementation prompts with TDD plan paths, Epic ID, and Issue IDs

#### REQ_010.1: Include TDD plan file path in the implementation prompt to e

Include TDD plan file path in the implementation prompt to enable Claude to read and implement the detailed plan

##### Testable Behaviors

1. Implementation prompt includes absolute path to TDD plan overview file
2. Path is validated to exist before inclusion in prompt
3. Path format is compatible with Claude file reading (e.g., 'Read the plan at: /path/to/plan.md')
4. Non-absolute paths are resolved relative to project root
5. Error handling returns PhaseResult with FAILED status if plan file not found
6. Plan path is registered as a ContextEntry in CentralContextStore with EntryType.PLAN
7. Plan content is indexed in VectorSearchIndex for future reference
8. WorkingLLMContext receives summary of plan for orchestrator coordination

#### REQ_010.2: Include Beads Epic ID in prompt with show command to enable 

Include Beads Epic ID in prompt with show command to enable Claude to view and track the overall epic progress

##### Testable Behaviors

1. Epic ID is included in prompt under '## Beads Tracking' section
2. Format includes 'Epic: {epicID}' label
3. Include 'bd show {epicID}' command example for viewing epic details
4. Epic section is conditionally rendered only when epicID is non-empty
5. Epic information is registered in CentralContextStore with EntryType.TRACKING
6. Summary includes epic purpose for WorkingLLMContext visibility

#### REQ_010.3: Include all Phase Issue IDs in prompt to enable Claude to tr

Include all Phase Issue IDs in prompt to enable Claude to track and update individual phase progress through beads

##### Testable Behaviors

1. All phase issue IDs are listed under '**Phase Issues**:' section
2. Each issue is formatted as '- Phase {N}: `{issueID}`' with phase number and issue ID
3. Phase numbers start at 1 and increment sequentially
4. Issue IDs preserve ordering from beads integration step
5. Empty issue_ids list results in section being omitted
6. Each phase issue is registered in CentralContextStore with parent_id linking to epic
7. TaskBatcher can batch phases based on CWA entry limits

#### REQ_010.4: Include implementation instructions for Red-Green-Refactor T

Include implementation instructions for Red-Green-Refactor TDD cycle to guide Claude through proper test-driven development

##### Testable Behaviors

1. Instructions section includes numbered steps (1-7) for TDD workflow
2. Step 1: Read the plan overview at the specified path
3. Step 2: Find the phase documents in the same directory
4. Step 3: Implement the highest priority TASK using subagents
5. Step 4: Run all tests with 'pytest' or 'make test' commands
6. Step 5: Update the plan with progress
7. Step 6: Use 'bd close <id>' when phase is complete
8. Step 7: Use '/clear' after closing an issue to start fresh
9. CRITICAL section emphasizes /clear after ALL TESTS PASS and after each successful bd close
10. Instructions are stored in CWA as reusable context entry with high priority

#### REQ_010.5: Include instructions for closing beads issues to enable prop

Include instructions for closing beads issues to enable proper progress tracking and phase transition

##### Testable Behaviors

1. Prompt includes 'Use `bd` commands to track progress' section header
2. Include 'bd ready' command to see available work
3. Include 'bd show <id>' command to view issue details
4. Include 'bd update <id> --status=in_progress' command to start work
5. Include 'bd close <id>' command to complete work with note about dependency unblocking
6. Include 'bd sync' command to sync changes
7. Commands are formatted as code blocks for easy copying
8. Workflow state transitions are tracked in CentralContextStore


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed