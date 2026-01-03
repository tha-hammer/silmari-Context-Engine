// DataNeeds Response
// Following canonical Response pattern
// Migrated: 2025-10-12 - Response pattern with metadata

// ==============================================================================
// TOP-LEVEL RESPONSE
// ==============================================================================

class DataNeedsResponse {
  data_needs DataNeed[]
  metadata ResponseMetadata
  @@dynamic
}

// ==============================================================================
// DOMAIN ENTITY
// ==============================================================================

// Note: DataNeed and supporting classes are defined in Gate1SharedClasses.baml
// Note: ResponseMetadata is imported from shared schema
