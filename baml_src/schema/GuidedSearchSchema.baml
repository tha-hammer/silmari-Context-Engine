// Guided Search - Gate 1 guided search findings
// Following canonical Response pattern
// Migrated: 2025-10-12 - Response pattern with metadata

// ==============================================================================
// TOP-LEVEL RESPONSE
// ==============================================================================

class GuidedSearchResponse {
  findings SearchFinding[]
  metadata ResponseMetadata
  @@dynamic
}

// ==============================================================================
// DOMAIN ENTITY
// ==============================================================================

// Note: ResponseMetadata is imported from shared schema
