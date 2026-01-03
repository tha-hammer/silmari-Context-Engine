// Initial Extraction - Gate 1 requirements analysis
// Following canonical Response pattern
// Migrated: 2025-10-12 - Response pattern with metadata

// ==============================================================================
// TOP-LEVEL RESPONSE
// ==============================================================================

class InitialExtractionResponse {
  requirements Requirement[]
  metadata ResponseMetadata
  @@dynamic
}

// ==============================================================================
// DOMAIN ENTITY
// ==============================================================================

// Note: ResponseMetadata is imported from shared schema
