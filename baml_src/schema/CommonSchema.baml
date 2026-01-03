// Common Frontend Schema Classes
// Shared across all frontend gate schemas to avoid duplication

class ParameterDefinition {
  name string
  type string  // string|number|object|array|boolean
  description string
  required bool
  @@dynamic
}

class ResponseMetadata {
  baml_validated bool
  processing_time_ms int?
  schema_version string
  llm_model string?
  @@dynamic
}

class ErrorHandlingStrategy {
  error_type string  // NetworkError|ValidationError|TimeoutError|AuthError
  handling string  // retry|throw|fallback|log
  message string?
  @@dynamic
}

class ReturnType {
  type string  // Promise<object>|Observable|object|void
  description string
  @@dynamic
}

class AccessibilityFeatures {
  aria_labels bool
  keyboard_navigation bool
  screen_reader_support bool
  wcag_level string?  // A|AA|AAA
  @@dynamic
}

// Additional shared types used across all domains
// Note: ValidationRule is defined in FrontendValidatorsSchema.baml

class DependencyDefinition {
  type string  // "npm|internal|peer|dev"
  name string
  version string?
  required bool
  @@dynamic
}

class ConfigurationOption {
  key string
  value string
  type string  // "string|number|boolean|object"
  required bool
  default_value string?
  @@dynamic
}
