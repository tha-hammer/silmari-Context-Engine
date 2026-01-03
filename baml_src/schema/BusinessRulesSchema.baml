// BusinessRules Response
// Following canonical Response pattern
// Migrated: 2025-10-12 - Response pattern with metadata

// ==============================================================================
// TOP-LEVEL RESPONSE
// ==============================================================================

class BusinessRulesResponse {
  business_rules BusinessRule[]
  metadata ResponseMetadata
  @@dynamic
}

// ==============================================================================
// DOMAIN ENTITY
// ==============================================================================

// Note: BusinessRule and supporting classes are defined in Gate1SharedClasses.baml
// Note: ResponseMetadata is imported from shared schema
