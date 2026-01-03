// ============================================================================
// BAML SCHEMA INDEX - Auto-generated from JSON schema migration
// ============================================================================
// This file imports all migrated schemas for easy reference
// Generated on: 2025-09-30T20:45:46.099839

// Note: Core unified schemas were deleted - these are now in migrated_schemas

// Migrated schemas are auto-loaded from migrated_schemas/ directory
// No explicit imports needed - BAML automatically loads all .baml files in the project

// Schema registry for runtime access
class BAMLSchemaRegistry {
  gate_schemas map<string, string>
  component_schemas map<string, string>
  migration_date string
  total_schemas int
  @@dynamic
}
