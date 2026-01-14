// BAML Functions for Complete Prompt System Integration
// These functions accept rich prompts from the existing Python prompt systems
// and return structured, type-safe output using dynamic types

// Dynamic container for structured output
class DynamicContainer {
  @@dynamic
}

// Screen Flow Chat Template Strings for Modular Prompts
template_string ScreenFlowSystemRole() #"
You are a UI/UX expert helping design screen flows for a web application.
Your expertise includes:
- User experience design principles
- Modern web application patterns
- Requirements analysis and mapping
- Progressive screen flow development
"#

template_string AppContextSection(app_description: string) #"
APP DESCRIPTION:
{{ app_description }}
"#

template_string RequirementsSection(requirements_summary: string) #"
FUNCTIONAL REQUIREMENTS:
{{ requirements_summary }}
"#

template_string ScreenSpecificationFormat() #"
For each suggested screen, provide:
- id: Short identifier (e.g., "home", "login", "profile")
- title: Human-readable screen title
- route: URL route pattern
- purpose: What this screen accomplishes
- requirements_addressed: List of requirement IDs this screen satisfies
- data_sources: Data this screen needs (e.g., "userProfile", "orderHistory")
- actions: User actions available (e.g., "login", "createOrder", "editProfile")
- states: Screen states (e.g., "loading", "loaded", "error", "empty")
"#

template_string AnalysisRequirements() #"
Also provide:
- Analysis of requirements coverage
- Questions to clarify unclear aspects
- Suggestions for next steps

Focus on the core screens first. We'll iterate to add more screens and refine details.
"#

template_string JsonResponseFormat() #"
IMPORTANT: Respond ONLY with valid JSON in the following structure with ALL required fields:
{
  "message": "Brief summary of your screen suggestions",
  "suggested_screens": [
    {
      "id": "screen_id",
      "title": "Screen Title",
      "route": "/route/path",
      "purpose": "What this screen accomplishes",
      "requirements_addressed": ["REQ_001", "REQ_002"],
      "data_sources": ["dataSource1", "dataSource2"],
      "actions": ["action1", "action2"],
      "states": ["loading", "loaded", "error"]
    }
  ],
  "requirements_analysis": {
    "total_requirements": 264,
    "addressed_count": 4,
    "addressed_ids": ["REQ_001"],
    "remaining_ids": ["REQ_002"],
    "coverage_percentage": 0.015
  },
  "questions": ["Question 1?", "Question 2?"],
  "next_steps": ["Step 1", "Step 2"]
}

CRITICAL:
- Use "coverage_percentage" as a decimal (e.g., 0.015 for 1.5%, not "1.5%")
- ALWAYS include "next_steps" array
- ALWAYS include "questions" array
- NEVER use "coverage" field - use "coverage_percentage"
"#

template_string RoleContext(role: string) #"
Role: {{ role }}
"#

template_string UserInstructions(instructions: string) #"
<INSTRUCTIONS>
{{ instructions }}
</INSTRUCTIONS>
"#

template_string UserFeedback(user_feedback: string) #"
<USER_FEEDBACK>
{{ user_feedback }}
</USER_FEEDBACK>
"#

// Core BAML Functions with Dynamic Types




// =============================================================================
// BAML TEST CASES FOR PLAYGROUND TESTING
// =============================================================================
// These test cases can be run in the BAML playground to validate function behavior
// Each test includes realistic prompts from your CodeWriter4.0 system


// ============================================================================
// GATE 6: SHARED OBJECTS - BAML PLAYGROUND TESTS (24 components)
// ============================================================================

// HIGH PRIORITY COMPONENTS - GATE 6 SHARED OBJECTS

// Test 11: ProcessSharedObjectsDataTypes - Data Types Generation
test ProcessSharedObjectsDataTypes {
  functions [ProcessSharedObjectsDataTypes]
  args {
    full_prompt "RequirementId: REQ-001-user-management\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"User registration data\",\n    \"do\": \"Validate and store user information\",\n    \"output\": \"User object with validation\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-001-user-management\": {\n        \"description\": \"Create user data types for cross-platform consistency\",\n        \"acceptance_criteria\": [\"TypeScript interfaces\", \"Python Pydantic models\", \"JSON schema validation\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"create_user\": {\n        \"parameters\": {\"username\": \"string\", \"email\": \"string\", \"password\": \"string\"},\n        \"returns\": \"User\"\n    },\n    \"validate_user\": {\n        \"parameters\": {\"user\": \"User\"},\n        \"returns\": \"boolean\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"language\": \"TypeScript\", \"version\": \"4.9.0\"},\n    \"backend\": {\"language\": \"Python\", \"version\": \"3.11\", \"framework\": \"Pydantic\"},\n    \"validation\": {\"library\": \"Zod\", \"version\": \"3.20.0\"}\n}\n</tech_stack>\n\nGenerate comprehensive data types for user management system with cross-platform consistency."
    component_type "Data Types"
    role "architect"
  }
}

// Test 12: ProcessSharedObjectsValidators - Validation Logic
test ProcessSharedObjectsValidators {
  functions [ProcessSharedObjectsValidators]
  args {
    full_prompt "RequirementId: REQ-002-data-validation\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Raw user input data\",\n    \"do\": \"Validate data against schemas\",\n    \"output\": \"Validated data or error messages\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-002-data-validation\": {\n        \"description\": \"Implement comprehensive data validation for all user inputs\",\n        \"acceptance_criteria\": [\"Client-side validation\", \"Server-side validation\", \"Consistent error messages\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"validate_email\": {\n        \"parameters\": {\"email\": \"string\"},\n        \"returns\": \"ValidationResult\"\n    },\n    \"validate_password\": {\n        \"parameters\": {\"password\": \"string\"},\n        \"returns\": \"ValidationResult\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"validation\": \"Zod\", \"version\": \"3.20.0\"},\n    \"backend\": {\"validation\": \"Pydantic\", \"version\": \"2.0.0\"},\n    \"shared\": {\"schema\": \"JSON Schema\", \"version\": \"2020-12\"}\n}\n</tech_stack>\n\nGenerate validation logic for user data with consistent error handling across platforms."
    component_type "Validators"
    role "developer"
  }
}

// Test 13: ProcessSharedObjectsSerializers - Serialization Logic
test ProcessSharedObjectsSerializers {
  functions [ProcessSharedObjectsSerializers]
  args {
    full_prompt "RequirementId: REQ-003-data-serialization\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Object data structures\",\n    \"do\": \"Serialize/deserialize data\",\n    \"output\": \"JSON strings or parsed objects\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-003-data-serialization\": {\n        \"description\": \"Implement data serialization for API communication\",\n        \"acceptance_criteria\": [\"JSON serialization\", \"Type safety\", \"Version compatibility\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"serialize_user\": {\n        \"parameters\": {\"user\": \"User\"},\n        \"returns\": \"string\"\n    },\n    \"deserialize_user\": {\n        \"parameters\": {\"json\": \"string\"},\n        \"returns\": \"User\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"serialization\": \"JSON\", \"library\": \"built-in\"},\n    \"backend\": {\"serialization\": \"Pydantic\", \"format\": \"JSON\"},\n    \"shared\": {\"format\": \"JSON\", \"version\": \"RFC 7159\"}\n}\n</tech_stack>\n\nGenerate serialization utilities for user data with proper error handling and type safety."
    component_type "Serializers"
    role "developer"
  }
}

// Test 14: ProcessSharedObjectsErrors - Error Handling
test ProcessSharedObjectsErrors {
  functions [ProcessSharedObjectsErrors]
  args {
    full_prompt "RequirementId: REQ-004-error-handling\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Application errors and exceptions\",\n    \"do\": \"Handle and format errors\",\n    \"output\": \"Structured error responses\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-004-error-handling\": {\n        \"description\": \"Implement comprehensive error handling system\",\n        \"acceptance_criteria\": [\"Error codes\", \"User-friendly messages\", \"Logging integration\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"handle_validation_error\": {\n        \"parameters\": {\"error\": \"ValidationError\"},\n        \"returns\": \"ErrorResponse\"\n    },\n    \"handle_auth_error\": {\n        \"parameters\": {\"error\": \"AuthError\"},\n        \"returns\": \"ErrorResponse\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"error_handling\": \"Custom Error classes\"},\n    \"backend\": {\"error_handling\": \"Python exceptions\"},\n    \"shared\": {\"error_format\": \"RFC 7807\"}\n}\n</tech_stack>\n\nGenerate error handling system with consistent error codes and messages across platforms."
    component_type "Errors"
    role "developer"
  }
}

