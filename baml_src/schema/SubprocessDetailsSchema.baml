// Subprocess Details - Gate 1 detailed subprocess analysis
// Following canonical Response pattern
// Migrated: 2025-10-12 - Response pattern with metadata

// ==============================================================================
// TOP-LEVEL RESPONSE
// ==============================================================================

class SubprocessDetailsResponse {
  implementation_details ImplementationDetail[]
  metadata ResponseMetadata
  @@dynamic
}

// ==============================================================================
// DOMAIN ENTITY
// ==============================================================================

// Note: ResponseMetadata is imported from shared schema
