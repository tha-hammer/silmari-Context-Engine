// Category Functional - Gate 1 functional requirements
// Following canonical Response pattern
// Migrated: 2025-10-12 - Response pattern with metadata

// ==============================================================================
// TOP-LEVEL RESPONSE
// ==============================================================================

class CategoryFunctionalResponse {
  requirements Requirement[]
  metadata ResponseMetadata
  @@dynamic
}

// ==============================================================================
// DOMAIN ENTITY
// ==============================================================================

// Note: ResponseMetadata is imported from shared schema
