"""Tests for SgBusArrivalsService."""

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.sg_bus_arrivals.sg_bus_arrivals_service import (
    SgBusArrivalsService,
)
import pytest

from homeassistant.core import HomeAssistant


@pytest.fixture
def service(hass: HomeAssistant):
    """Fixture for SgBusArrivalsService."""
    return SgBusArrivalsService(hass, "test_api_key")


@pytest.fixture
def mock_session():
    """Mock aiohttp ClientSession."""
    with patch("aiohttp.ClientSession") as mock_client_session:
        session = MagicMock()
        mock_client_session.return_value.__aenter__.return_value = session
        yield session


async def test_authenticate_success(mock_session: MagicMock, service) -> None:
    """Test successful authentication."""

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_session.get.return_value.__aenter__.return_value = mock_response

    result = await service.authenticate()

    assert result is True


async def test_authenticate_failed(mock_session: MagicMock, service) -> None:
    """Test successful authentication."""

    mock_response = AsyncMock()
    mock_response.status = 401
    mock_session.get.return_value.__aenter__.return_value = mock_response

    result = await service.authenticate()

    assert result is False


async def test_authenticate_already_authenticated(service) -> None:
    """Test authentication when already authenticated."""
    service._isAuthenticated = True

    result = await service.authenticate()

    assert result is True
