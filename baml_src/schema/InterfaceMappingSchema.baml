// Gate 3: Function Mapping Response Schema
// Following API 2.0 Standard
// Migrated: 2025-10-14 - API 2.0 standardized structure

// ==============================================================================
// TOP-LEVEL RESPONSE (API 2.0 Standard)
// ==============================================================================

class Gate3FunctionMappingResponse {
  functions FunctionDefinition[]
  service_groups map<string, ServiceGroup>?
  interface_contracts map<string, InterfaceContract>?
  metadata ResponseMetadata
  @@dynamic
}

// ==============================================================================
// DOMAIN ENTITIES (API 2.0 Structure)
// ==============================================================================

class FunctionDefinition {
  function_id string
  function_name string
  description string?
  interfaces InterfaceReference[]?
  dependencies string[]?
  implementation_component string?
  acceptance_criteria_id string?
  @@dynamic
}

class InterfaceReference {
  interface_id string
  interface_type string?
  description string?
  @@dynamic
}

class ServiceGroup {
  group_id string
  group_name string?
  services string[]?
  shared_contracts string[]?
  @@dynamic
}

class InterfaceContract {
  contract_id string
  provider string?
  consumer string?
  methods ContractMethod[]?
  data_format string?
  @@dynamic
}

class ContractMethod {
  method_name string
  inputs map<string, string>?
  outputs map<string, string>?
  preconditions string[]?
  postconditions string[]?
  @@dynamic
}

// Legacy response for backward compatibility with v1
class InterfaceMappingResponse {
  functions FunctionDefinition[]
  service_groups map<string, ServiceGroup>?
  interface_contracts map<string, InterfaceContract>?
  metadata ResponseMetadata
  @@dynamic
}

// Note: ResponseMetadata is imported from FrontendCommonSchema.baml
