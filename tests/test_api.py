"""Tests for SgBusArrivals."""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiofiles
from anyio import Path
from custom_components.sg_bus_arrivals.api import (
    ApiAuthenticationError,
    ApiGeneralError,
    SgBusArrivals,
)
from custom_components.sg_bus_arrivals.models import (
    BusArrival,
    BusStop,
    TrainServiceAlert,
)
import pytest


@pytest.fixture
def service(mock_session: MagicMock) -> SgBusArrivals:
    """Fixture for SgBusArrivals."""
    return SgBusArrivals(mock_session, "test_api_key")


@pytest.fixture
def mock_session():
    """Mock aiohttp ClientSession."""
    with patch("aiohttp.ClientSession") as mock_client_session:
        session = MagicMock()
        mock_client_session.return_value.__aenter__.return_value = session
        yield session


async def test_authenticate_success(
    mock_session: MagicMock, service: SgBusArrivals
) -> None:
    """Test successful authentication."""

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_session.get.return_value.__aenter__.return_value = mock_response

    await service.authenticate()

    assert mock_session.get.called


async def test_authenticate_failed(
    mock_session: MagicMock, service: SgBusArrivals
) -> None:
    """Test successful authentication."""

    mock_response = AsyncMock()
    mock_response.status = 401
    mock_session.get.return_value.__aenter__.return_value = mock_response

    with pytest.raises(ApiAuthenticationError):
        await service.authenticate()

    assert mock_session.get.called


async def test_authenticate_error(
    mock_session: MagicMock, service: SgBusArrivals
) -> None:
    """Test successful authentication."""

    mock_response = AsyncMock()
    mock_response.status = 500
    mock_session.get.return_value.__aenter__.return_value = mock_response

    with pytest.raises(ApiGeneralError):
        await service.authenticate()

    assert mock_session.get.called


async def test_get_bus_stop(
    mock_session: MagicMock, service: SgBusArrivals
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

    assert mock_session.get.called
    assert bus_stop is not None


async def test_get_bus_stop_not_found(
    mock_session: MagicMock, service: SgBusArrivals
) -> None:
    """Test get bus stop."""

    json: str = await load_file("tests/fixtures/bus_stops_empty.json")

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = json
    mock_session.get.return_value.__aenter__.return_value = mock_response

    bus_stop: BusStop = await service.get_bus_stop("invalid bus stop code")

    assert mock_session.get.called
    assert bus_stop is None


async def test_get_bus_arrivals(
    mock_session: MagicMock, service: SgBusArrivals
) -> None:
    """Test get bus arrivals."""

    json: str = await load_file("tests/fixtures/bus_arrival.json")

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = json
    mock_session.get.return_value.__aenter__.return_value = mock_response

    arrivals: list[BusArrival] = await service.get_bus_arrivals("83139")

    assert mock_session.get.called
    assert arrivals


async def test_compute_arrival_minutes(service: SgBusArrivals) -> None:
    """Test compute arrival minutes."""

    result: int = service._compute_arrival_minutes("9999-12-31T12:00:00+08:00")  # noqa: SLF001

    assert result > 0


async def test_train_service_alerts(mock_session: MagicMock, service: SgBusArrivals) -> None:
    "Test get train service alerts."

    json: str = await load_file("tests/fixtures/train_service_alerts.json")

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = json
    mock_session.get.return_value.__aenter__.return_value = mock_response

    response: dict[str, TrainServiceAlert] = await service.get_train_service_alerts()

    assert mock_session.get.called
    assert "normal" in response["nel"].status


async def load_file(filename: str) -> Any:
    """Load a file from the test data directory."""

    exists: bool = await Path(filename).exists()
    path = filename if exists else "config/" + filename

    async with aiofiles.open(path, encoding="utf-8") as file:
        contents: str = await file.read()
        return json.loads(contents)
