# Phase 05: The system must integrate Agent SDK with BAML modu...

## Requirements

### REQ_004: The system must integrate Agent SDK with BAML modular API (b

The system must integrate Agent SDK with BAML modular API (b.request/b.parse) to enable unified architecture using Opus 4.5 with type-safe parsing

#### REQ_004.1: Use BAML b.request to build typed prompts with output format

Use BAML b.request to build typed prompts with output format for Agent SDK calls

##### Testable Behaviors

1. BAML b.request returns a request object containing the typed prompt with {{ ctx.output_format }} substituted
2. Request object includes the full prompt text ready for Agent SDK consumption
3. Request object preserves all BAML function parameters (sub_process, parent_description, scope_text, user_confirmation)
4. Prompt includes the expected JSON schema from the BAML function's return type
5. Request builder works for all ProcessGate1 functions (SubprocessDetailsPrompt, CategoryFunctionalPrompt, RequirementValidationPrompt, etc.)
6. Async variant (await b.request.FunctionName()) is available for async Agent SDK calls
7. Sync variant (b.request.FunctionName()) is available for synchronous use cases
8. Request object can be serialized for logging/debugging purposes

#### REQ_004.2: Execute Agent SDK calls with ClaudeAgentOptions specifying c

Execute Agent SDK calls with ClaudeAgentOptions specifying claude-opus-4-5 model and optional tools (Read, Glob, Grep)

##### Testable Behaviors

1. Agent SDK client is initialized with model='claude-opus-4-5-20251101'
2. ClaudeAgentOptions correctly configures allowed_tools as ['Read', 'Glob', 'Grep'] when codebase inspection is needed
3. Permission mode is configurable (acceptEdits, ask, deny) with sensible default for read-only operations
4. Async iteration over client.receive_response() properly accumulates all TextBlock content
5. Session management allows multi-turn conversations for complex decomposition tasks
6. Timeout handling prevents hanging on unresponsive calls (default 300s, configurable)
7. Error handling captures and categorizes Agent SDK errors (API errors, timeout, tool errors)
8. Response text is accumulated from all AssistantMessage content blocks
9. Tool use results are incorporated into the response when tools are enabled

#### REQ_004.3: Parse Agent SDK responses using BAML b.parse for type-safe P

Parse Agent SDK responses using BAML b.parse for type-safe Pydantic model validation

##### Testable Behaviors

1. BAML b.parse.<FunctionName>() correctly parses raw LLM response text into typed Pydantic model
2. Parser handles partial/malformed JSON gracefully with informative error messages
3. Parsed response matches the exact schema defined in BAML (SubprocessDetailsResponse, CategoryFunctionalResponse, etc.)
4. Validation errors include field-level detail for debugging (which field failed, expected type vs actual)
5. Parser works with streaming partial responses using b.parse_stream for progressive parsing
6. Retry parsing with cleaned response text when initial parse fails (strip markdown code fences, etc.)
7. Parser returns None or raises typed exception when response cannot be parsed after retries
8. All existing BAML response types are supported: SubprocessDetailsResponse, RequirementExpansionResponse, ValidationSummary, etc.

#### REQ_004.4: Add OpusAgent client configuration to baml_src/clients.baml 

Add OpusAgent client configuration to baml_src/clients.baml with claude-opus-4-5-20251101 model

##### Testable Behaviors

1. OpusAgent client is defined in baml_src/clients.baml with provider anthropic
2. Model is set to 'claude-opus-4-5-20251101' for Opus 4.5
3. API key uses env.ANTHROPIC_API_KEY for secure credential management
4. max_tokens is set to 8192 or higher for complex decomposition responses
5. temperature is configurable via env.ANTHROPIC_TEMPERATURE with sensible default (0.3)
6. Client includes retry_policy Exponential for transient failure handling
7. BAML client regeneration (baml-cli generate) succeeds without errors
8. OpusAgent can be selected using b.with_options(client='OpusAgent') in Python code
9. Fallback client OpusWithHaikuFallback is configured using fallback provider strategy [OpusAgent, CustomHaiku]

#### REQ_004.5: Integrate Agent SDK + BAML parse pattern for decomposition P

Integrate Agent SDK + BAML parse pattern for decomposition Phase 1, TDD Planning, and Validation phases

##### Testable Behaviors

1. Decomposition Phase 1 (initial extraction) uses Agent SDK with Opus for high-quality requirement extraction
2. Decomposition Phase 2 (requirement expansion) uses BAML b.request + Agent SDK + b.parse pattern
3. TDD Planning phase uses Agent SDK for multi-turn review sessions with tool access
4. Validation phase uses Agent SDK + BAML parse for semantic validation with structured output
5. All phases maintain backward compatibility with existing Ollama fallback when API unavailable
6. Progress callbacks work correctly with async Agent SDK calls
7. Save callbacks are invoked after each requirement is processed (for incremental persistence)
8. Error handling propagates Agent SDK errors to DecompositionError with appropriate error codes
9. Configuration flag allows switching between direct BAML (local Ollama) and Agent SDK + BAML parse (Opus)


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed