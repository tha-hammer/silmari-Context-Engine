// Shared classes for Gate1 and other Response schemas
// Following canonical Response pattern
// Created: 2025-10-12

// ==============================================================================
// SHARED CLASSES USED BY MULTIPLE SCHEMAS
// ==============================================================================

// Used by: InitialExtraction, CategoryAnalysis, Category* responses
class Requirement {
  description string
  sub_processes string[]
  related_concepts string[]
}

// Used by: SubprocessAnalysis, SubprocessDetails
class ImplementationDetail {
  function_id string
  description string
  related_concepts string[]
  acceptance_criteria string[]
  implementation ImplementationComponents
}

// Used by: Multiple implementation-related schemas
class ImplementationComponents {
  frontend string[]
  backend string[]
  middleware string[]
  shared string[]
}

// Used by: GapAnalysis
class Gap {
  description string
  context string
  suggestion string
}

// Used by: RequirementExpansion
class RequirementChild {
  description string
  acceptance_criteria string[]
  related_concepts string[]
  implementation ImplementationComponents
}

// Used by: GuidedSearch
class SearchFinding {
  description string
  category string
  confidence float
}

// Used by: UserInteractions
class UserInteraction {
  description string
  acceptance_criteria string[]
  related_concepts string[]
  implementation ImplementationComponents
}

// Used by: DataNeeds
class DataNeed {
  description string
  acceptance_criteria string[]
  related_concepts string[]
  implementation ImplementationComponents
}

// Used by: BusinessRules
class BusinessRule {
  description string
  acceptance_criteria string[]
  related_concepts string[]
  implementation ImplementationComponents
}

// Used by: RequirementValidation
class ValidationResult {
  requirement_id string
  component_name string?
  is_valid bool
  validation_issues string[]
  suggestions string[]
  confidence_score float?
}

// Used by: RequirementPrioritization
class PrioritizedRequirement {
  requirement_id string
  priority_level string
  priority_score float
  justification string
}

// Used by: ScreenFlow, ScreenFlowChat
class ScreenSuggestion {
  id string
  title string
  route string
  purpose string
  requirements_addressed string[]
  data_sources string[]
  actions string[]
  layout_hints LayoutHints?
  priority int?
  dependencies string[]?
  error_handling string[]?
  @@dynamic
}

class LayoutHints {
  layout_type string
  grid_structure string?
  responsive_breakpoints string[]?
  accessibility_features string[]?
  @@dynamic
}

// Used by: InterfaceMapping
class ServiceExtraction {
  service_name string
  description string
  responsibilities string[]
  dependencies string[]
  methods string[]
  related_requirements string[]
  @@dynamic
}

