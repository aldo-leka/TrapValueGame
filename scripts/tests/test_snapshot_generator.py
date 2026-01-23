"""Unit tests for snapshot_generator service."""

import pytest
from datetime import date, datetime, timedelta
from services.snapshot_generator import (
    generate_snapshots,
    compute_outcome,
    classify_outcome,
    classify_difficulty,
)


class TestClassifyOutcome:
    """Test outcome classification logic."""

    def test_value_classification_high_return(self):
        """Returns >= 30% should be classified as 'value'."""
        assert classify_outcome(0.50) == "value"  # 50%
        assert classify_outcome(0.30) == "value"  # 30% (boundary)
        assert classify_outcome(1.00) == "value"  # 100%

    def test_trap_classification_low_return(self):
        """Returns <= -20% should be classified as 'trap'."""
        assert classify_outcome(-0.50) == "trap"  # -50%
        assert classify_outcome(-0.20) == "trap"  # -20% (boundary)
        assert classify_outcome(-0.90) == "trap"  # -90%

    def test_neutral_classification_middle_return(self):
        """Returns between -20% and 30% should be 'neutral'."""
        assert classify_outcome(0.00) == "neutral"  # 0%
        assert classify_outcome(0.10) == "neutral"  # 10%
        assert classify_outcome(0.29) == "neutral"  # Just below value
        assert classify_outcome(-0.19) == "neutral"  # Just above trap
        assert classify_outcome(-0.10) == "neutral"  # -10%


class TestClassifyDifficulty:
    """Test difficulty classification logic."""

    def test_easy_classification_extreme_returns(self):
        """Extreme returns (>= 50%) are easy to identify."""
        assert classify_difficulty(0.60) == "easy"  # 60%
        assert classify_difficulty(-0.60) == "easy"  # -60%
        assert classify_difficulty(0.50) == "easy"  # Boundary
        assert classify_difficulty(-0.50) == "easy"  # Boundary

    def test_hard_classification_small_returns(self):
        """Small returns (<= 10%) are hard to call."""
        assert classify_difficulty(0.05) == "hard"  # 5%
        assert classify_difficulty(-0.05) == "hard"  # -5%
        assert classify_difficulty(0.10) == "hard"  # Boundary
        assert classify_difficulty(0.00) == "hard"  # 0%

    def test_medium_classification_middle_returns(self):
        """Returns between 10% and 50% are medium difficulty."""
        assert classify_difficulty(0.25) == "medium"  # 25%
        assert classify_difficulty(-0.25) == "medium"  # -25%
        assert classify_difficulty(0.40) == "medium"  # 40%


class TestComputeOutcome:
    """Test outcome computation from price data."""

    @pytest.fixture
    def sample_prices(self):
        """Generate sample price data for testing."""
        base_date = date(2020, 1, 1)
        base_price = 100.0

        prices = []
        for i in range(800):  # ~2+ years of daily data
            prices.append({
                "date": base_date + timedelta(days=i),
                "adj_close": base_price + (i * 0.1),  # Gradual increase
            })
        return prices

    @pytest.fixture
    def declining_prices(self):
        """Generate declining price data for testing trap scenarios."""
        base_date = date(2020, 1, 1)
        base_price = 100.0

        prices = []
        for i in range(800):
            prices.append({
                "date": base_date + timedelta(days=i),
                "adj_close": max(base_price - (i * 0.08), 10.0),  # Declining
            })
        return prices

    def test_compute_outcome_success(self, sample_prices):
        """Successfully compute outcome from valid price data."""
        snapshot_date = date(2020, 6, 1)  # 5 months in
        outcome = compute_outcome(sample_prices, snapshot_date)

        assert outcome is not None
        assert "price_at_snapshot" in outcome
        assert "price_at_24mo" in outcome
        assert "return_24mo" in outcome
        assert "outcome_label" in outcome
        assert "difficulty" in outcome

    def test_compute_outcome_returns_none_insufficient_data(self):
        """Return None when insufficient price data."""
        # Only 1 day of data
        prices = [{"date": date(2020, 1, 1), "adj_close": 100.0}]
        outcome = compute_outcome(prices, date(2020, 1, 1))
        assert outcome is None

    def test_compute_outcome_calculates_correct_return(self):
        """Verify return calculation is accurate."""
        prices = [
            {"date": date(2020, 1, 1), "adj_close": 100.0},
            {"date": date(2020, 7, 1), "adj_close": 110.0},  # 6mo
            {"date": date(2021, 1, 1), "adj_close": 120.0},  # 12mo
            {"date": date(2022, 1, 1), "adj_close": 150.0},  # 24mo
        ]

        outcome = compute_outcome(prices, date(2020, 1, 1))

        assert outcome is not None
        assert outcome["price_at_snapshot"] == 100.0
        assert outcome["price_at_24mo"] == 150.0
        assert outcome["return_24mo"] == 0.50  # 50% return
        assert outcome["outcome_label"] == "value"

    def test_compute_outcome_declining_stock(self, declining_prices):
        """Test outcome for a declining stock (trap)."""
        snapshot_date = date(2020, 6, 1)
        outcome = compute_outcome(declining_prices, snapshot_date)

        assert outcome is not None
        assert outcome["return_24mo"] < 0
        # Should be classified as trap due to significant decline


class TestGenerateSnapshots:
    """Test snapshot generation for stocks."""

    @pytest.fixture
    def long_price_history(self):
        """Generate 8 years of price data."""
        base_date = date(2016, 1, 1)
        prices = []

        for i in range(2920):  # ~8 years
            prices.append({
                "date": base_date + timedelta(days=i),
                "adj_close": 100.0 + (i * 0.02),  # Slow growth
            })
        return prices

    def test_generate_snapshots_empty_prices(self):
        """Return empty list for empty prices."""
        result = generate_snapshots(1, [])
        assert result == []

    def test_generate_snapshots_insufficient_history(self):
        """Return empty list when history is too short."""
        # Only 1 year of data when we need 5+ years
        base_date = date(2023, 1, 1)
        prices = [
            {"date": base_date + timedelta(days=i), "adj_close": 100.0}
            for i in range(365)
        ]

        result = generate_snapshots(1, prices, min_history_years=5)
        assert result == []

    def test_generate_snapshots_creates_valid_snapshots(self, long_price_history):
        """Generate valid snapshots from sufficient price history."""
        result = generate_snapshots(
            stock_id=42,
            prices=long_price_history,
            min_history_years=5,
            forward_months=24,
            min_snapshot_year=2021
        )

        assert len(result) > 0

        for snapshot in result:
            assert snapshot["stock_id"] == 42
            assert "snapshot_date" in snapshot
            assert "price_at_snapshot" in snapshot
            assert "return_24mo" in snapshot
            assert "outcome_label" in snapshot
            assert snapshot["snapshot_date"].year >= 2021

    def test_generate_snapshots_quarterly_intervals(self, long_price_history):
        """Snapshots should be approximately 90 days apart."""
        result = generate_snapshots(
            stock_id=1,
            prices=long_price_history,
            min_snapshot_year=2021
        )

        if len(result) >= 2:
            date1 = result[0]["snapshot_date"]
            date2 = result[1]["snapshot_date"]
            diff = (date2 - date1).days
            assert 85 <= diff <= 95  # Approximately quarterly

    def test_generate_snapshots_respects_min_snapshot_year(self, long_price_history):
        """All snapshots should be on or after min_snapshot_year."""
        result = generate_snapshots(
            stock_id=1,
            prices=long_price_history,
            min_snapshot_year=2022
        )

        for snapshot in result:
            assert snapshot["snapshot_date"].year >= 2022


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_classify_outcome_exact_boundaries(self):
        """Test exact boundary values."""
        assert classify_outcome(0.30) == "value"  # Exactly 30%
        assert classify_outcome(-0.20) == "trap"  # Exactly -20%

    def test_classify_difficulty_exact_boundaries(self):
        """Test exact boundary values."""
        assert classify_difficulty(0.50) == "easy"  # Exactly 50%
        assert classify_difficulty(0.10) == "hard"  # Exactly 10%

    def test_compute_outcome_with_datetime_input(self):
        """Handle datetime objects as input."""
        prices = [
            {"date": date(2020, 1, 1), "adj_close": 100.0},
            {"date": date(2022, 1, 1), "adj_close": 130.0},
        ]

        # Pass datetime instead of date
        outcome = compute_outcome(prices, datetime(2020, 1, 1))
        assert outcome is not None
        assert outcome["return_24mo"] == 0.30

    def test_generate_snapshots_mixed_date_types(self):
        """Handle mixed date/datetime in price data."""
        base_date = date(2016, 1, 1)
        prices = []

        for i in range(2920):
            prices.append({
                "date": base_date + timedelta(days=i),
                "adj_close": 100.0 + i,
            })

        # Should not raise an error
        result = generate_snapshots(1, prices, min_snapshot_year=2021)
        assert isinstance(result, list)