// Test 15: ProcessSharedObjectsSecurity - Security Utilities
test ProcessSharedObjectsSecurity {
  functions [ProcessSharedObjectsSecurity]
  args {
    full_prompt "RequirementId: REQ-005-security-utilities\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Sensitive data and credentials\",\n    \"do\": \"Apply security measures\",\n    \"output\": \"Secured data and tokens\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-005-security-utilities\": {\n        \"description\": \"Implement security utilities for data protection\",\n        \"acceptance_criteria\": [\"Password hashing\", \"Token generation\", \"Data encryption\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"hash_password\": {\n        \"parameters\": {\"password\": \"string\"},\n        \"returns\": \"string\"\n    },\n    \"verify_password\": {\n        \"parameters\": {\"password\": \"string\", \"hash\": \"string\"},\n        \"returns\": \"boolean\"\n    },\n    \"generate_token\": {\n        \"parameters\": {\"payload\": \"object\"},\n        \"returns\": \"string\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"crypto\": \"Web Crypto API\"},\n    \"backend\": {\"crypto\": \"bcrypt\", \"jwt\": \"PyJWT\"},\n    \"shared\": {\"algorithm\": \"bcrypt\", \"jwt\": \"HS256\"}\n}\n</tech_stack>\n\nGenerate security utilities for password hashing, token generation, and data encryption."
    component_type "Security"
    role "security_engineer"
  }
}

// MEDIUM PRIORITY COMPONENTS - GATE 6 SHARED OBJECTS

// Test 16: ProcessSharedObjectsConstants - Application Constants
test ProcessSharedObjectsConstants {
  functions [ProcessSharedObjectsConstants]
  args {
    full_prompt "RequirementId: REQ-006-application-constants\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Configuration values and settings\",\n    \"do\": \"Define application constants\",\n    \"output\": \"Typed constant definitions\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-006-application-constants\": {\n        \"description\": \"Define application-wide constants and configuration\",\n        \"acceptance_criteria\": [\"Type-safe constants\", \"Environment-specific values\", \"Documentation\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"get_api_url\": {\n        \"parameters\": {\"environment\": \"string\"},\n        \"returns\": \"string\"\n    },\n    \"get_database_config\": {\n        \"parameters\": {},\n        \"returns\": \"DatabaseConfig\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"constants\": \"TypeScript enums\"},\n    \"backend\": {\"constants\": \"Python constants\"},\n    \"shared\": {\"config\": \"Environment variables\"}\n}\n</tech_stack>\n\nGenerate application constants with proper typing and environment-specific configuration."
    component_type "Constants"
    role "developer"
  }
}

// Test 17: ProcessSharedObjectsUtilities - Utility Functions
test ProcessSharedObjectsUtilities {
  functions [ProcessSharedObjectsUtilities]
  args {
    full_prompt "RequirementId: REQ-007-utility-functions\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Common operations and data\",\n    \"do\": \"Process and transform data\",\n    \"output\": \"Processed results\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-007-utility-functions\": {\n        \"description\": \"Create utility functions for common operations\",\n        \"acceptance_criteria\": [\"Pure functions\", \"Type safety\", \"Reusability\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"format_date\": {\n        \"parameters\": {\"date\": \"Date\", \"format\": \"string\"},\n        \"returns\": \"string\"\n    },\n    \"sanitize_string\": {\n        \"parameters\": {\"input\": \"string\"},\n        \"returns\": \"string\"\n    },\n    \"generate_id\": {\n        \"parameters\": {\"prefix\": \"string\"},\n        \"returns\": \"string\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"utilities\": \"TypeScript functions\"},\n    \"backend\": {\"utilities\": \"Python functions\"},\n    \"shared\": {\"format\": \"ISO 8601\"}\n}\n</tech_stack>\n\nGenerate utility functions for common data processing and formatting operations."
    component_type "Utilities"
    role "developer"
  }
}

// Test 18: ProcessSharedObjectsHelpers - Helper Functions
test ProcessSharedObjectsHelpers {
  functions [ProcessSharedObjectsHelpers]
  args {
    full_prompt "RequirementId: REQ-008-helper-functions\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Complex operations and workflows\",\n    \"do\": \"Simplify and assist operations\",\n    \"output\": \"Simplified results\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-008-helper-functions\": {\n        \"description\": \"Create helper functions for complex operations\",\n        \"acceptance_criteria\": [\"Abstraction\", \"Error handling\", \"Documentation\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"create_user_helper\": {\n        \"parameters\": {\"user_data\": \"object\"},\n        \"returns\": \"User\"\n    },\n    \"validate_form_helper\": {\n        \"parameters\": {\"form_data\": \"object\"},\n        \"returns\": \"ValidationResult\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"helpers\": \"React hooks\"},\n    \"backend\": {\"helpers\": \"Python decorators\"},\n    \"shared\": {\"patterns\": \"Factory pattern\"}\n}\n</tech_stack>\n\nGenerate helper functions that simplify complex operations and provide better abstractions."
    component_type "Helpers"
    role "developer"
  }
}

// Test 19: ProcessSharedObjectsAdapters - Interface Adapters
test ProcessSharedObjectsAdapters {
  functions [ProcessSharedObjectsAdapters]
  args {
    full_prompt "RequirementId: REQ-009-interface-adapters\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"External API responses and data\",\n    \"do\": \"Adapt data to internal format\",\n    \"output\": \"Standardized internal data\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-009-interface-adapters\": {\n        \"description\": \"Create adapters for external service integration\",\n        \"acceptance_criteria\": [\"Data transformation\", \"Error handling\", \"Type safety\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"adapt_external_user\": {\n        \"parameters\": {\"external_user\": \"object\"},\n        \"returns\": \"User\"\n    },\n    \"adapt_api_response\": {\n        \"parameters\": {\"response\": \"object\"},\n        \"returns\": \"StandardResponse\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"adapters\": \"TypeScript classes\"},\n    \"backend\": {\"adapters\": \"Python classes\"},\n    \"shared\": {\"pattern\": \"Adapter pattern\"}\n}\n</tech_stack>\n\nGenerate interface adapters for external service integration and data transformation."
    component_type "Adapters"
    role "developer"
  }
}

// Test 20: ProcessSharedObjectsBuilders - Object Builders
test ProcessSharedObjectsBuilders {
  functions [ProcessSharedObjectsBuilders]
  args {
    full_prompt "RequirementId: REQ-010-object-builders\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Object construction parameters\",\n    \"do\": \"Build complex objects step by step\",\n    \"output\": \"Fully constructed objects\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-010-object-builders\": {\n        \"description\": \"Implement builder pattern for complex object creation\",\n        \"acceptance_criteria\": [\"Fluent interface\", \"Validation\", \"Immutability\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"build_user\": {\n        \"parameters\": {\"builder\": \"UserBuilder\"},\n        \"returns\": \"User\"\n    },\n    \"build_config\": {\n        \"parameters\": {\"builder\": \"ConfigBuilder\"},\n        \"returns\": \"Config\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"builders\": \"TypeScript classes\"},\n    \"backend\": {\"builders\": \"Python classes\"},\n    \"shared\": {\"pattern\": \"Builder pattern\"}\n}\n</tech_stack>\n\nGenerate object builders using the builder pattern for complex object construction."
    component_type "Builders"
    role "developer"
  }
}

// Test 21: ProcessSharedObjectsFactories - Object Factories
test ProcessSharedObjectsFactories {
  functions [ProcessSharedObjectsFactories]
  args {
    full_prompt "RequirementId: REQ-011-object-factories\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Factory parameters and type specifications\",\n    \"do\": \"Create objects based on type\",\n    \"output\": \"Typed object instances\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-011-object-factories\": {\n        \"description\": \"Implement factory pattern for object creation\",\n        \"acceptance_criteria\": [\"Type-based creation\", \"Dependency injection\", \"Extensibility\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"create_user_factory\": {\n        \"parameters\": {\"user_type\": \"string\"},\n        \"returns\": \"User\"\n    },\n    \"create_service_factory\": {\n        \"parameters\": {\"service_type\": \"string\"},\n        \"returns\": \"Service\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"factories\": \"TypeScript classes\"},\n    \"backend\": {\"factories\": \"Python classes\"},\n    \"shared\": {\"pattern\": \"Factory pattern\"}\n}\n</tech_stack>\n\nGenerate object factories for type-based object creation and dependency injection."
    component_type "Factories"
    role "developer"
  }
}

