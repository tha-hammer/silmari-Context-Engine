"""Tests for property derivation and test skeleton generation.

Tests the property_generator module which analyzes acceptance criteria
and produces Hypothesis property-based test skeletons.
"""

import ast
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# =============================================================================
# Test Strategies
# =============================================================================


@st.composite
def _criterion_with_keyword(draw, keywords: list[str]) -> str:
    """Generate a criterion containing one of the keywords."""
    keyword = draw(st.sampled_from(keywords))
    prefix = draw(st.text(min_size=0, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))))
    suffix = draw(st.text(min_size=0, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Z"))))
    return f"{prefix} {keyword} {suffix}".strip()


# =============================================================================
# Tests for PropertyType
# =============================================================================


class TestPropertyType:
    """Tests for PropertyType enum."""

    def test_invariant_exists(self):
        """PropertyType.INVARIANT should exist."""
        from planning_pipeline.property_generator import PropertyType

        assert PropertyType.INVARIANT.value == "invariant"

    def test_round_trip_exists(self):
        """PropertyType.ROUND_TRIP should exist."""
        from planning_pipeline.property_generator import PropertyType

        assert PropertyType.ROUND_TRIP.value == "round_trip"

    def test_idempotence_exists(self):
        """PropertyType.IDEMPOTENCE should exist."""
        from planning_pipeline.property_generator import PropertyType

        assert PropertyType.IDEMPOTENCE.value == "idempotence"

    def test_oracle_exists(self):
        """PropertyType.ORACLE should exist."""
        from planning_pipeline.property_generator import PropertyType

        assert PropertyType.ORACLE.value == "oracle"


# =============================================================================
# Tests for derive_properties
# =============================================================================


class TestDeriveProperties:
    """Tests for derive_properties function."""

    def test_empty_criteria_returns_empty(self):
        """Empty criteria list should return empty properties list."""
        from planning_pipeline.property_generator import derive_properties

        result = derive_properties([])
        assert result == []

    def test_uniqueness_criterion_produces_invariant(self):
        """Uniqueness criterion should produce invariant property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Must validate agent_id uniqueness"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.INVARIANT.value

    def test_distinct_criterion_produces_invariant(self):
        """Distinct criterion should produce invariant property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["All IDs must be distinct"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.INVARIANT.value

    def test_no_duplicate_criterion_produces_invariant(self):
        """No duplicate criterion should produce invariant property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["No duplicate entries allowed"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.INVARIANT.value

    def test_not_empty_criterion_produces_invariant(self):
        """Not empty criterion should produce invariant property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Result must not be empty"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.INVARIANT.value

    def test_state_criterion_produces_invariant(self):
        """State criterion should produce invariant property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["State must be valid after operation"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.INVARIANT.value

    def test_save_load_criterion_produces_round_trip(self):
        """Save/load criterion should produce round_trip property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Data must be preserved after save and load"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.ROUND_TRIP.value

    def test_serialize_criterion_produces_round_trip(self):
        """Serialize criterion should produce round_trip property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Object must serialize correctly"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.ROUND_TRIP.value

    def test_preserved_criterion_produces_round_trip(self):
        """Preserved criterion should produce round_trip property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Session data must be preserved after save/load"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.ROUND_TRIP.value

    def test_idempotent_criterion_produces_idempotence(self):
        """Idempotent criterion should produce idempotence property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Operation should be idempotent"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.IDEMPOTENCE.value

    def test_twice_criterion_produces_idempotence(self):
        """Twice criterion should produce idempotence property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Applying twice should give same result"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.IDEMPOTENCE.value

    def test_sorted_criterion_produces_idempotence(self):
        """Sorted criterion should produce idempotence property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Output must be sorted"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.IDEMPOTENCE.value

    def test_reference_criterion_produces_oracle(self):
        """Reference criterion should produce oracle property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Output must match reference implementation"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.ORACLE.value

    def test_oracle_criterion_produces_oracle(self):
        """Oracle criterion should produce oracle property type."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Use oracle to verify correctness"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.ORACLE.value

    def test_unknown_criterion_defaults_to_invariant(self):
        """Unknown criterion pattern should default to invariant."""
        from planning_pipeline.property_generator import derive_properties, PropertyType

        criteria = ["Some random requirement without keywords"]
        result = derive_properties(criteria)

        assert len(result) == 1
        assert result[0].property_type == PropertyType.INVARIANT.value

    def test_multiple_criteria_returns_multiple_properties(self):
        """Multiple criteria should return multiple properties."""
        from planning_pipeline.property_generator import derive_properties

        criteria = [
            "Must validate agent_id uniqueness",
            "Session data must be preserved after save/load",
            "Operation should be idempotent",
        ]
        result = derive_properties(criteria)

        assert len(result) == 3

    def test_criterion_text_preserved(self):
        """Criterion text should be preserved in property."""
        from planning_pipeline.property_generator import derive_properties

        criteria = ["Must validate agent_id uniqueness"]
        result = derive_properties(criteria)

        assert result[0].criterion == "Must validate agent_id uniqueness"

    def test_hypothesis_strategy_is_set(self):
        """Hypothesis strategy should be set based on property type."""
        from planning_pipeline.property_generator import derive_properties

        criteria = ["Must validate agent_id uniqueness"]
        result = derive_properties(criteria)

        assert result[0].hypothesis_strategy is not None
        assert len(result[0].hypothesis_strategy) > 0
        assert "st." in result[0].hypothesis_strategy


# =============================================================================
# Tests for generate_test_skeleton
# =============================================================================


class TestGenerateTestSkeleton:
    """Tests for generate_test_skeleton function."""

    def test_generates_valid_python(self):
        """Generated skeleton should be valid Python code."""
        from planning_pipeline.property_generator import derive_properties, generate_test_skeleton

        criteria = ["Must validate agent_id uniqueness"]
        props = derive_properties(criteria)
        skeleton = generate_test_skeleton(props[0], class_name="SessionManager")

        # Should parse without SyntaxError
        ast.parse(skeleton)

    def test_includes_hypothesis_decorator(self):
        """Generated skeleton should include @given decorator."""
        from planning_pipeline.property_generator import derive_properties, generate_test_skeleton

        criteria = ["Must validate agent_id uniqueness"]
        props = derive_properties(criteria)
        skeleton = generate_test_skeleton(props[0], class_name="SessionManager")

        assert "@given" in skeleton

    def test_includes_class_under_test(self):
        """Generated skeleton should reference the class under test."""
        from planning_pipeline.property_generator import derive_properties, generate_test_skeleton

        criteria = ["Must validate agent_id uniqueness"]
        props = derive_properties(criteria)
        skeleton = generate_test_skeleton(props[0], class_name="SessionManager")

        assert "SessionManager" in skeleton

    def test_includes_method_name_with_criterion(self):
        """Generated method name should include sanitized criterion text."""
        from planning_pipeline.property_generator import derive_properties, generate_test_skeleton

        criteria = ["Must validate agent_id uniqueness"]
        props = derive_properties(criteria)
        skeleton = generate_test_skeleton(props[0], class_name="SessionManager")

        assert "def test_" in skeleton

    def test_includes_docstring(self):
        """Generated skeleton should include docstring with criterion."""
        from planning_pipeline.property_generator import derive_properties, generate_test_skeleton

        criteria = ["Must validate agent_id uniqueness"]
        props = derive_properties(criteria)
        skeleton = generate_test_skeleton(props[0], class_name="SessionManager")

        assert '"""' in skeleton or "'''" in skeleton

    def test_includes_todo_comment(self):
        """Generated skeleton should include TODO comment for implementation."""
        from planning_pipeline.property_generator import derive_properties, generate_test_skeleton

        criteria = ["Must validate agent_id uniqueness"]
        props = derive_properties(criteria)
        skeleton = generate_test_skeleton(props[0], class_name="SessionManager")

        assert "TODO" in skeleton

    def test_includes_assertion(self):
        """Generated skeleton should include a placeholder assertion."""
        from planning_pipeline.property_generator import derive_properties, generate_test_skeleton

        criteria = ["Must validate agent_id uniqueness"]
        props = derive_properties(criteria)
        skeleton = generate_test_skeleton(props[0], class_name="SessionManager")

        assert "assert" in skeleton

    def test_round_trip_skeleton_has_encode_decode_structure(self):
        """Round trip skeleton should include encode/decode or save/load structure."""
        from planning_pipeline.property_generator import derive_properties, generate_test_skeleton

        criteria = ["Session data must be preserved after save/load"]
        props = derive_properties(criteria)
        skeleton = generate_test_skeleton(props[0], class_name="SessionManager")

        # Should have comments or structure indicating round-trip
        assert "round" in skeleton.lower() or "encode" in skeleton.lower() or "serialize" in skeleton.lower() or "save" in skeleton.lower()

    def test_idempotence_skeleton_has_twice_structure(self):
        """Idempotence skeleton should include double-application structure."""
        from planning_pipeline.property_generator import derive_properties, generate_test_skeleton

        criteria = ["Operation should be idempotent"]
        props = derive_properties(criteria)
        skeleton = generate_test_skeleton(props[0], class_name="Processor")

        # Should have comments or structure indicating idempotence
        assert "twice" in skeleton.lower() or "idempot" in skeleton.lower() or "same" in skeleton.lower()


# =============================================================================
# Tests for generate_full_test_file
# =============================================================================


class TestGenerateFullTestFile:
    """Tests for generate_full_test_file function."""

    def test_generates_valid_python_module(self):
        """Generated file should be a valid Python module."""
        from planning_pipeline.property_generator import derive_properties, generate_full_test_file

        criteria = [
            "Must validate agent_id uniqueness",
            "Session data must be preserved after save/load",
        ]
        props = derive_properties(criteria)
        test_file = generate_full_test_file(props, class_name="SessionManager", module_path="planning_pipeline.session")

        # Should parse without SyntaxError
        ast.parse(test_file)

    def test_includes_imports(self):
        """Generated file should include necessary imports."""
        from planning_pipeline.property_generator import derive_properties, generate_full_test_file

        criteria = ["Must validate agent_id uniqueness"]
        props = derive_properties(criteria)
        test_file = generate_full_test_file(props, class_name="SessionManager", module_path="planning_pipeline.session")

        assert "import pytest" in test_file
        assert "from hypothesis" in test_file
        assert "import" in test_file and "hypothesis" in test_file

    def test_includes_module_import(self):
        """Generated file should import the module under test."""
        from planning_pipeline.property_generator import derive_properties, generate_full_test_file

        criteria = ["Must validate agent_id uniqueness"]
        props = derive_properties(criteria)
        test_file = generate_full_test_file(props, class_name="SessionManager", module_path="planning_pipeline.session")

        assert "planning_pipeline.session" in test_file

    def test_includes_all_test_methods(self):
        """Generated file should include test methods for all properties."""
        from planning_pipeline.property_generator import derive_properties, generate_full_test_file

        criteria = [
            "Must validate agent_id uniqueness",
            "Session data must be preserved after save/load",
            "Operation should be idempotent",
        ]
        props = derive_properties(criteria)
        test_file = generate_full_test_file(props, class_name="SessionManager", module_path="planning_pipeline.session")

        # Count test methods (each starts with "def test_")
        test_count = test_file.count("def test_")
        assert test_count >= 3

    def test_empty_properties_generates_empty_test_class(self):
        """Empty properties should generate file with empty test class."""
        from planning_pipeline.property_generator import generate_full_test_file

        test_file = generate_full_test_file([], class_name="SessionManager", module_path="planning_pipeline.session")

        # Should still be valid Python
        ast.parse(test_file)

        # Should have imports but minimal test methods
        assert "import pytest" in test_file


# =============================================================================
# Parametrized tests for criterion classification
# =============================================================================


class TestPropertyTypeClassification:
    """Parametrized tests for criterion to property type classification."""

    @pytest.mark.parametrize(
        "criterion,expected_type",
        [
            # Invariant patterns
            ("Must validate unique IDs", "invariant"),
            ("All values distinct", "invariant"),
            ("No duplicate entries", "invariant"),
            ("Result not empty", "invariant"),
            ("Non-empty list required", "invariant"),
            ("Has content", "invariant"),
            ("State valid", "invariant"),
            ("Status must be active", "invariant"),
            # Round-trip patterns
            ("Save and load preserves data", "round_trip"),
            ("Encode and decode correctly", "round_trip"),
            ("Serialize to JSON", "round_trip"),
            ("Round-trip through dict", "round_trip"),
            ("Data preserved after storage", "round_trip"),
            ("Value unchanged after processing", "round_trip"),
            ("Maintains original value", "round_trip"),
            # Idempotence patterns
            ("Applying twice gives same result", "idempotence"),
            ("Multiple times same output", "idempotence"),
            ("Idempotent operation", "idempotence"),
            ("Same result on retry", "idempotence"),
            ("Output sorted correctly", "idempotence"),
            ("Ordered list returned", "idempotence"),
            ("Stable sort", "idempotence"),
            # Oracle patterns
            ("Matches reference implementation", "oracle"),
            ("Compare to oracle", "oracle"),
            ("Equals expected output", "oracle"),
        ],
    )
    def test_criterion_classified_correctly(self, criterion, expected_type):
        """Criterion should be classified to expected property type."""
        from planning_pipeline.property_generator import derive_properties

        result = derive_properties([criterion])

        assert len(result) == 1
        assert result[0].property_type == expected_type, (
            f"Criterion '{criterion}' classified as '{result[0].property_type}', "
            f"expected '{expected_type}'"
        )


# =============================================================================
# Property-based tests
# =============================================================================


class TestPropertyBasedDeriveProperties:
    """Property-based tests for derive_properties."""

    @given(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=10))
    @settings(max_examples=50)
    def test_returns_same_length_as_input(self, criteria):
        """derive_properties should return one property per criterion."""
        from planning_pipeline.property_generator import derive_properties

        result = derive_properties(criteria)
        assert len(result) == len(criteria)

    @given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5))
    @settings(max_examples=50)
    def test_all_properties_have_valid_type(self, criteria):
        """All derived properties should have valid property type."""
        from planning_pipeline.property_generator import derive_properties

        valid_types = {"invariant", "round_trip", "idempotence", "oracle"}
        result = derive_properties(criteria)

        for prop in result:
            assert prop.property_type in valid_types

    @given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5))
    @settings(max_examples=50)
    def test_all_properties_have_hypothesis_strategy(self, criteria):
        """All derived properties should have a hypothesis strategy."""
        from planning_pipeline.property_generator import derive_properties

        result = derive_properties(criteria)

        for prop in result:
            assert prop.hypothesis_strategy is not None
            assert len(prop.hypothesis_strategy) > 0

    @given(_criterion_with_keyword(["unique", "distinct", "no duplicate"]))
    @settings(max_examples=30)
    def test_invariant_keywords_produce_invariant(self, criterion):
        """Criteria with invariant keywords should produce invariant type."""
        from planning_pipeline.property_generator import derive_properties

        result = derive_properties([criterion])
        assert result[0].property_type == "invariant"

    @given(_criterion_with_keyword(["serialize", "preserved", "unchanged", "round-trip", "maintains"]))
    @settings(max_examples=30)
    def test_round_trip_keywords_produce_round_trip(self, criterion):
        """Criteria with round-trip keywords should produce round_trip type."""
        from planning_pipeline.property_generator import derive_properties

        result = derive_properties([criterion])
        assert result[0].property_type == "round_trip"
