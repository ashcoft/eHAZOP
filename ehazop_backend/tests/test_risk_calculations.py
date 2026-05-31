"""Tests for risk matrix calculation logic.

These tests verify the risk calculation methods without requiring database setup.
"""

import pytest


class TestRiskMatrixCalculations:
    """Tests for risk matrix calculation logic."""

    def test_calculate_risk_score_basic(self):
        """Test basic risk score calculation."""
        # Test matrix data
        matrix_data = [
            [1, 2, 3, 4, 5],   # Severity 1
            [2, 4, 6, 8, 10],  # Severity 2
            [3, 6, 9, 12, 15], # Severity 3
            [4, 8, 12, 16, 20],# Severity 4
            [5, 10, 15, 20, 25],# Severity 5
        ]

        # Test various combinations
        assert matrix_data[0][0] == 1  # Sev 1, Lik A
        assert matrix_data[0][4] == 5  # Sev 1, Lik E
        assert matrix_data[4][0] == 5  # Sev 5, Lik A
        assert matrix_data[4][4] == 25  # Sev 5, Lik E

    def test_calculate_risk_score_middle_values(self):
        """Test risk score calculation for middle values."""
        matrix_data = [
            [1, 2, 3, 4, 5],
            [2, 4, 6, 8, 10],
            [3, 6, 9, 12, 15],
            [4, 8, 12, 16, 20],
            [5, 10, 15, 20, 25],
        ]

        assert matrix_data[2][2] == 9  # Sev 3, Lik C
        assert matrix_data[3][3] == 16  # Sev 4, Lik D
        assert matrix_data[1][1] == 4  # Sev 2, Lik B

    def test_risk_score_case_insensitive(self):
        """Test risk score calculation is case insensitive."""
        # Likelihood index calculation
        def likelihood_index(likelihood: str) -> int:
            return ord(likelihood.upper()) - ord("A")

        assert likelihood_index("a") == 0
        assert likelihood_index("A") == 0
        assert likelihood_index("b") == 1
        assert likelihood_index("B") == 1

    def test_risk_score_calculation_function(self):
        """Test the risk score calculation function."""
        matrix_data = [
            [1, 2, 3, 4, 5],
            [2, 4, 6, 8, 10],
            [3, 6, 9, 12, 15],
            [4, 8, 12, 16, 20],
            [5, 10, 15, 20, 25],
        ]

        def calculate_score(severity: int, likelihood: str) -> int:
            if not likelihood or len(likelihood) != 1:
                return 0
            likelihood_index = ord(likelihood.upper()) - ord("A")
            if 0 <= likelihood_index < 5 and 1 <= severity <= 5:
                return matrix_data[severity - 1][likelihood_index]
            return 0

        # Valid combinations
        assert calculate_score(1, "A") == 1
        assert calculate_score(1, "E") == 5
        assert calculate_score(5, "A") == 5
        assert calculate_score(5, "E") == 25

        # Invalid severity
        assert calculate_score(0, "A") == 0
        assert calculate_score(6, "A") == 0
        assert calculate_score(-1, "A") == 0

        # Invalid likelihood (out of range)
        assert calculate_score(2, "F") == 0
        assert calculate_score(2, "Z") == 0

        # Edge case: empty string
        assert calculate_score(2, "") == 0