// Test 22: ProcessSharedObjectsTransformers - Data Transformers
test ProcessSharedObjectsTransformers {
  functions [ProcessSharedObjectsTransformers]
  args {
    full_prompt "RequirementId: REQ-012-data-transformers\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Source data in various formats\",\n    \"do\": \"Transform data between formats\",\n    \"output\": \"Transformed data in target format\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-012-data-transformers\": {\n        \"description\": \"Create data transformers for format conversion\",\n        \"acceptance_criteria\": [\"Bidirectional transformation\", \"Type safety\", \"Performance\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"transform_to_api_format\": {\n        \"parameters\": {\"data\": \"object\"},\n        \"returns\": \"object\"\n    },\n    \"transform_from_api_format\": {\n        \"parameters\": {\"api_data\": \"object\"},\n        \"returns\": \"object\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"transformers\": \"TypeScript functions\"},\n    \"backend\": {\"transformers\": \"Python functions\"},\n    \"shared\": {\"format\": \"JSON\"}\n}\n</tech_stack>\n\nGenerate data transformers for converting data between different formats and structures."
    component_type "Transformers"
    role "developer"
  }
}

// Test 23: ProcessSharedObjectsConverters - Data Converters
test ProcessSharedObjectsConverters {
  functions [ProcessSharedObjectsConverters]
  args {
    full_prompt "RequirementId: REQ-013-data-converters\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Data in one type/format\",\n    \"do\": \"Convert to another type/format\",\n    \"output\": \"Converted data\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-013-data-converters\": {\n        \"description\": \"Implement type and format converters\",\n        \"acceptance_criteria\": [\"Type conversion\", \"Format conversion\", \"Error handling\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"convert_string_to_number\": {\n        \"parameters\": {\"value\": \"string\"},\n        \"returns\": \"number\"\n    },\n    \"convert_date_to_string\": {\n        \"parameters\": {\"date\": \"Date\"},\n        \"returns\": \"string\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"converters\": \"TypeScript functions\"},\n    \"backend\": {\"converters\": \"Python functions\"},\n    \"shared\": {\"types\": \"Primitive types\"}\n}\n</tech_stack>\n\nGenerate data converters for type and format conversion with proper error handling."
    component_type "Converters"
    role "developer"
  }
}

// Test 24: ProcessSharedObjectsFormatters - Data Formatters
test ProcessSharedObjectsFormatters {
  functions [ProcessSharedObjectsFormatters]
  args {
    full_prompt "RequirementId: REQ-014-data-formatters\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Raw data and formatting options\",\n    \"do\": \"Format data for display\",\n    \"output\": \"Formatted data strings\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-014-data-formatters\": {\n        \"description\": \"Create data formatters for display and output\",\n        \"acceptance_criteria\": [\"Multiple formats\", \"Localization\", \"Customization\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"format_currency\": {\n        \"parameters\": {\"amount\": \"number\", \"currency\": \"string\"},\n        \"returns\": \"string\"\n    },\n    \"format_date\": {\n        \"parameters\": {\"date\": \"Date\", \"locale\": \"string\"},\n        \"returns\": \"string\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"formatters\": \"Intl API\"},\n    \"backend\": {\"formatters\": \"Python locale\"},\n    \"shared\": {\"standards\": \"ISO 4217, ISO 8601\"}\n}\n</tech_stack>\n\nGenerate data formatters for currency, dates, and other data types with localization support."
    component_type "Formatters"
    role "developer"
  }
}

// Test 25: ProcessSharedObjectsParsers - Data Parsers
test ProcessSharedObjectsParsers {
  functions [ProcessSharedObjectsParsers]
  args {
    full_prompt "RequirementId: REQ-015-data-parsers\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Raw string data and file content\",\n    \"do\": \"Parse and extract structured data\",\n    \"output\": \"Parsed object data\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-015-data-parsers\": {\n        \"description\": \"Implement parsers for various data formats\",\n        \"acceptance_criteria\": [\"JSON parsing\", \"CSV parsing\", \"Error handling\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"parse_json\": {\n        \"parameters\": {\"json_string\": \"string\"},\n        \"returns\": \"object\"\n    },\n    \"parse_csv\": {\n        \"parameters\": {\"csv_string\": \"string\"},\n        \"returns\": \"array\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"parsers\": \"JSON.parse\"},\n    \"backend\": {\"parsers\": \"json, csv modules\"},\n    \"shared\": {\"formats\": \"JSON, CSV\"}\n}\n</tech_stack>\n\nGenerate data parsers for JSON, CSV, and other common data formats."
    component_type "Parsers"
    role "developer"
  }
}

// Test 26: ProcessSharedObjectsManagers - Object Managers
test ProcessSharedObjectsManagers {
  functions [ProcessSharedObjectsManagers]
  args {
    full_prompt "RequirementId: REQ-016-object-managers\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Object lifecycle and state management\",\n    \"do\": \"Manage object instances and state\",\n    \"output\": \"Managed object instances\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-016-object-managers\": {\n        \"description\": \"Create managers for object lifecycle and state\",\n        \"acceptance_criteria\": [\"Singleton pattern\", \"State management\", \"Lifecycle hooks\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"get_user_manager\": {\n        \"parameters\": {},\n        \"returns\": \"UserManager\"\n    },\n    \"get_session_manager\": {\n        \"parameters\": {},\n        \"returns\": \"SessionManager\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"managers\": \"TypeScript classes\"},\n    \"backend\": {\"managers\": \"Python classes\"},\n    \"shared\": {\"pattern\": \"Singleton pattern\"}\n}\n</tech_stack>\n\nGenerate object managers for managing object instances and state across the application."
    component_type "Managers"
    role "developer"
  }
}

// Test 27: ProcessSharedObjectsGenerators - Code Generators
test ProcessSharedObjectsGenerators {
  functions [ProcessSharedObjectsGenerators]
  args {
    full_prompt "RequirementId: REQ-017-code-generators\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Schema definitions and templates\",\n    \"do\": \"Generate code from templates\",\n    \"output\": \"Generated code files\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-017-code-generators\": {\n        \"description\": \"Create code generators for automated development\",\n        \"acceptance_criteria\": [\"Template-based generation\", \"Type safety\", \"Customization\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"generate_types\": {\n        \"parameters\": {\"schema\": \"object\"},\n        \"returns\": \"string\"\n    },\n    \"generate_models\": {\n        \"parameters\": {\"schema\": \"object\"},\n        \"returns\": \"string\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"generators\": \"TypeScript\"},\n    \"backend\": {\"generators\": \"Python\"},\n    \"shared\": {\"templates\": \"Mustache\"}\n}\n</tech_stack>\n\nGenerate code generators for automated type and model generation from schemas."
    component_type "Generators"
    role "developer"
  }
}

// Test 28: ProcessSharedObjectsStructures - Data Structures
test ProcessSharedObjectsStructures {
  functions [ProcessSharedObjectsStructures]
  args {
    full_prompt "RequirementId: REQ-018-data-structures\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Data organization requirements\",\n    \"do\": \"Define data structures\",\n    \"output\": \"Typed data structures\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-018-data-structures\": {\n        \"description\": \"Define common data structures for the application\",\n        \"acceptance_criteria\": [\"Type definitions\", \"Performance optimization\", \"Memory efficiency\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"create_linked_list\": {\n        \"parameters\": {\"data\": \"array\"},\n        \"returns\": \"LinkedList\"\n    },\n    \"create_tree\": {\n        \"parameters\": {\"data\": \"object\"},\n        \"returns\": \"Tree\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"structures\": \"TypeScript classes\"},\n    \"backend\": {\"structures\": \"Python classes\"},\n    \"shared\": {\"algorithms\": \"Standard algorithms\"}\n}\n</tech_stack>\n\nGenerate data structures like linked lists, trees, and other common data organization patterns."
    component_type "Structures"
    role "developer"
  }
}

