// BAML Type Definitions for Gate 1 Interactive Requirements Analysis

// ============================================================================
// GATE 1: INTERACTIVE REQUIREMENTS ANALYSIS - RESPONSE TYPES
// ============================================================================

// Initial Requirements Extraction Response
// MIGRATED: class InitialExtractionResponse {
//   requirements Requirement[]
// }

// MIGRATED: class Requirement {
//   description string
//   sub_processes string[]
//   related_concepts string[]
// }

// Gap Analysis Response
// MIGRATED: class GapAnalysisResponse {
//   gaps Gap[]
// }

// MIGRATED: class Gap {
//   description string
//   context string
//   suggestion string
// }

// Subprocess Analysis Response
// MIGRATED: class SubprocessAnalysisResponse {
//   implementation_details ImplementationDetail[]
// }

// MIGRATED: class ImplementationDetail {
//   function_id string
//   description string
//   related_concepts string[]
//   acceptance_criteria string[]
//   implementation ImplementationComponents
// }

// MIGRATED: class ImplementationComponents {
//   frontend string[]
//   backend string[]
//   middleware string[]
//   shared string[]
// }

// Category Analysis Response
// MIGRATED: class CategoryAnalysisResponse {
//   requirements Requirement[]
// }

// Requirement Expansion Response
// MIGRATED: class RequirementExpansionResponse {
//   children RequirementChild[]
// }

// MIGRATED: class RequirementChild {
//   description string
//   acceptance_criteria string[]
//   related_concepts string[]
//   implementation ImplementationComponents
// }

// Guided Search Response
// MIGRATED: class GuidedSearchResponse {
//   findings SearchFinding[]
// }

// MIGRATED: class SearchFinding {
//   description string
//   category string
//   confidence float
// }

// ============================================================================
// ADDITIONAL GATE 1 RESPONSE TYPES (10 missing types)
// ============================================================================

// Subprocess Details Analysis Response (RequirementsProcessor)
// MIGRATED: class SubprocessDetailsResponse {
//   implementation_details ImplementationDetail[]
// }

// Category-Specific Analysis Responses
// MIGRATED: class CategoryFunctionalResponse {
//   requirements Requirement[]
// }

// MIGRATED: class CategoryNonFunctionalResponse {
//   requirements Requirement[]
// }

// MIGRATED: class CategorySecurityResponse {
//   requirements Requirement[]
// }

// MIGRATED: class CategoryPerformanceResponse {
//   requirements Requirement[]
// }

// MIGRATED: class CategoryUsabilityResponse {
//   requirements Requirement[]
// }

// MIGRATED: class CategoryIntegrationResponse {
//   requirements Requirement[]
// }

// Expansion-Specific Response Types
// MIGRATED: class UserInteractionsResponse {
//   user_interactions UserInteraction[]
// }

// MIGRATED: class UserInteraction {
//   description string
//   acceptance_criteria string[]
//   related_concepts string[]
//   implementation ImplementationComponents
// }

// MIGRATED: class DataNeedsResponse {
//   data_needs DataNeed[]
// }

// MIGRATED: class DataNeed {
//   description string
//   acceptance_criteria string[]
//   related_concepts string[]
//   implementation ImplementationComponents
// }

// MIGRATED: class BusinessRulesResponse {
//   business_rules BusinessRule[]
// }

// MIGRATED: class BusinessRule {
//   description string
//   acceptance_criteria string[]
//   related_concepts string[]
//   implementation ImplementationComponents
// }

// ============================================================================
// GATE 1: MISSING TYPE DEFINITIONS
// ============================================================================

// MIGRATED: class RequirementValidationResponse {
//   validation_results ValidationResult[]
// }

// MIGRATED: class ValidationResult {
//   requirement_id string
//   component_name string?
//   is_valid bool
//   validation_issues string[]
//   suggestions string[]
//   confidence_score float?
// }