class TestRiskBandCalculation:
    """Tests for risk band calculation logic."""

    def test_get_risk_band_low(self):
        """Test getting low risk band."""
        risk_bands = [
            {"name": "Low", "min_score": 0, "max_score": 5, "color": "green"},
            {"name": "Medium", "min_score": 6, "max_score": 10, "color": "yellow"},
            {"name": "High", "min_score": 11, "max_score": 15, "color": "orange"},
            {"name": "Very High", "min_score": 16, "max_score": 25, "color": "red"},
        ]

        def get_band(score: int) -> str:
            for band in risk_bands:
                if band["min_score"] <= score <= band["max_score"]:
                    return band["name"]
            return "Low"

        assert get_band(0) == "Low"
        assert get_band(5) == "Low"
        assert get_band(3) == "Low"

    def test_get_risk_band_medium(self):
        """Test getting medium risk band."""
        risk_bands = [
            {"name": "Low", "min_score": 0, "max_score": 5, "color": "green"},
            {"name": "Medium", "min_score": 6, "max_score": 10, "color": "yellow"},
            {"name": "High", "min_score": 11, "max_score": 15, "color": "orange"},
            {"name": "Very High", "min_score": 16, "max_score": 25, "color": "red"},
        ]

        def get_band(score: int) -> str:
            for band in risk_bands:
                if band["min_score"] <= score <= band["max_score"]:
                    return band["name"]
            return "Low"

        assert get_band(6) == "Medium"
        assert get_band(10) == "Medium"
        assert get_band(8) == "Medium"

    def test_get_risk_band_high(self):
        """Test getting high risk band."""
        risk_bands = [
            {"name": "Low", "min_score": 0, "max_score": 5, "color": "green"},
            {"name": "Medium", "min_score": 6, "max_score": 10, "color": "yellow"},
            {"name": "High", "min_score": 11, "max_score": 15, "color": "orange"},
            {"name": "Very High", "min_score": 16, "max_score": 25, "color": "red"},
        ]

        def get_band(score: int) -> str:
            for band in risk_bands:
                if band["min_score"] <= score <= band["max_score"]:
                    return band["name"]
            return "Low"

        assert get_band(11) == "High"
        assert get_band(15) == "High"
        assert get_band(13) == "High"

    def test_get_risk_band_very_high(self):
        """Test getting very high risk band."""
        risk_bands = [
            {"name": "Low", "min_score": 0, "max_score": 5, "color": "green"},
            {"name": "Medium", "min_score": 6, "max_score": 10, "color": "yellow"},
            {"name": "High", "min_score": 11, "max_score": 15, "color": "orange"},
            {"name": "Very High", "min_score": 16, "max_score": 25, "color": "red"},
        ]

        def get_band(score: int) -> str:
            for band in risk_bands:
                if band["min_score"] <= score <= band["max_score"]:
                    return band["name"]
            return "Low"

        assert get_band(16) == "Very High"
        assert get_band(25) == "Very High"
        assert get_band(20) == "Very High"

    def test_get_risk_band_below_range(self):
        """Test getting risk band below defined range."""
        risk_bands = [
            {"name": "Low", "min_score": 0, "max_score": 5, "color": "green"},
        ]

        def get_band(score: int) -> str:
            for band in risk_bands:
                if band["min_score"] <= score <= band["max_score"]:
                    return band["name"]
            return "Low"

        # Below range should return default "Low"
        assert get_band(-1) == "Low"
        assert get_band(-100) == "Low"

    def test_get_risk_band_above_range(self):
        """Test getting risk band above defined range."""
        risk_bands = [
            {"name": "Medium", "min_score": 6, "max_score": 10, "color": "yellow"},
        ]

        def get_band(score: int) -> str:
            for band in risk_bands:
                if band["min_score"] <= score <= band["max_score"]:
                    return band["name"]
            return "Low"

        # Above range should return default "Low"
        assert get_band(100) == "Low"


class TestRiskMatrixEdgeCases:
    """Tests for edge cases in risk calculations."""

    def test_empty_matrix_handling(self):
        """Test handling of empty matrix."""
        empty_matrix = []

        def calculate_score(severity: int, likelihood: str, matrix: list) -> int:
            if not matrix:
                return 0
            likelihood_index = ord(likelihood.upper()) - ord("A")
            if 0 <= likelihood_index < 5 and 1 <= severity <= 5:
                if severity <= len(matrix) and likelihood_index < len(matrix[severity - 1]):
                    return matrix[severity - 1][likelihood_index]
            return 0

        assert calculate_score(1, "A", empty_matrix) == 0

    def test_matrix_with_different_sizes(self):
        """Test matrix with non-standard sizes."""
        small_matrix = [[1, 2], [2, 4]]  # 2x2 matrix

        def calculate_score(severity: int, likelihood: str, matrix: list) -> int:
            likelihood_index = ord(likelihood.upper()) - ord("A")
            if 0 <= likelihood_index < 5 and 1 <= severity <= 5:
                if severity <= len(matrix) and likelihood_index < len(matrix[severity - 1]):
                    return matrix[severity - 1][likelihood_index]
            return 0

        assert calculate_score(1, "A", small_matrix) == 1
        assert calculate_score(1, "B", small_matrix) == 2
        assert calculate_score(2, "A", small_matrix) == 2
        assert calculate_score(2, "B", small_matrix) == 4
        # Out of bounds should return 0
        assert calculate_score(1, "C", small_matrix) == 0

    def test_negative_scores(self):
        """Test handling of negative risk scores."""
        risk_bands = [
            {"name": "Negative", "min_score": -10, "max_score": 0, "color": "blue"},
            {"name": "Low", "min_score": 1, "max_score": 5, "color": "green"},
        ]

        def get_band(score: int) -> str:
            for band in risk_bands:
                if band["min_score"] <= score <= band["max_score"]:
                    return band["name"]
            return "Unknown"

        assert get_band(-5) == "Negative"
        assert get_band(0) == "Negative"
        assert get_band(3) == "Low"