// Test 29: ProcessSharedObjectsLogging - Logging Utilities
test ProcessSharedObjectsLogging {
  functions [ProcessSharedObjectsLogging]
  args {
    full_prompt "RequirementId: REQ-019-logging-utilities\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Application events and messages\",\n    \"do\": \"Log and track events\",\n    \"output\": \"Structured log entries\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-019-logging-utilities\": {\n        \"description\": \"Implement comprehensive logging system\",\n        \"acceptance_criteria\": [\"Log levels\", \"Structured logging\", \"Performance monitoring\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"log_info\": {\n        \"parameters\": {\"message\": \"string\", \"data\": \"object\"},\n        \"returns\": \"void\"\n    },\n    \"log_error\": {\n        \"parameters\": {\"error\": \"Error\", \"context\": \"object\"},\n        \"returns\": \"void\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"logging\": \"Console API\"},\n    \"backend\": {\"logging\": \"Python logging\"},\n    \"shared\": {\"format\": \"JSON\"}\n}\n</tech_stack>\n\nGenerate logging utilities with structured logging and different log levels."
    component_type "Logging"
    role "developer"
  }
}

// Test 30: ProcessSharedObjectsCaching - Caching Utilities
test ProcessSharedObjectsCaching {
  functions [ProcessSharedObjectsCaching]
  args {
    full_prompt "RequirementId: REQ-020-caching-utilities\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Data and cache keys\",\n    \"do\": \"Store and retrieve cached data\",\n    \"output\": \"Cached data or cache miss\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-020-caching-utilities\": {\n        \"description\": \"Implement caching system for performance optimization\",\n        \"acceptance_criteria\": [\"TTL support\", \"Cache invalidation\", \"Memory management\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"cache_set\": {\n        \"parameters\": {\"key\": \"string\", \"value\": \"any\", \"ttl\": \"number\"},\n        \"returns\": \"void\"\n    },\n    \"cache_get\": {\n        \"parameters\": {\"key\": \"string\"},\n        \"returns\": \"any\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"caching\": \"Map, localStorage\"},\n    \"backend\": {\"caching\": \"Redis, memory\"},\n    \"shared\": {\"protocol\": \"Cache-aside\"}\n}\n</tech_stack>\n\nGenerate caching utilities with TTL support and cache invalidation strategies."
    component_type "Caching"
    role "developer"
  }
}

// Test 31: ProcessSharedObjectsSettings - Configuration Settings
test ProcessSharedObjectsSettings {
  functions [ProcessSharedObjectsSettings]
  args {
    full_prompt "RequirementId: REQ-021-configuration-settings\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Environment variables and config files\",\n    \"do\": \"Load and manage configuration\",\n    \"output\": \"Typed configuration objects\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-021-configuration-settings\": {\n        \"description\": \"Create configuration management system\",\n        \"acceptance_criteria\": [\"Environment-specific config\", \"Type safety\", \"Validation\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"load_config\": {\n        \"parameters\": {\"environment\": \"string\"},\n        \"returns\": \"Config\"\n    },\n    \"get_setting\": {\n        \"parameters\": {\"key\": \"string\"},\n        \"returns\": \"any\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"config\": \"Environment variables\"},\n    \"backend\": {\"config\": \"Python configparser\"},\n    \"shared\": {\"format\": \"JSON, YAML\"}\n}\n</tech_stack>\n\nGenerate configuration management system with environment-specific settings and validation."
    component_type "Settings"
    role "developer"
  }
}

// Test 32: ProcessSharedObjectsVerifiers - Data Verifiers
test ProcessSharedObjectsVerifiers {
  functions [ProcessSharedObjectsVerifiers]
  args {
    full_prompt "RequirementId: REQ-022-data-verifiers\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Data integrity and verification requirements\",\n    \"do\": \"Verify data integrity and authenticity\",\n    \"output\": \"Verification results\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-022-data-verifiers\": {\n        \"description\": \"Implement data verification and integrity checks\",\n        \"acceptance_criteria\": [\"Checksum verification\", \"Digital signatures\", \"Data integrity\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"verify_checksum\": {\n        \"parameters\": {\"data\": \"string\", \"checksum\": \"string\"},\n        \"returns\": \"boolean\"\n    },\n    \"verify_signature\": {\n        \"parameters\": {\"data\": \"string\", \"signature\": \"string\"},\n        \"returns\": \"boolean\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"verification\": \"Web Crypto API\"},\n    \"backend\": {\"verification\": \"Python hashlib\"},\n    \"shared\": {\"algorithms\": \"SHA-256, HMAC\"}\n}\n</tech_stack>\n\nGenerate data verifiers for checksum verification and digital signature validation."
    component_type "Verifiers"
    role "developer"
  }
}

// LOW PRIORITY COMPONENTS - GATE 6 SHARED OBJECTS

// Test 33: ProcessSharedObjectsMinimal - Minimal Implementations
test ProcessSharedObjectsMinimal {
  functions [ProcessSharedObjectsMinimal]
  args {
    full_prompt "RequirementId: REQ-023-minimal-implementations\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Basic functionality requirements\",\n    \"do\": \"Create minimal working implementations\",\n    \"output\": \"Minimal but functional code\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-023-minimal-implementations\": {\n        \"description\": \"Create minimal implementations for basic functionality\",\n        \"acceptance_criteria\": [\"Working prototypes\", \"Basic functionality\", \"Extensibility\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"minimal_user\": {\n        \"parameters\": {\"username\": \"string\"},\n        \"returns\": \"User\"\n    },\n    \"minimal_auth\": {\n        \"parameters\": {\"credentials\": \"object\"},\n        \"returns\": \"boolean\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"minimal\": \"Basic TypeScript\"},\n    \"backend\": {\"minimal\": \"Basic Python\"},\n    \"shared\": {\"approach\": \"MVP\"}\n}\n</tech_stack>\n\nGenerate minimal implementations that provide basic functionality with room for future expansion."
    component_type "Minimal"
    role "developer"
  }
}

// Test 34: ProcessSharedObjectsPrompts - Prompt Templates
test ProcessSharedObjectsPrompts {
  functions [ProcessSharedObjectsPrompts]
  args {
    full_prompt "RequirementId: REQ-024-prompt-templates\nCategory: shared_objects\n\n<IN:DO:OUT>\n{\n    \"input\": \"Template requirements and variables\",\n    \"do\": \"Generate prompt templates\",\n    \"output\": \"Reusable prompt templates\"\n}\n</IN:DO:OUT>\n\n<requirements>\n{\n    \"REQ-024-prompt-templates\": {\n        \"description\": \"Create prompt templates for AI interactions\",\n        \"acceptance_criteria\": [\"Template variables\", \"Reusability\", \"Documentation\"]\n    }\n}\n</requirements>\n\n<functions_map>\n{\n    \"generate_prompt\": {\n        \"parameters\": {\"template\": \"string\", \"variables\": \"object\"},\n        \"returns\": \"string\"\n    },\n    \"validate_prompt\": {\n        \"parameters\": {\"prompt\": \"string\"},\n        \"returns\": \"boolean\"\n    }\n}\n</functions_map>\n\n<tech_stack>\n{\n    \"frontend\": {\"templates\": \"Template literals\"},\n    \"backend\": {\"templates\": \"Python string formatting\"},\n    \"shared\": {\"format\": \"Mustache\"}\n}\n</tech_stack>\n\nGenerate prompt templates for AI interactions with variable substitution and validation."
    component_type "Prompts"
    role "developer"
  }
}

// ============================================================================
// GATE 1: INTERACTIVE REQUIREMENTS ANALYSIS - SPECIALIZED BAML FUNCTIONS
// ============================================================================

// GATE 1: INITIAL REQUIREMENTS EXTRACTION