// MIGRATED: class RequirementPrioritizationResponse {
//   prioritized_requirements PrioritizedRequirement[]
// }

// MIGRATED: class PrioritizedRequirement {
//   requirement_id string
//   priority_level string
//   priority_score float
//   justification string
// }

// ============================================================================
// GATE 2: SCREEN FLOW CHAT - RESPONSE TYPES
// ============================================================================

// Screen Flow Chat Response
// MIGRATED: class ScreenFlowChatResponse {
//   message string
//   suggested_screens ScreenSuggestion[]
//   requirements_analysis RequirementsAnalysis
//   questions string[]
//   next_steps string[]
// }

// MIGRATED: class ScreenSuggestion {
//   id string
//   title string
//   route string
//   purpose string
//   requirements_addressed string[]
//   data_sources string[]
//   actions string[]
//   states string[]
//   layout_hints LayoutHints?
//   interaction_patterns InteractionPattern[]?
//   @@dynamic
// }

class RequirementsAnalysis {
  total_requirements int
  addressed_count int
  addressed_ids string[]
  remaining_ids string[]
  coverage_percentage float?
  coverage float?
}

// ============================================================================
// GATE 2: BAML DYNAMIC TYPES FOR TECH STACK AND SCREEN FLOW
// ============================================================================

// Tech Stack Response Types with Dynamic Capabilities
// MIGRATED: class TechStackResponse {
//   tech_stack TechStackComponents
//   confidence_score float
//   validation_results ValidationResult[]
//   decision_rationale string
//   alternatives_considered TechStackAlternative[]
//   @@dynamic
// }

// MIGRATED: class TechStackComponents {
//   frontend FrontendTechStack
//   backend BackendTechStack
//   database DatabaseTechStack
//   language LanguageTechStack?
//   infrastructure InfrastructureTechStack?
//   dependencies string[]?
//   third_party_packages string[]?
//   @@dynamic
// }

// MIGRATED: class FrontendTechStack {
//   framework string
//   name string?
//   version string?
//   configuration string?
//   specific_features FrontendFeatures?
//   @@dynamic
// }

// MIGRATED: class FrontendFeatures {
//   jsx_patterns string[]?
//   hooks_usage string[]?
//   component_patterns string[]?
//   store_usage string[]?
//   routing_patterns string[]?
//   @@dynamic
// }

// MIGRATED: class BackendTechStack {
//   framework string
//   name string?
//   version string?
//   configuration string?
//   specific_features BackendFeatures?
//   @@dynamic
// }

// MIGRATED: class BackendFeatures {
//   middleware_patterns string[]?
//   orm_usage string[]?
//   api_patterns string[]?
//   auth_strategies string[]?
//   deployment_patterns string[]?
//   @@dynamic
// }

// MIGRATED: class DatabaseTechStack {
//   type string?
//   name string?
//   version string?
//   configuration string?
//   schema_patterns string[]?
//   @@dynamic
// }

// MIGRATED: class LanguageTechStack {
//   name string
//   version string?
//   configuration string?
//   specific_features string[]?
//   @@dynamic
// }

// MIGRATED: class InfrastructureTechStack {
//   cloud CloudProvider?
//   build BuildSystem?
//   deploy DeploymentSystem?
//   @@dynamic
// }

// MIGRATED: class CloudProvider {
//   provider string
//   account_id string?
//   region string?
//   configuration string?
//   @@dynamic
// }

// MIGRATED: class BuildSystem {
//   name string
//   version string?
//   configuration string?
//   @@dynamic
// }

// MIGRATED: class DeploymentSystem {
//   name string
//   version string?
//   configuration string?
//   @@dynamic
// }

class TechStackAlternative {
  name string
  reason_not_chosen string
  pros_cons string[]
}

