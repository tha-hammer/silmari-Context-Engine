// Tech Stack Selection - Gate 2 technology decisions
// Following canonical Response pattern
// Migrated: 2025-10-12 - Response pattern with metadata

// ==============================================================================
// TOP-LEVEL RESPONSE
// ==============================================================================

class TechStackResponse {
  tech_stack TechStackComponents
  metadata ResponseMetadata
  @@dynamic
}

// ==============================================================================
// DOMAIN ENTITY
// ==============================================================================

class TechStackComponents {
  frontend FrontendTechStack
  backend BackendTechStack
  database DatabaseTechStack
  language LanguageTechStack?
  infrastructure InfrastructureTechStack?
  dependencies string[]?
  third_party_packages string[]?
  @@dynamic
}

class BackendFeatures {
  middleware_patterns string[]?
  orm_usage string[]?
  api_patterns string[]?
  auth_strategies string[]?
  deployment_patterns string[]?
  @@dynamic
}

class BackendTechStack {
  framework string
  name string?
  version string?
  configuration string?
  specific_features BackendFeatures?
  @@dynamic
}

class BuildSystem {
  name string
  version string?
  configuration string?
  @@dynamic
}

class CloudProvider {
  provider string
  account_id string?
  region string?
  configuration string?
  @@dynamic
}

class DatabaseTechStack {
  type string?
  name string?
  version string?
  configuration string?
  schema_patterns string[]?
  @@dynamic
}

class DeploymentSystem {
  name string
  version string?
  configuration string?
  @@dynamic
}

class FrontendFeatures {
  jsx_patterns string[]?
  hooks_usage string[]?
  component_patterns string[]?
  store_usage string[]?
  routing_patterns string[]?
  @@dynamic
}

class FrontendTechStack {
  framework string
  name string?
  version string?
  configuration string?
  specific_features FrontendFeatures?
  @@dynamic
}

class InfrastructureTechStack {
  cloud CloudProvider?
  build BuildSystem?
  deploy DeploymentSystem?
  @@dynamic
}

class LanguageTechStack {
  name string
  version string?
  configuration string?
  specific_features string[]?
  @@dynamic
}

// Note: ResponseMetadata is imported from shared schema