function ProcessGate1InitialExtractionPrompt(
  scope_text: string,
  analysis_framework: string,
  user_confirmation: bool
) -> InitialExtractionResponse {
  client EnvironmentOllama  // Using local Ollama when API credits exhausted
  prompt #"
You are an expert software requirements analyst. Your task is to extract EVERY requirement from the scope text. DO NOT summarize. Extract individual requirements from EVERY section.

**MANDATORY REQUIREMENTS:**
1. Count all numbered sections in the document (e.g., '## 0.', '## 1.', '## 2.', etc.)
2. Extract AT LEAST 2-5 requirements from EACH numbered section
3. For a document with 15 sections, you MUST extract 30-75+ requirements total
4. DO NOT combine multiple requirements into one - each requirement must be separate
5. Process sections in order: Section 0, then Section 1, then Section 2, etc. - do not skip any

Scope Text:
{{scope_text}}

Analysis Framework:
{{analysis_framework}}

User Confirmation: {{user_confirmation}}

**EXTRACTION METHOD:**

For EACH numbered section (## 0, ## 1, ## 2, etc.):

1. Read the entire section content
2. Find ALL requirement statements (look for: "must", "should", "shall", "will", "needs to", "requires", "supports", "implements", "provides")
3. Extract EACH requirement as a separate item - do not combine them
4. Include requirements from:
   - Section headers and objectives
   - Bullet points and lists
   - Tables and structured data
   - Subsections (2.1, 2.2, etc.)
   - Examples and use cases
   - Technical specifications

**REQUIREMENT TYPES TO EXTRACT:**
- Functional: What the system does (features, capabilities, workflows)
- Non-functional: How it performs (performance, scalability, reliability)
- Security: Authentication, authorization, encryption, compliance
- Integration: Third-party tools, APIs, data synchronization
- Usability: User experience, interface design, accessibility
- Technical: Infrastructure, deployment, monitoring, data storage

**EXAMPLES OF GOOD REQUIREMENTS:**
- "The system must support end-to-end encryption for private chats" (specific, actionable)
- "The system must scale to 10,000+ concurrent users" (quantitative, clear)
- "The system must integrate with Slack, Gmail, and Notion" (specific integrations)
- "The system must support ISO 27001-2022 compliance" (specific standard)

**EXAMPLES OF BAD REQUIREMENTS (DO NOT CREATE THESE):**
- "The system must be secure" (too vague - break into specific security requirements)
- "The system must have good performance" (too vague - extract specific performance metrics)
- "The system must integrate with tools" (too vague - list specific tools)

**MINIMUM REQUIREMENTS:**
- If the document has 15 sections, extract at least 30 requirements (2 per section minimum)
- More sections = more requirements (aim for 2-5 per section)
- Better to extract too many than too few

**RESPONSE FORMAT:**
Return JSON with:
1. "requirements" - Array of Requirement objects (MUST have 30+ for documents with 15 sections)
2. "metadata" - Response metadata object

**Each Requirement Object:**
- "description": Specific requirement statement (required, 25+ chars)
- "sub_processes": Array of subprocess names (can be empty [])
- "related_concepts": Array of related concepts/technologies (can be empty [])

**Metadata Object:**
- "baml_validated": true
- "schema_version": "2.0.0"
- "llm_model": string (model name)
- "processing_time_ms": optional integer
- "sections_processed": integer (count of sections you processed - should match document sections)
- "extraction_completeness": "high|medium|low" (should be "high" if you extracted 2+ requirements per section)

Output ONLY the JSON object with 'requirements' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
{{ ctx.output_format }}
"#
}

// GATE 1: GAP ANALYSIS

function ProcessGate1GapAnalysisPrompt(
  scope_text: string,
  current_requirements: string,
  user_confirmation: bool
) -> GapAnalysisResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst. Analyze the provided requirements and identify potential gaps.

Scope Text:
{{scope_text}}

Current Requirements:
{{current_requirements}}

User Confirmation: {{user_confirmation}}

Output ONLY valid JSON following the schema structure.
NO prose, explanations, or code fences.

{{ ctx.output_format }}
"#
}

// GATE 1: SUBPROCESS ANALYSIS

function ProcessGate1SubprocessAnalysisPrompt(
  scope_text: string,
  current_requirements: string,
  user_confirmation: bool
) -> SubprocessAnalysisResponse {
  client EnvironmentOllama
  prompt #"
 You are an expert software analyst. Expand each requirement into specific implementation requirements.
  The sofware developer needs to know what detailed requirements are needed to implement this requirement for this project.
  For each implementation requirement:

Scope Text: {{scope_text}}
Current Requirements: {{current_requirements}}
User Confirmation: {{user_confirmation}}

        1. Provide a clear, actionable description
        2. List ALL REQUIRED STEPS to implement the requirement
        3. For each step, provide specific acceptance criteria
        4. Consider technical and functional aspects
        5. If the requirement lists specific actions, questions or decisions, include them as acceptance criteria
        6. If the requirement is a decision, include the decision and the criteria for making that decision
        7. If the requirement is a question, include the question and the criteria for answering it
        8. Add any related or dependent concepts
        9. EACH AND EVERY STEP to implement the requirement must be included
        10. For each requirement, specify exactly what components are needed:
            - frontend: UI components, pages, forms, validation, user interactions
            - backend: API endpoints, services, data processing, business logic
            - middleware: authentication, authorization, request/response processing
            - shared: data models, utilities, constants, interfaces
        Assume sub-processes exist even if not stated. Propose granular steps.\n
        

{{ ctx.output_format }}
"#
}

// GATE 1: CATEGORY ANALYSIS

function ProcessGate1CategoryAnalysisPrompt(
  category: string,
  scope_text: string,
  current_requirements: string,
  user_confirmation: bool
) -> CategoryAnalysisResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst focused on {{category}} requirements.

Category: {{category}}
Scope Text: {{scope_text}}
Current Requirements: {{current_requirements}}
User Confirmation: {{user_confirmation}}

Output ONLY valid JSON following the schema structure.
NO prose, explanations, or code fences.

{{ ctx.output_format }}
"#
}

// GATE 1: REQUIREMENT EXPANSION

function ProcessGate1RequirementExpansionPrompt(
  parent_description: string,
  scope_text: string,
  user_confirmation: bool
) -> RequirementExpansionResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst. Expand the provided requirement into specific implementation details.

Parent Requirement: {{parent_description}}
Scope Text: {{scope_text}}
User Confirmation: {{user_confirmation}}

Output ONLY valid JSON following the schema structure.
NO prose, explanations, or code fences.

{{ ctx.output_format }}
"#
}

// GATE 1: GUIDED SEARCH

function ProcessGate1GuidedSearchPrompt(
  search_strategy: string,
  search_terms: string,
  current_requirements: string,
  user_confirmation: bool
) -> GuidedSearchResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst. Perform guided search to find additional requirements.

Search Strategy: {{search_strategy}}
Search Terms: {{search_terms}}
Current Requirements: {{current_requirements}}
User Confirmation: {{user_confirmation}}

Output ONLY valid JSON following the schema structure.
NO prose, explanations, or code fences.

{{ ctx.output_format }}
"#
}

// ============================================================================
// GATE 1: ADDITIONAL SPECIALIZED BAML FUNCTIONS (10 missing functions)
// ============================================================================

// GATE 1: SUBPROCESS DETAILS ANALYSIS (RequirementsProcessor)
function ProcessGate1SubprocessDetailsPrompt(
  sub_process: string,
  parent_description: string,
  scope_text: string,
  user_confirmation: bool
) -> SubprocessDetailsResponse {
  client EnvironmentOllama  // Using local Ollama when API credits exhausted
  prompt #"
You are an expert software analyst. Expand each requirement into specific implementation requirements.
The software developer needs to know what detailed requirements are needed to implement this requirement for this project.
For each implementation requirement:
Context:
SCOPE:
{{scope_text}}

Here is the description for the parent requirement:
Parent Requirement: {{parent_description}}

Here is the description for the sub-process:
Sub-process: {{sub_process}}

1. Provide a clear, actionable description
2. List ALL REQUIRED STEPS to implement the requirement
3. For each step, provide specific acceptance criteria
4. Consider technical and functional aspects
5. If the requirement lists specific actions, questions or decisions, include them as acceptance criteria
6. If the requirement is a decision, include the decision and the criteria for making that decision
7. If the requirement is a question, include the question and the criteria for answering it
8. Add any related or dependent concepts
9. EACH AND EVERY STEP to implement the requirement must be included
10. For each requirement, specify exactly what components are needed:
    - frontend: UI components, pages, forms, validation, user interactions
    - backend: API endpoints, services, data processing, business logic
    - middleware: authentication, authorization, request/response processing
    - shared: data models, utilities, constants, interfaces
Assume sub-processes exist even if not stated. Propose granular steps.

Output ONLY valid JSON following the schema structure.
NO prose, explanations, or code fences.

{{ ctx.output_format }}
"#
}

// GATE 1: CATEGORY FUNCTIONAL ANALYSIS
function ProcessGate1CategoryFunctionalPrompt(
  scope_text: string,
  user_confirmation: bool
) -> CategoryFunctionalResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst focused on functional requirements.

Scope Text: {{scope_text}}
User Confirmation: {{user_confirmation}}

Analyze the scope text and identify all functional requirements - the specific behaviors and features the system must provide.

Output ONLY valid JSON following the schema structure.
NO prose, explanations, or code fences.

{{ ctx.output_format }}
"#
}

// GATE 1: CATEGORY NON-FUNCTIONAL ANALYSIS
function ProcessGate1CategoryNonFunctionalPrompt(
  scope_text: string,
  user_confirmation: bool
) -> CategoryNonFunctionalResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst focused on non-functional requirements.

Scope Text: {{scope_text}}
User Confirmation: {{user_confirmation}}

Analyze the scope text and identify all non-functional requirements - performance, reliability, scalability, maintainability, and other quality attributes.

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "requirements" - Array of Requirement objects
2. "metadata" - Response metadata object

**Requirement Structure Requirements:**
Each requirement must include:
- "description": Clear non-functional requirement statement (required, min 25 chars)
- "sub_processes": Array of subprocess names (required, can be empty array)
- "related_concepts": Array of related concept names (required, can be empty array)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer


Output ONLY the JSON object with 'requirements' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
{{ ctx.output_format }}
"#
}

// GATE 1: CATEGORY SECURITY ANALYSIS
function ProcessGate1CategorySecurityPrompt(
  scope_text: string,
  user_confirmation: bool
) -> CategorySecurityResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst focused on security requirements.

Scope Text: {{scope_text}}
User Confirmation: {{user_confirmation}}

Analyze the scope text and identify all security requirements - authentication, authorization, data protection, privacy, and security controls.

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "requirements" - Array of Requirement objects
2. "metadata" - Response metadata object

**Requirement Structure Requirements:**
Each requirement must include:
- "description": Clear security requirement statement (required, min 25 chars)
- "sub_processes": Array of subprocess names (required, can be empty array)
- "related_concepts": Array of related concept names (required, can be empty array)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer


Output ONLY the JSON object with 'requirements' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
{{ ctx.output_format }}
"#
}

// GATE 1: CATEGORY PERFORMANCE ANALYSIS
function ProcessGate1CategoryPerformancePrompt(
  scope_text: string,
  user_confirmation: bool
) -> CategoryPerformanceResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst focused on performance requirements.

Scope Text: {{scope_text}}
User Confirmation: {{user_confirmation}}

Analyze the scope text and identify all performance requirements - response times, throughput, resource usage, and scalability metrics.

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "requirements" - Array of Requirement objects
2. "metadata" - Response metadata object

**Requirement Structure Requirements:**
Each requirement must include:
- "description": Clear performance requirement statement (required, min 25 chars)
- "sub_processes": Array of subprocess names (required, can be empty array)
- "related_concepts": Array of related concept names (required, can be empty array)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer


Output ONLY the JSON object with 'requirements' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
{{ ctx.output_format }}
"#
}

// GATE 1: CATEGORY USABILITY ANALYSIS
function ProcessGate1CategoryUsabilityPrompt(
  scope_text: string,
  user_confirmation: bool
) -> CategoryUsabilityResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst focused on usability requirements.

Scope Text: {{scope_text}}
User Confirmation: {{user_confirmation}}

Analyze the scope text and identify all usability requirements - user interface design, user experience, accessibility, and ease of use.

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "requirements" - Array of Requirement objects
2. "metadata" - Response metadata object

**Requirement Structure Requirements:**
Each requirement must include:
- "description": Clear usability requirement statement (required, min 25 chars)
- "sub_processes": Array of subprocess names (required, can be empty array)
- "related_concepts": Array of related concept names (required, can be empty array)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer

Output ONLY the JSON object with 'requirements' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
{{ ctx.output_format }}
"#
}

// GATE 1: CATEGORY INTEGRATION ANALYSIS
function ProcessGate1CategoryIntegrationPrompt(
  scope_text: string,
  user_confirmation: bool
) -> CategoryIntegrationResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst focused on integration requirements.

Scope Text: {{scope_text}}
User Confirmation: {{user_confirmation}}

Analyze the scope text and identify all integration requirements - API integrations, data exchange, third-party services, and system interoperability.

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "requirements" - Array of Requirement objects
2. "metadata" - Response metadata object

**Requirement Structure Requirements:**
Each requirement must include:
- "description": Clear integration requirement statement (required, min 25 chars)
- "sub_processes": Array of subprocess names (required, can be empty array)
- "related_concepts": Array of related concept names (required, can be empty array)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer


Output ONLY the JSON object with 'requirements' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
{{ ctx.output_format }}
"#
}

// GATE 1: USER INTERACTIONS EXPANSION
function ProcessGate1UserInteractionsPrompt(
  parent_description: string,
  scope_text: string,
  user_confirmation: bool
) -> UserInteractionsResponse {
  client EnvironmentOllama
  prompt #"
You are an expert UX analyst. Expand the provided requirement to focus on user interactions and user experience.

Parent Requirement: {{parent_description}}
Scope Text: {{scope_text}}
User Confirmation: {{user_confirmation}}

Identify all user interaction patterns, workflows, and UX requirements needed to implement this requirement.

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "user_interactions" - Array of UserInteraction objects
2. "metadata" - Response metadata object

**UserInteraction Structure Requirements:**
Each user interaction must include:
- "description": Specific user interaction requirement (required, min 25 chars)
- "acceptance_criteria": Array of measurable criteria (required, at least 1 criterion)
- "related_concepts": Array of related concept names (required, can be empty array)
- "implementation": ImplementationComponents object (required)

**ImplementationComponents Structure:**
- "frontend": Array of UI components needed (required)
- "backend": Array of API endpoints needed (required)
- "middleware": Array of authentication/validation requirements (required)
- "shared": Array of data models needed (required)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer


Output ONLY the JSON object with 'user_interactions' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
{{ ctx.output_format }}
"#
}

// GATE 1: DATA NEEDS EXPANSION
function ProcessGate1DataNeedsPrompt(
  parent_description: string,
  scope_text: string,
  user_confirmation: bool
) -> DataNeedsResponse {
  client EnvironmentOllama
  prompt #"
You are an expert data analyst. Expand the provided requirement to focus on data needs and data management.

Parent Requirement: {{parent_description}}
Scope Text: {{scope_text}}
User Confirmation: {{user_confirmation}}

Identify all data requirements, data structures, data flow, and data management needs for this requirement.

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "data_needs" - Array of DataNeed objects
2. "metadata" - Response metadata object

**DataNeed Structure Requirements:**
Each data need must include:
- "description": Specific data requirement (required, min 25 chars)
- "acceptance_criteria": Array of measurable criteria (required, at least 1 criterion)
- "related_concepts": Array of related concept names (required, can be empty array)
- "implementation": ImplementationComponents object (required)

**ImplementationComponents Structure:**
- "frontend": Array of UI components needed (required)
- "backend": Array of API endpoints needed (required)
- "middleware": Array of authentication/validation requirements (required)
- "shared": Array of data models needed (required)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer

}

Output ONLY the JSON object with 'data_needs' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
{{ ctx.output_format }}
"#
}

// GATE 1: BUSINESS RULES EXPANSION
function ProcessGate1BusinessRulesPrompt(
  parent_description: string,
  scope_text: string,
  user_confirmation: bool
) -> BusinessRulesResponse {
  client EnvironmentOllama
  prompt #"
You are an expert business analyst. Expand the provided requirement to focus on business rules and business logic.

Parent Requirement: {{parent_description}}
Scope Text: {{scope_text}}
User Confirmation: {{user_confirmation}}

Identify all business rules, validation logic, decision points, and business constraints needed for this requirement.

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "business_rules" - Array of BusinessRule objects
2. "metadata" - Response metadata object

**BusinessRule Structure Requirements:**
Each business rule must include:
- "description": Specific business rule requirement (required, min 25 chars)
- "acceptance_criteria": Array of measurable criteria (required, at least 1 criterion)
- "related_concepts": Array of related concept names (required, can be empty array)
- "implementation": ImplementationComponents object (required)

**ImplementationComponents Structure:**
- "frontend": Array of UI components needed (required)
- "backend": Array of API endpoints needed (required)
- "middleware": Array of authentication/validation requirements (required)
- "shared": Array of data models needed (required)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer

}

Output ONLY the JSON object with 'business_rules' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
{{ ctx.output_format }}
"#
}

// ============================================================================
// GATE 1: MISSING FUNCTIONS - REQUIREMENT VALIDATION & PRIORITIZATION
// ============================================================================

function ProcessGate1RequirementValidationPrompt(
  scope_text: string,
  current_requirements: string
) -> RequirementValidationResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst. Validate the provided requirements against the scope.

Scope Text:
{{scope_text}}

Current Requirements:
{{current_requirements}}

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "validation_results" - Array of ValidationResult objects
2. "metadata" - Response metadata object

**ValidationResult Structure Requirements:**
Each validation result must include:
- "requirement_id": Unique identifier for the requirement being validated (required)
- "component_name": Name of the component if applicable (optional)
- "is_valid": Boolean indicating if requirement is valid (required)
- "validation_issues": Array of identified issues (required, can be empty array if valid)
- "suggestions": Array of improvement suggestions (required, can be empty array)
- "confidence_score": Confidence in validation result, 0.0-1.0 (optional)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer

}

Output ONLY the JSON object with 'validation_results' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
  {{ ctx.output_format }}
"#
}

function ProcessGate1RequirementPrioritizationPrompt(
  scope_text: string,
  current_requirements: string
) -> RequirementPrioritizationResponse {
  client EnvironmentOllama
  prompt #"
You are an expert requirements analyst. Prioritize the provided requirements.

Scope Text:
{{scope_text}}

Current Requirements:
{{current_requirements}}

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "prioritized_requirements" - Array of PrioritizedRequirement objects
2. "metadata" - Response metadata object

**PrioritizedRequirement Structure Requirements:**
Each prioritized requirement must include:
- "requirement_id": Unique identifier for the requirement (required)
- "priority_level": Priority level - "high", "medium", or "low" (required)
- "priority_score": Numeric priority score between 0.0 and 1.0 (required, float)
- "justification": Explanation for the priority assignment (required, min 25 chars)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer

}

Output ONLY the JSON object with 'prioritized_requirements' array and 'metadata' object at the top level.
NO prose, explanations, or code fences.
  {{ ctx.output_format }}
"#
}

// ============================================================================
// GATE 2-5: FOUNDATIONAL GATES - SPECIALIZED BAML FUNCTIONS
// ============================================================================

// GATE 2: TECH STACK - SPECIALIZED BAML FUNCTIONS

function ProcessGate2TechStackPrompt(
  full_prompt: string,
  component_type: string,
  role: string
) -> string {
  client EnvironmentOllama
  prompt #"
{{full_prompt}}

Role: {{role}}
Component: {{component_type}}
Domain: Tech Stack Analysis

You are a platform architect. Your job is to analyze these requirements and scope and make FINAL, SINGULAR technology decisions. 
If the project requirements call out for specific technology, use that.

RULES:
1. Choose the Svelte + Svelte Kit framework unless otherwise specified or there is an exceedingly strong signal to choose another framework. Should there be a strong signal to choose another framework, choose the one with the most supporting evidence. Choose ONE option for each requirement based on the strongest signal in the requirements and the scope
2. If multiple options are presented, select the one with the most supporting evidence
3. If, after your analysis, no clear winner exists, select Svelte + Svelte Kit
4. NEVER suggest alternatives
5. NEVER hedge decisions
6. NEVER add explanations
7. For web apps without specific requirements:
   - Backend: Node.js with Express for web server
   - Database: MongoDB if database needed
   - Frontend: Svelte + SvelteKit
8. DO NOT USE unless explicitly required in project details:
   - AWS, Google Cloud
   - Docker, Kubernetes
   - Microservices
   - Single-page app frameworks (React, Next.js, Angular, Vue, Svelte)
9. Select the most appropriate architectural pattern based on your technology choices and the project scope and requirements. Choose between:
   - MVC (Model-View-Controller), 
   - MVVM (Model-View-ViewModel), and 
   - VIPER (View-Interactor-Presenter-Entity-Router)

Return in this JSON format:
{
  "tech_stack": {
    "components": {
      "frontend": {
        "framework": "",
        "name": "",
        "version": "",
        "configuration": ""
      },
      "backend": {
        "framework": "", 
        "name": "",
        "version": "",
        "configuration": ""
      },
      "database": {
        "type": "",
        "name": "",
        "version": "",
        "configuration": ""
      },
      "language": {
        "name": "",
        "version": "",
        "configuration": ""
      }
    },
    "infrastructure": {
      "cloud": {
        "provider": "",
        "account_id": "",
        "region": "",
        "configuration": ""
      },
      "build": {
        "name": "",
        "version": "",
        "configuration": ""
      },
      "deploy": {
        "name": "",
        "version": "",
        "configuration": ""
      }
    },
    "dependencies": [],
    "third_party_packages": [],
    "services": {
      "llm": {
        "provider": "",
        "connect_url": "",
        "api_key": ""
      },
      "database": {
        "url": "",
        "name": "",
        "user": "",
        "password": ""
      },
      "web_server": {
        "url": "",
        "port": "",
        "connection_string": ""
      }
    },
    "api_keys": {
      "service_name": "key_value"
    }
  }
}
{{ ctx.output_format }}
"#
}

// GATE 3: FUNCTIONS - SPECIALIZED BAML FUNCTIONS

function ProcessGate3FunctionsPrompt(
  full_prompt: string,
  component_type: string,
  role: string
) -> Gate3FunctionMappingResponse {
  client EnvironmentOllama
  prompt #"
{{full_prompt}}

Role: {{role}}
Component: {{component_type}}
Domain: Function Mapping & UX Design

**FUNCTION MAPPING INSTRUCTIONS:**
- Map requirements to specific functions and interfaces
- Design user experience flows and interactions
- Create function chains and dependency relationships
- Generate comprehensive function specifications
- Include input/output parameters and business logic
- Consider error handling and edge cases
- Design for scalability and maintainability

Generate function mapping following the specifications above.

{{ ctx.output_format }}
"#
}

// GATE 4: IN:DO:OUT - SPECIALIZED BAML FUNCTIONS
// Function moved to gate4_execution_patterns.baml

// GATE 5: DATA FLOW & ARCHITECTURE - SPECIALIZED BAML FUNCTIONS

function ProcessGate5DataFlowPrompt(
  full_prompt: string,
  component_type: string,
  role: string
) -> string {
  client EnvironmentOllama
  prompt #"
{{full_prompt}}

Role: {{role}}
Component: {{component_type}}
Domain: Data Flow & Architecture

**DATA FLOW & ARCHITECTURE INSTRUCTIONS:**
- Design data flow patterns and storage architecture
- Create file structure and interface mappings
- Define data storage and retrieval mechanisms
- Generate comprehensive architectural specifications
- Include performance and scalability considerations
- Consider data consistency and integrity
- Design for maintainability and extensibility

Generate data flow and architecture following the specifications above.
{{ ctx.output_format }}
"#
}


// Screen Flow Chat Tests for Debugging

test ProcessScreenFlowChatSimple {
  functions [ProcessScreenFlowChat]
  args {
    app_description "A simple task management application where users can create, edit, and track tasks."
    requirements_summary "USER REQUEST: Initial screen creation\n\nCOVERAGE STATUS:\n- Total Requirements: 10\n- Addressed: 0 (0.0%)\n- Remaining: 10\n- Priority Requirements to Address: 10\n\n🎯 PRIORITY FOCUS: Create screens for unaddressed requirements marked with 🎯\n\n==================================================\n\nFUNCTIONAL REQUIREMENTS:\n  🎯 PRIORITY: REQ_001: User authentication and login\n  🎯 PRIORITY: REQ_002: Task creation and editing\n  🎯 PRIORITY: REQ_003: Task list display\n  🎯 PRIORITY: REQ_004: Task status management\n  🎯 PRIORITY: REQ_005: User profile management"
    role "UI_ARCHITECT"
    instructions "PRIORITY: Focus on core user workflows that address multiple requirements simultaneously.\nCreate fundamental screens like authentication, dashboard, and main navigation.\nCRITICAL: DO NOT suggest screens that duplicate existing functionality.\nSuggest 3-5 screens that each address multiple related requirements."
    user_feedback "continue processing requirements"
  }
  @@assert({{ this.message != "" }})
  @@assert({{ this.suggested_screens.length > 0 }})
  @@assert({{ this.requirements_analysis.coverage_percentage >= 0 }})
}

test ProcessScreenFlowChatMinimal {
  functions [ProcessScreenFlowChat]
  args {
    app_description "Simple todo app"
    requirements_summary "FUNCTIONAL REQUIREMENTS:\n  🎯 PRIORITY: REQ_001: Login functionality\n  🎯 PRIORITY: REQ_002: Task creation"
    role "UI_ARCHITECT"
    instructions "Create basic screens"
    user_feedback "start with login"
  }
  @@assert({{ this.message != "" }})
  @@assert({{ this.suggested_screens.length > 0 }})
}
// ============================================================================
// GATE 2: BAML FUNCTIONS FOR TECH STACK AND SCREEN FLOW WITH DYNAMIC TYPES
// ============================================================================

// Gate 2 Tech Stack Selection with Dynamic Schema Adaptation
function ProcessTechStackSelection(
  scope_text: string,
  existing_tech_preferences: string?,
  requirements_context: string?,
  role: string
) -> TechStackResponse {
  client EnvironmentOllama
  prompt #"
You are a platform architect. Your job is to analyze requirements and scope and make FINAL, SINGULAR technology decisions.

{{ scope_text }}

{% if existing_tech_preferences %}
EXISTING TECH PREFERENCES:
{{ existing_tech_preferences }}
{% endif %}

{% if requirements_context %}
REQUIREMENTS CONTEXT:
{{ requirements_context }}
{% endif %}

**RESPONSE FORMAT (CRITICAL):**
Return a Response object with TWO top-level keys:
1. "tech_stack" - Single TechStackComponents object
2. "metadata" - Response metadata object

**TechStackComponents Structure Requirements:**
The tech_stack object must include:
- "frontend": FrontendTechStack object with framework, name, version, configuration (required)
- "backend": BackendTechStack object with framework, name, version, configuration (required)
- "database": DatabaseTechStack object with type, name, version, configuration (required)
- "language": LanguageTechStack object (optional)
- "infrastructure": InfrastructureTechStack object (optional)
- "dependencies": Array of dependency names (optional)
- "third_party_packages": Array of package names (optional)

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (always use this version)
- "llm_model": string (the model name, e.g., "gemma3:latest")
- "processing_time_ms": optional integer

**TECHNOLOGY SELECTION RULES:**
1. Choose the Svelte + Svelte Kit framework unless otherwise specified or there is an exceedingly strong signal to choose another framework
2. If multiple options are presented, select the one with the most supporting evidence
3. If, after your analysis, no clear winner exists, select Svelte + Svelte Kit
4. NEVER suggest alternatives
5. NEVER hedge decisions
6. NEVER add explanations beyond what's in the structure
7. For web apps without specific requirements:
   - Backend: Node.js with Express for web server
   - Database: MongoDB if database needed
   - Frontend: Svelte + SvelteKit
8. DO NOT USE unless explicitly required in project details:
   - AWS, Google Cloud
   - Docker, Kubernetes
   - Microservices
   - Single-page app frameworks (React, Next.js, Angular, Vue, Svelte)
9. Select the most appropriate architectural pattern based on your technology choices


Output ONLY the JSON object with 'tech_stack' object and 'metadata' object at the top level.
NO prose, explanations, or code fences.

Role: {{ role }}
{{ ctx.output_format }}
"#
}


// Tests for Gate 2 BAML Functions with Dynamic Types
test ProcessTechStackSelectionBasic {
  functions [ProcessTechStackSelection]
  type_builder {
    // Test dynamic modification of TechStackResponse
    dynamic class TechStackResponse {
      test_context string?
      framework_detected string?
    }

    // Test React-specific dynamic fields
    dynamic class FrontendFeatures {
      jsx_patterns string[]?
      hooks_usage string[]?
      test_react_feature string?
    }

    // Test Express-specific dynamic fields
    dynamic class BackendFeatures {
      middleware_patterns string[]?
      api_patterns string[]?
      test_express_feature string?
    }
  }
  args {
    scope_text "Build a React web application with user authentication and task management using Express backend"
    existing_tech_preferences ""
    requirements_context "React frontend, Express backend, user auth, CRUD operations"
    role "architect"
  }
  @@assert({{ this.tech_stack != "" }})
  @@assert({{ this.confidence_score >= 0.0 and this.confidence_score <= 1.0 }})
  @@assert({{ this.decision_rationale != "" }})
}


// ============================================================================
// GATE 3: INTERFACE MAPPING - BAML FUNCTIONS WITH DYNAMIC TYPES
// ============================================================================

// Main Interface Mapping Function for Requirements Groups
function ProcessInterfaceMapping(
  group_requirements: string,
  group_context: string,
  tech_stack_context: string?,
  role: string
) -> InterfaceMappingResponse {
  client EnvironmentOllama
  prompt #"
You are an expert software architect specializing in interface mapping and service extraction.
Analyze the provided requirements and tech stack to identify services, design patterns, and architectural improvements.

REQUIREMENTS TO ANALYZE:

{{ group_requirements }}


{% if tech_stack_context %}
TECH STACK CONTEXT:
{{ tech_stack_context }}
{% endif %}

**RESPONSE FORMAT (API 2.0 STANDARD):**
Return a Response object with FOUR top-level keys following Gate API 2.0:
1. "functions" - Array of FunctionDefinition objects
2. "service_groups" - Object mapping group IDs to ServiceGroup objects (optional)
3. "interface_contracts" - Object mapping contract IDs to InterfaceContract objects (optional)
4. "metadata" - Response metadata object

**Analysis Process:**
IMPORTANT:
- Focus on architectural services, not individual functions
- Identify design patterns that match requirement complexity
- Recommend organization improvements for maintainability
- Find shared code opportunities to reduce duplication
- Consider scalability, testability, and separation of concerns

Analyze systematically to provide comprehensive interface mapping and service extraction.
1. FUNCTION DEFINITIONS
Identify concrete functions/services based on requirements:
- function_id: Unique identifier (use requirement ID format)
- function_name: Clear, descriptive name (e.g., "authenticateUser")
- description: Specific responsibilities and business logic
- interfaces: Array of interface references this function provides/requires
- dependencies: Array of other function IDs this depends on
- implementation_component: Where implemented (e.g., "backend.auth_service")
- acceptance_criteria_id: Related acceptance criteria ID

2. SERVICE GROUPS 
Group related functions into logical service units:
- group_id: Unique identifier
- group_name: Descriptive name
- services: Array of function_ids in this group
- shared_contracts: Array of contract_ids shared by group

3. INTERFACE CONTRACTS 
Define contracts between components:
- contract_id: Unique identifier
- provider: Component providing the interface
- consumer: Component consuming the interface
- methods: Array of contract methods with inputs/outputs
- data_format: Data format used (e.g., "JSON", "Protocol Buffers")

**Response Metadata Requirements:**
The "metadata" object must include:
- "baml_validated": true (always set to true)
- "schema_version": "2.0.0" (API 2.0 version)
- "llm_model": string (the model name)
- "processing_time_ms": optional integer


Output ONLY the JSON object with keys: 'functions', 'service_groups', 'interface_contracts', and 'metadata'.

IMPORTANT: Focus on architectural services, not individual functions. Identify design patterns that match requirement complexity.
  {{ ctx.output_format }}
"#

}

// Enhanced Interface Mapping with Dynamic Type Adaptation
function ProcessInterfaceMappingWithDynamicTypes(
  requirements_context: string,
  tech_stack_info: string,
  group_metadata: string,
  role: string
) -> Gate3DynamicContainer {
  client EnvironmentOllama
  prompt #"
You are a software architect with expertise in interface mapping and dynamic system design.

REQUIREMENTS CONTEXT:
{{ requirements_context }}

TECH STACK INFO:
{{ tech_stack_info }}

GROUP METADATA:
{{ group_metadata }}

Perform comprehensive interface mapping analysis and provide structured output for:

1. Complete interface mapping response with service extraction, patterns, organization, and shared code
2. Requirement group analysis with complexity assessment
3. Metadata about the analysis process

Adapt your analysis to the specific tech stack and provide framework-specific guidance where applicable.
  {{ ctx.output_format }}
"#

}