// Screen Flow Response Types with Dynamic Capabilities
// MIGRATED: class ScreenFlowResponse {
//   message string
//   suggested_screens ScreenSuggestion[]
//   requirements_analysis RequirementsAnalysis
//   questions string[]
//   next_steps string[]
//   navigation_patterns NavigationPattern[]
//   ui_patterns UIPattern[]
//   @@dynamic
// }

// MIGRATED: class LayoutHints {
//   layout_type string
//   grid_structure string?
//   responsive_breakpoints string[]?
//   accessibility_features string[]?
//   @@dynamic
// }

class InteractionPattern {
  pattern_type string
  description string
  implementation_hints string[]?
  @@dynamic
}

class NavigationPattern {
  pattern_type string
  from_screen string
  to_screen string
  trigger_condition string
  navigation_method string
  @@dynamic
}

class UIPattern {
  pattern_name string
  description string
  applicable_screens string[]
  implementation_guidance string[]
  framework_specific_notes string[]?
  @@dynamic
}


// Dynamic Container for Gate 2 Responses
class Gate2DynamicContainer {
  tech_stack_response TechStackResponse?
  metadata Gate2Metadata
  @@dynamic
}

class Gate2Metadata {
  processing_time_ms int
  llm_model_used string
  schema_version string
  dynamic_types_applied string[]
  fallback_used bool
}

// ============================================================================
// GATE 3: INTERFACE MAPPING - BAML DYNAMIC TYPES
// ============================================================================

// Main Interface Mapping Response - Service extraction format
// MIGRATED: class InterfaceMappingResponse {
//   service_extraction ServiceExtraction[]
//   patterns DesignPattern[]
//   organization OrganizationImprovement[]
//   shared_code_opportunities SharedCodeOpportunity[]
//   @@dynamic
// }

// Service Extraction - Concrete services to be extracted
// MIGRATED: class ServiceExtraction {
//   service_name string
//   description string
//   responsibilities string[]
//   dependencies string[]
//   methods string[]
//   related_requirements string[]
//   @@dynamic
// }

// Design Pattern - Applicable design patterns
class DesignPattern {
  pattern_name string
  description string
  application string
  implementation_areas string[]
  @@dynamic
}

// Organization Improvement - Architectural recommendations
class OrganizationImprovement {
  improvement string
  description string
  impact string
  @@dynamic
}

// Shared Code Opportunity - Code consolidation opportunities
class SharedCodeOpportunity {
  opportunity string
  description string
  benefits string
  @@dynamic
}

// Interface Analysis Types
class InterfaceAnalysis {
  total_interfaces int
  interface_complexity InterfaceComplexity
  integration_points IntegrationPoint[]
  data_flow_patterns DataFlowPattern[]
  @@dynamic
}

class InterfaceComplexity {
  simple_interfaces int
  moderate_interfaces int
  complex_interfaces int
  overall_complexity string
  @@dynamic
}

class IntegrationPoint {
  from_service string
  to_service string
  integration_type string
  data_format string?
  communication_pattern string?
  @@dynamic
}

class DataFlowPattern {
  pattern_name string
  description string
  involved_services string[]
  data_transformation_required bool
  @@dynamic
}

// Requirement Group Analysis (for interface mapping context)
class RequirementGroupAnalysis {
  group_id string
  group_name string
  primary_domain string
  requirements_count int
  complexity_assessment ComplexityAssessment
  mapping_confidence float
  @@dynamic
}

class ComplexityAssessment {
  technical_complexity string
  business_complexity string
  integration_complexity string
  overall_rating string
  risk_factors string[]?
  @@dynamic
}

// Dynamic Container for Gate 3 Responses
class Gate3DynamicContainer {
  interface_mapping_response InterfaceMappingResponse?
  requirement_group_analysis RequirementGroupAnalysis[]?
  metadata Gate3Metadata
  @@dynamic
}

class Gate3Metadata {
  processing_time_ms int
  llm_model_used string
  schema_version string
  dynamic_types_applied string[]
  groups_processed int
  requirements_analyzed int
  @@dynamic
}
