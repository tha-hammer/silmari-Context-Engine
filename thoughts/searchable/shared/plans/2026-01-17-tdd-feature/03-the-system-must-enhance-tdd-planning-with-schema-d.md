# Phase 03: The system must enhance TDD planning with schema-d...

## Requirements

### REQ_002: The system must enhance TDD planning with schema-driven prom

The system must enhance TDD planning with schema-driven prompts incorporating design-by-contract patterns including preconditions, postconditions, and invariants

#### REQ_002.1: Enhance TDD_GENERATION_PROMPT to include function_id, catego

Enhance TDD_GENERATION_PROMPT to include function_id, category, and ImplementationComponents (frontend, backend, middleware, shared) for schema-driven plan generation

##### Testable Behaviors

1. TDD_GENERATION_PROMPT_V2 template includes {function_id} placeholder that maps to RequirementNode.function_id
2. Template includes {category} placeholder populated from requirement categorization (functional, security, performance, usability, integration)
3. Template includes {frontend_components} section listing UI components, pages, forms, and user interactions
4. Template includes {backend_components} section listing API endpoints, services, and business logic
5. Template includes {middleware_components} section listing authentication, authorization, and request/response processing
6. Template includes {shared_components} section listing data models, utilities, constants, and interfaces
7. Prompt template is stored in a configurable location allowing override without code changes
8. Backward compatibility maintained with existing TDD_GENERATION_PROMPT when enhanced fields are not available
9. Unit tests verify all placeholders are correctly substituted in generated prompts
10. Integration test confirms enhanced prompt produces higher quality TDD plans compared to baseline

#### REQ_002.2: Add design contract extraction for preconditions, postcondit

Add design contract extraction for preconditions, postconditions, and invariants during the decomposition phase to enable design-by-contract TDD planning

##### Testable Behaviors

1. Decomposition prompt includes explicit instructions to extract preconditions from requirement text
2. Decomposition prompt includes explicit instructions to extract postconditions from requirement text
3. Decomposition prompt includes explicit instructions to extract invariants from requirement text
4. Extracted contracts follow standardized format: 'subject predicate value' (e.g., 'user.id != null')
5. Each RequirementNode contains contracts: DesignContracts field after decomposition
6. DesignContracts includes preconditions: List[str] with minimum 1 precondition per requirement
7. DesignContracts includes postconditions: List[str] with minimum 1 postcondition per requirement
8. DesignContracts includes invariants: List[str] (optional, may be empty)
9. Contract extraction handles requirements where contracts are implicit and generates reasonable defaults
10. BAML schema updated to include DesignContracts in decomposition response type
11. Validation ensures extracted contracts are syntactically valid predicate expressions
12. Fallback mechanism generates generic contracts when LLM extraction fails

#### REQ_002.3: Generate TDD plans with Gherkin format (Given/When/Then) tes

Generate TDD plans with Gherkin format (Given/When/Then) test specifications for behavior-driven development alignment

##### Testable Behaviors

1. Each TDD plan includes a 'Test Specification' section using Gherkin syntax
2. Gherkin scenarios include Feature: header derived from requirement description
3. Each acceptance criterion generates at least one Scenario with Given/When/Then steps
4. Given steps establish preconditions from extracted design contracts
5. When steps describe the action being tested derived from requirement
6. Then steps verify postconditions and expected outcomes
7. Scenarios include And/But steps for complex multi-step behaviors
8. Scenario Outlines used for parameterized tests with Examples table
9. Background section included when common setup applies to multiple scenarios
10. Generated Gherkin is syntactically valid and can be parsed by behave/cucumber parsers
11. Gherkin scenarios are traceable via @acceptance_criteria_id tags
12. Integration with existing TDD plan markdown format preserves file structure

#### REQ_002.4: Include minimum 3 edge cases derived from preconditions in e

Include minimum 3 edge cases derived from preconditions in each TDD plan to ensure comprehensive test coverage of boundary conditions

##### Testable Behaviors

1. Each TDD plan includes an 'Edge Cases' section with minimum 3 edge cases
2. Edge cases are systematically derived from extracted preconditions
3. For each precondition, generate at least one edge case that violates it
4. NULL/empty edge cases generated for all nullable input parameters
5. Boundary value edge cases generated for numeric preconditions (min-1, min, max, max+1)
6. Type mismatch edge cases generated for typed parameters
7. Edge cases include expected error type and error message
8. Edge cases are prioritized by risk/impact (high/medium/low)
9. Each edge case includes clear test scenario description
10. Edge cases include both synchronous and asynchronous failure modes where applicable
11. Duplicate or redundant edge cases are deduplicated
12. Edge cases traceable to source precondition via precondition_id reference

#### REQ_002.5: Generate complete pytest tests with real assertions instead 

Generate complete pytest tests with real assertions instead of placeholders, producing immediately runnable test code

##### Testable Behaviors

1. Each TDD plan includes a '🔴 Red' section with complete, runnable pytest test code
2. Generated tests use pytest conventions: test_ prefix, assert statements, fixtures
3. Tests include proper imports for the module under test and testing utilities
4. All assertions use concrete expected values derived from postconditions, not placeholders
5. Tests include pytest.raises() blocks for edge case error assertions
6. Fixtures generated for common test setup using @pytest.fixture decorator
7. Mock objects generated using unittest.mock or pytest-mock for external dependencies
8. Parameterized tests generated using @pytest.mark.parametrize for multiple input scenarios
9. Test docstrings include requirement ID and acceptance criteria reference
10. Generated tests follow AAA pattern: Arrange, Act, Assert with clear section comments
11. Tests are syntactically valid Python that passes flake8/ruff linting
12. Test file path follows project conventions: tests/test_{module_name}.py
13. Tests can be executed with 'pytest {test_file}' without modification


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed