# Phase 07: The system must include proper metadata in pipelin...

## Requirements

### REQ_006: The system must include proper metadata in pipeline results 

The system must include proper metadata in pipeline results when using --plan-path option

#### REQ_006.1: Include requirements_count (top-level requirement count) in 

Include requirements_count (top-level requirement count) in pipeline result metadata when validating hierarchy from --plan-path option

##### Testable Behaviors

1. When --plan-path is provided, the decomposition PhaseResult.metadata must contain a 'requirements_count' key
2. requirements_count must be an integer representing only top-level requirements (parent_id == null), not total nodes
3. requirements_count must equal len(hierarchy.requirements) from the parsed RequirementHierarchy
4. requirements_count must be included in PhaseResult.metadata before returning from _validate_hierarchy_path
5. Test: Hierarchy with 2 top-level requirements each having 3 children must report requirements_count=2
6. Test: Empty hierarchy (no requirements) must report requirements_count=0
7. Test: requirements_count must be accessible via pipeline.state.get_phase_result(PhaseType.DECOMPOSITION).metadata['requirements_count']

#### REQ_006.2: Include total_nodes count (all nodes at all levels) in pipel

Include total_nodes count (all nodes at all levels) in pipeline result metadata when validating hierarchy from --plan-path option

##### Testable Behaviors

1. When --plan-path is provided, the decomposition PhaseResult.metadata must contain a 'total_nodes' key
2. total_nodes must be an integer representing ALL nodes in the hierarchy tree (parents + children + grandchildren)
3. total_nodes must be calculated by recursively counting: sum of 1 + len(children) + sum(len(grandchild.children)) for each requirement
4. total_nodes must equal the count computed by _count_nodes() or equivalent tree traversal
5. Test: Hierarchy with 2 parents, each having 2 children, each having 2 grandchildren = 2 + 4 + 8 = 14 total_nodes
6. Test: Single parent with no children must report total_nodes=1
7. Test: total_nodes must always be >= requirements_count

#### REQ_006.3: Track and propagate the 'source' field from hierarchy metada

Track and propagate the 'source' field from hierarchy metadata to identify the decomposition origin (e.g., agent_sdk_decomposition, test, baml_decomposition)

##### Testable Behaviors

1. When --plan-path is provided, the source field from hierarchy.metadata must be included in PhaseResult.metadata
2. If hierarchy.metadata contains 'source' key, it must be copied to PhaseResult.metadata['source']
3. If hierarchy.metadata does not contain 'source' key, PhaseResult.metadata['source'] should be set to 'external_hierarchy' or omitted
4. Valid source values include: 'agent_sdk_decomposition', 'baml_decomposition', 'test', 'manual'
5. Test: Hierarchy with source='agent_sdk_decomposition' must propagate source to result metadata
6. Test: Hierarchy with source='test' must propagate source to result metadata
7. Test: Hierarchy without source field must handle gracefully (not raise exception)

#### REQ_006.4: Include decomposition_stats in pipeline result metadata when

Include decomposition_stats in pipeline result metadata when available in the hierarchy JSON file

##### Testable Behaviors

1. When --plan-path hierarchy contains decomposition_stats in metadata, it must be included in PhaseResult.metadata
2. decomposition_stats must be a dict containing: requirements_found, subprocesses_expanded, total_nodes, extraction_time_ms, expansion_time_ms
3. If decomposition_stats is present, copy it to PhaseResult.metadata['decomposition_stats']
4. If decomposition_stats is not present (e.g., manually created hierarchy), omit the field rather than setting to null
5. decomposition_stats.total_nodes should be consistent with the calculated total_nodes (validation check)
6. Test: Hierarchy with decomposition_stats must propagate all stat fields to result metadata
7. Test: Hierarchy without decomposition_stats must not include the key in result metadata


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed