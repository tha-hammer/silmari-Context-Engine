"""Property derivation and test skeleton generation from acceptance criteria.

This module provides functions to:
1. Analyze acceptance criteria strings and derive testable properties
2. Generate Hypothesis test skeletons for each property
3. Generate complete test files with imports and class structure

Property types correspond to common testing patterns:
- invariant: State validity, uniqueness constraints
- round_trip: Serialization/deserialization, encode/decode
- idempotence: Operations that produce same result when applied multiple times
- oracle: Comparison against reference implementation
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from planning_pipeline.models import TestableProperty


class PropertyType(Enum):
    """Types of properties that can be derived from acceptance criteria."""

    INVARIANT = "invariant"
    ROUND_TRIP = "round_trip"
    IDEMPOTENCE = "idempotence"
    ORACLE = "oracle"


@dataclass
class PropertyPattern:
    """Pattern for matching criteria to property types."""

    regex: str
    property_type: PropertyType
    default_strategy: str


# Patterns for classifying acceptance criteria into property types
# Order matters - first match wins
PROPERTY_PATTERNS: list[PropertyPattern] = [
    # Round-trip patterns (check first because "preserved" is common)
    PropertyPattern(
        regex=r"save.*load|load.*save|encode.*decode|decode.*encode|serialize|round.?trip",
        property_type=PropertyType.ROUND_TRIP,
        default_strategy="st.text()",
    ),
    PropertyPattern(
        regex=r"preserved|unchanged|maintains",
        property_type=PropertyType.ROUND_TRIP,
        default_strategy="st.text()",
    ),
    # Idempotence patterns
    PropertyPattern(
        regex=r"twice|multiple times|idempotent|same result",
        property_type=PropertyType.IDEMPOTENCE,
        default_strategy="st.lists(st.integers())",
    ),
    PropertyPattern(
        regex=r"sorted|ordered|stable",
        property_type=PropertyType.IDEMPOTENCE,
        default_strategy="st.lists(st.integers())",
    ),
    # Oracle patterns
    PropertyPattern(
        regex=r"reference|oracle|matches|equals",
        property_type=PropertyType.ORACLE,
        default_strategy="st.text()",
    ),
    # Invariant patterns (most common, check last as fallback)
    PropertyPattern(
        regex=r"unique|distinct|no duplicate",
        property_type=PropertyType.INVARIANT,
        default_strategy="st.text(min_size=1)",
    ),
    PropertyPattern(
        regex=r"not empty|non.?empty|has content",
        property_type=PropertyType.INVARIANT,
        default_strategy="st.text(min_size=1)",
    ),
    PropertyPattern(
        regex=r"state|status|must be|valid",
        property_type=PropertyType.INVARIANT,
        default_strategy="st.sampled_from([])",
    ),
]


def _match_criterion_to_pattern(criterion: str) -> tuple[PropertyType, str]:
    """Match a criterion to a property pattern.

    Args:
        criterion: The acceptance criterion text

    Returns:
        Tuple of (property_type, hypothesis_strategy)
    """
    criterion_lower = criterion.lower()

    for pattern in PROPERTY_PATTERNS:
        if re.search(pattern.regex, criterion_lower):
            return pattern.property_type, pattern.default_strategy

    # Default to invariant if no pattern matches
    return PropertyType.INVARIANT, "st.text()"


def _sanitize_method_name(text: str, max_length: int = 30) -> str:
    """Convert criterion text to a valid Python method name suffix.

    Args:
        text: The text to sanitize
        max_length: Maximum length of the result

    Returns:
        Sanitized string suitable for use in a method name
    """
    # Replace non-alphanumeric with underscore
    sanitized = re.sub(r"[^a-zA-Z0-9]", "_", text.lower())
    # Collapse multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")
    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip("_")
    return sanitized


def derive_properties(criteria: list[str]) -> list[TestableProperty]:
    """Derive testable properties from acceptance criteria strings.

    Analyzes each criterion and determines the appropriate property type
    and Hypothesis strategy based on pattern matching.

    Args:
        criteria: List of acceptance criterion strings

    Returns:
        List of TestableProperty objects with property_type, hypothesis_strategy,
        and a basic test_skeleton for each criterion
    """
    properties: list[TestableProperty] = []

    for criterion in criteria:
        property_type, strategy = _match_criterion_to_pattern(criterion)

        # Generate a basic skeleton (will be expanded by generate_test_skeleton)
        method_name = _sanitize_method_name(criterion)
        skeleton = f"@given({strategy})\ndef test_property_{method_name}(self, value): ..."

        prop = TestableProperty(
            criterion=criterion,
            property_type=property_type.value,
            hypothesis_strategy=strategy,
            test_skeleton=skeleton,
        )
        properties.append(prop)

    return properties


def generate_test_skeleton(prop: TestableProperty, class_name: str) -> str:
    """Generate a Hypothesis test skeleton for a single property.

    Creates a complete test method with:
    - @given decorator with appropriate strategy
    - Method name derived from criterion
    - Docstring with original criterion
    - TODO comment with guidance based on property type
    - Placeholder assertion

    Args:
        prop: The TestableProperty to generate a skeleton for
        class_name: Name of the class being tested

    Returns:
        String containing valid Python test method code
    """
    method_name = _sanitize_method_name(prop.criterion)
    strategy = prop.hypothesis_strategy
    property_type = prop.property_type

    # Generate type-specific skeleton structure
    if property_type == PropertyType.ROUND_TRIP.value:
        body = f'''@given({strategy})
def test_property_{method_name}(self, value):
    """Property: {prop.criterion}"""
    instance = {class_name}()
    # TODO: Implement round-trip check
    # Given: original value
    # When: serialize then deserialize (or save then load)
    # Then: result equals original
    # Example:
    #   serialized = instance.serialize(value)
    #   restored = instance.deserialize(serialized)
    #   assert restored == value
    assert True  # Replace with actual assertion'''

    elif property_type == PropertyType.IDEMPOTENCE.value:
        body = f'''@given({strategy})
def test_property_{method_name}(self, value):
    """Property: {prop.criterion}"""
    instance = {class_name}()
    # TODO: Implement idempotence check
    # Given: input value
    # When: apply operation twice
    # Then: same result as applying once
    # Example:
    #   result_once = instance.operation(value)
    #   result_twice = instance.operation(instance.operation(value))
    #   assert result_once == result_twice
    assert True  # Replace with actual assertion'''

    elif property_type == PropertyType.ORACLE.value:
        body = f'''@given({strategy})
def test_property_{method_name}(self, value):
    """Property: {prop.criterion}"""
    instance = {class_name}()
    # TODO: Implement oracle check
    # Given: input value
    # When: compute result
    # Then: matches reference implementation
    # Example:
    #   result = instance.compute(value)
    #   expected = reference_implementation(value)
    #   assert result == expected
    assert True  # Replace with actual assertion'''

    else:  # INVARIANT (default)
        body = f'''@given({strategy})
def test_property_{method_name}(self, value):
    """Property: {prop.criterion}"""
    instance = {class_name}()
    # TODO: Implement invariant check
    # Given: instance with value
    # When: operation performed
    # Then: invariant holds
    # Example:
    #   instance.add(value)
    #   assert instance.is_valid()
    assert True  # Replace with actual assertion'''

    return body


def generate_full_test_file(
    properties: list[TestableProperty],
    class_name: str,
    module_path: str,
) -> str:
    """Generate a complete test file with imports and all property tests.

    Creates a full Python test module including:
    - Standard imports (pytest, hypothesis)
    - Module under test import
    - Test class with all property-based test methods

    Args:
        properties: List of TestableProperty objects to generate tests for
        class_name: Name of the class being tested
        module_path: Import path for the module under test (e.g., "planning_pipeline.session")

    Returns:
        String containing valid Python test file content
    """
    # Build imports section
    imports = f'''"""Property-based tests for {class_name}.

Auto-generated test skeletons derived from acceptance criteria.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from {module_path} import {class_name}

'''

    # Build test class
    test_class = f'''class Test{class_name}Properties:
    """Property-based tests for {class_name}."""

'''

    # Add test methods
    if not properties:
        test_class += "    pass\n"
    else:
        for prop in properties:
            skeleton = generate_test_skeleton(prop, class_name)
            # Indent the skeleton to fit inside the class
            indented = "\n".join(
                "    " + line if line.strip() else line
                for line in skeleton.split("\n")
            )
            test_class += indented + "\n\n"

    return imports + test_class
