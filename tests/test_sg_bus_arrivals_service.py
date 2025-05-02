"""Tests for SgBusArrivalsService."""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiofiles
from anyio import Path
from custom_components.sg_bus_arrivals.model.bus_stop import BusStop
from custom_components.sg_bus_arrivals.sg_bus_arrivals_service import (
    SgBusArrivalsService,
)
import pytest

from homeassistant.core import HomeAssistant


@pytest.fixture
def service(hass: HomeAssistant) -> SgBusArrivalsService:
    """Fixture for SgBusArrivalsService."""
    return SgBusArrivalsService(hass, "test_api_key")


@pytest.fixture
def mock_session():
    """Mock aiohttp ClientSession."""
    with patch("aiohttp.ClientSession") as mock_client_session:
        session = MagicMock()
        mock_client_session.return_value.__aenter__.return_value = session
        yield session


async def test_authenticate_success(
    mock_session: MagicMock, service: SgBusArrivalsService
) -> None:
    """Test successful authentication."""

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_session.get.return_value.__aenter__.return_value = mock_response

    result = await service.authenticate()

    assert result is True


async def test_authenticate_failed(
    mock_session: MagicMock, service: SgBusArrivalsService
) -> None:
    """Test successful authentication."""

    mock_response = AsyncMock()
    mock_response.status = 401
    mock_session.get.return_value.__aenter__.return_value = mock_response

    result = await service.authenticate()

    assert result is False


async def test_authenticate_already_authenticated(
    service: SgBusArrivalsService,
) -> None:
    """Test authentication when already authenticated."""

    service._is_authenticated = True  # noqa: SLF001

    result = await service.authenticate()

    assert result is True


async def test_get_bus_stop(
    mock_session: MagicMock, service: SgBusArrivalsService
) -> None:
    """Test get bus stop."""

    # for entry in os.scandir("tests/fixtures"):
    #    print(f"File: {entry.name}")

    json: str = await load_file("tests/fixtures/bus_stops.json")

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = json
    mock_session.get.return_value.__aenter__.return_value = mock_response

    bus_stop: BusStop = await service.get_bus_stop("01012")

    assert bus_stop is not None


async def test_get_bus_stop_not_found(
    mock_session: MagicMock, service: SgBusArrivalsService
) -> None:
    """Test get bus stop."""

    # for entry in os.scandir("tests/fixtures"):
    #    print(f"File: {entry.name}")

    json: str = await load_file("tests/fixtures/bus_stops.json")

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = json
    mock_session.get.return_value.__aenter__.return_value = mock_response

    bus_stop: BusStop = await service.get_bus_stop("invalid bus stop code")

    assert bus_stop is None


async def load_file(filename: str) -> Any:
    """Load a file from the test data directory."""

    exists: bool = await Path(filename).exists()
    path = filename if exists else "config/" + filename

    async with aiofiles.open(path, encoding="utf-8") as file:
        contents: str = await file.read()
        return json.loads(contents)
