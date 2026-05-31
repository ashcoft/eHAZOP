"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.risk import (
    RiskMatrixBase,
    RiskMatrixCreate,
    RiskMatrixOverrideBase,
    RiskMatrixOverrideCreate,
    RiskScoreRequest,
)


class TestRiskMatrixBase:
    """Tests for RiskMatrixBase schema."""

    def test_valid_minimal_data(self):
        """Test with minimal valid data."""
        schema = RiskMatrixBase(name="Test Matrix")
        assert schema.name == "Test Matrix"
        assert schema.description is None
        assert schema.study_type is None

    def test_valid_full_data(self):
        """Test with full valid data."""
        schema = RiskMatrixBase(
            name="Test Matrix",
            description="A test risk matrix",
            study_type="EHAZOP",
        )
        assert schema.name == "Test Matrix"
        assert schema.description == "A test risk matrix"
        assert schema.study_type == "EHAZOP"

    def test_default_categories(self):
        """Test default categories."""
        schema = RiskMatrixBase(name="Test")
        assert schema.categories == ["People", "Asset", "Environment", "Reputation"]

    def test_custom_categories(self):
        """Test custom categories."""
        schema = RiskMatrixBase(
            name="Test",
            categories=["Safety", "Environment"],
        )
        assert schema.categories == ["Safety", "Environment"]

    def test_empty_name_invalid(self):
        """Empty name should be invalid."""
        with pytest.raises(ValidationError):
            RiskMatrixBase(name="")

    def test_name_too_long(self):
        """Name exceeding max length should be invalid."""
        with pytest.raises(ValidationError):
            RiskMatrixBase(name="x" * 256)


class TestRiskMatrixCreate:
    """Tests for RiskMatrixCreate schema."""

    def test_valid_create(self):
        """Test valid creation."""
        schema = RiskMatrixCreate(name="New Matrix")
        assert schema.name == "New Matrix"
        assert schema.is_default is False

    def test_with_matrix_data(self):
        """Test with matrix data."""
        matrix_data = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
        schema = RiskMatrixCreate(
            name="Test",
            matrix_data=matrix_data,
        )
        assert schema.matrix_data == matrix_data

    def test_with_scales(self):
        """Test with scales."""
        severity_scale = [
            {"level": 1, "name": "Minor", "description": "Minor impact"},
        ]
        schema = RiskMatrixCreate(
            name="Test",
            severity_scale=severity_scale,
        )
        assert len(schema.severity_scale) == 1

    def test_default_is_false(self):
        """Test default is_default is False."""
        schema = RiskMatrixCreate(name="Test")
        assert schema.is_default is False

    def test_is_default_can_be_true(self):
        """Test is_default can be True."""
        schema = RiskMatrixCreate(name="Test", is_default=True)
        assert schema.is_default is True


class TestRiskMatrixOverrideBase:
    """Tests for RiskMatrixOverrideBase schema."""

    def test_valid_override(self):
        """Test valid override."""
        schema = RiskMatrixOverrideBase(
            severity=3,
            likelihood="C",
            new_score=12,
        )
        assert schema.severity == 3
        assert schema.likelihood == "C"
        assert schema.new_score == 12

    def test_with_optional_fields(self):
        """Test with optional fields."""
        schema = RiskMatrixOverrideBase(
            severity=4,
            likelihood="D",
            new_score=20,
            new_band="Very High",
            reason="Site specific",
        )
        assert schema.new_band == "Very High"
        assert schema.reason == "Site specific"

    def test_severity_minimum(self):
        """Test severity minimum boundary."""
        schema = RiskMatrixOverrideBase(
            severity=1,
            likelihood="A",
            new_score=1,
        )
        assert schema.severity == 1

    def test_severity_maximum(self):
        """Test severity maximum boundary."""
        schema = RiskMatrixOverrideBase(
            severity=5,
            likelihood="E",
            new_score=25,
        )
        assert schema.severity == 5

    def test_severity_too_low(self):
        """Severity below minimum should be invalid."""
        with pytest.raises(ValidationError):
            RiskMatrixOverrideBase(
                severity=0,
                likelihood="A",
                new_score=0,
            )

    def test_severity_too_high(self):
        """Severity above maximum should be invalid."""
        with pytest.raises(ValidationError):
            RiskMatrixOverrideBase(
                severity=6,
                likelihood="A",
                new_score=0,
            )

    def test_likelihood_valid_values(self):
        """Test valid likelihood values."""
        for letter in ["A", "B", "C", "D", "E"]:
            schema = RiskMatrixOverrideBase(
                severity=1,
                likelihood=letter,
                new_score=1,
            )
            assert schema.likelihood == letter

    def test_likelihood_too_long(self):
        """Likelihood with more than one char should be invalid."""
        with pytest.raises(ValidationError):
            RiskMatrixOverrideBase(
                severity=1,
                likelihood="AB",
                new_score=1,
            )

    def test_new_score_minimum(self):
        """Test new_score minimum boundary."""
        schema = RiskMatrixOverrideBase(
            severity=1,
            likelihood="A",
            new_score=0,
        )
        assert schema.new_score == 0


class TestRiskMatrixOverrideCreate:
    """Tests for RiskMatrixOverrideCreate schema."""

    def test_valid_create(self):
        """Test valid creation."""
        schema = RiskMatrixOverrideCreate(
            matrix_id="matrix-123",
            severity=3,
            likelihood="C",
            new_score=12,
        )
        assert schema.matrix_id == "matrix-123"

    def test_with_study_id(self):
        """Test with study_id."""
        schema = RiskMatrixOverrideCreate(
            matrix_id="matrix-123",
            study_id="study-456",
            severity=3,
            likelihood="C",
            new_score=12,
        )
        assert schema.study_id == "study-456"

    def test_study_id_optional(self):
        """Test study_id is optional."""
        schema = RiskMatrixOverrideCreate(
            matrix_id="matrix-123",
            severity=3,
            likelihood="C",
            new_score=12,
        )
        assert schema.study_id is None


class TestRiskScoreRequest:
    """Tests for RiskScoreRequest schema."""

    def test_valid_request(self):
        """Test valid request."""
        schema = RiskScoreRequest(
            severity=3,
            likelihood="C",
        )
        assert schema.severity == 3
        assert schema.likelihood == "C"
        assert schema.matrix_id is None

    def test_with_matrix_id(self):
        """Test with matrix_id."""
        schema = RiskScoreRequest(
            severity=3,
            likelihood="C",
            matrix_id="matrix-123",
        )
        assert schema.matrix_id == "matrix-123"

    def test_severity_boundaries(self):
        """Test severity boundaries."""
        # Minimum
        schema = RiskScoreRequest(severity=1, likelihood="A")
        assert schema.severity == 1

        # Maximum
        schema = RiskScoreRequest(severity=5, likelihood="E")
        assert schema.severity == 5

    def test_severity_too_low(self):
        """Severity below minimum should be invalid."""
        with pytest.raises(ValidationError):
            RiskScoreRequest(severity=0, likelihood="A")

    def test_severity_too_high(self):
        """Severity above maximum should be invalid."""
        with pytest.raises(ValidationError):
            RiskScoreRequest(severity=6, likelihood="A")

    def test_likelihood_valid_values(self):
        """Test valid likelihood values."""
        for letter in ["A", "B", "C", "D", "E"]:
            schema = RiskScoreRequest(severity=1, likelihood=letter)
            assert schema.likelihood == letter

    def test_likelihood_invalid(self):
        """Invalid likelihood should be invalid."""
        with pytest.raises(ValidationError):
            RiskScoreRequest(severity=1, likelihood="F")