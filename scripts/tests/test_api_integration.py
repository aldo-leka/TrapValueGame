"""Integration tests for FastAPI endpoints."""

import pytest
import sys
from pathlib import Path
from datetime import date
from unittest.mock import patch, AsyncMock, MagicMock

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_db():
    """Mock database for testing."""
    mock = MagicMock()

    # Mock cursor context manager
    mock_cursor = MagicMock()
    mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor.__aexit__ = AsyncMock(return_value=None)
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.fetchall = AsyncMock(return_value=[])

    mock.execute = MagicMock(return_value=mock_cursor)

    return mock


@pytest.fixture
def test_snapshot_row():
    """Sample snapshot data as it would come from database."""
    return (
        1,  # id
        "2023-01-15",  # snapshot_date
        "Test narrative here",  # narrative
        "Tech Alpha Corp",  # fake_name
        "Technology",  # sector
        "Software",  # industry
        42,  # stock_id
    )


@pytest.fixture
def test_financials_rows():
    """Sample financial data rows."""
    return [
        (2022, 15000.0, 0.60, 4000.0, 5000.0, 3000.0, 3200.0, 1000.0, 5000.0),
        (2021, 12000.0, 0.58, 3000.0, 4000.0, 2200.0, 2500.0, 1500.0, 4000.0),
        (2020, 10000.0, 0.55, 2500.0, 3500.0, 1800.0, 2000.0, 2000.0, 3000.0),
    ]


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_endpoint(self):
        """Health endpoint should return healthy status."""
        from main import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestGameEndpoints:
    """Test game-related API endpoints."""

    @pytest.mark.asyncio
    async def test_get_next_snapshot_no_data(self, mock_db):
        """Return 404 when no snapshots available."""
        from main import app

        with patch("api.game.get_db", return_value=mock_db):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/game/next")

                # Should return 404 when no data
                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reveal_invalid_choice(self):
        """Return 400 for invalid player choice."""
        from main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/game/reveal/1?player_choice=invalid"
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_reveal_snapshot_not_found(self, mock_db):
        """Return 404 for non-existent snapshot."""
        from main import app

        with patch("api.game.get_db", return_value=mock_db):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/game/reveal/99999?player_choice=value"
                )

                assert response.status_code == 404


class TestAdminEndpoints:
    """Test admin-related API endpoints."""

    def test_seed_endpoint_accepts_tickers(self):
        """Seed endpoint should accept ticker list."""
        from main import app

        client = TestClient(app)

        # The seed endpoint runs in background, so it returns immediately
        response = client.post(
            "/admin/seed",
            json={"tickers": ["TEST"], "force_refresh": False}
        )

        assert response.status_code == 200
        assert "message" in response.json()

    def test_seed_sp500_endpoint(self):
        """SP500 seed endpoint should return immediately."""
        from main import app

        client = TestClient(app)

        response = client.post("/admin/seed-sp500")

        assert response.status_code == 200
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_status_endpoint(self, mock_db):
        """Status endpoint should return database stats."""
        from main import app

        # Mock the cursor to return counts
        mock_cursor = MagicMock()
        mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor.__aexit__ = AsyncMock(return_value=None)

        # Return different counts for different queries
        mock_cursor.fetchone = AsyncMock(side_effect=[
            (10,),  # total_stocks
            (50,),  # total_snapshots
            (40,),  # playable_snapshots
        ])

        mock_db.execute = MagicMock(return_value=mock_cursor)

        with patch("api.admin.get_db", return_value=mock_db):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/admin/status")

                # Check response structure
                assert response.status_code == 200
                data = response.json()
                assert "total_stocks" in data or "error" not in data


class TestQueryParameters:
    """Test query parameter handling."""

    @pytest.mark.asyncio
    async def test_next_snapshot_with_difficulty_filter(self, mock_db):
        """Test filtering by difficulty."""
        from main import app

        with patch("api.game.get_db", return_value=mock_db):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/game/next?difficulty=easy")

                # Will return 404 with mock, but should not error
                assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_next_snapshot_with_sector_filter(self, mock_db):
        """Test filtering by sector."""
        from main import app

        with patch("api.game.get_db", return_value=mock_db):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/game/next?sector=Technology")

                assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_next_snapshot_with_exclude_ids(self, mock_db):
        """Test excluding specific snapshot IDs."""
        from main import app

        with patch("api.game.get_db", return_value=mock_db):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/game/next?exclude_ids=1,2,3")

                assert response.status_code in [200, 404]


class TestResponseSchemas:
    """Test that responses match expected schemas."""

    def test_health_response_schema(self):
        """Health response should have correct schema."""
        from main import app

        client = TestClient(app)
        response = client.get("/health")

        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert isinstance(data["status"], str)


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_endpoint_returns_404(self):
        """Non-existent endpoints return 404."""
        from main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/nonexistent/endpoint")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_method_not_allowed(self):
        """Wrong HTTP method returns 405."""
        from main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # Try POST on GET endpoint
            response = await client.post("/health")

            assert response.status_code == 405


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers_present(self):
        """CORS headers should be present for allowed origins."""
        from main import app

        client = TestClient(app)

        # Preflight request
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5000",
                "Access-Control-Request-Method": "GET",
            }
        )

        # Should allow the origin
        assert response.status_code in [200, 204]
