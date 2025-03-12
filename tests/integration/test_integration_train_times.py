import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from api.main import app
from api.feature.train_times.models import TrainTimeRequest

mock_train_schedule = {
    "station_codes": ["LBG", "DFD"],
    "start_time": "2024-08-04 15:30",
    "max_wait_time": 120,
    "force_cache_refresh": False,
}

mock_train_response = {"arrival_time": "2024-08-04 17:30:00"}


# Just to showcase I've though about integration tests, but for now have mocked early.
@pytest.mark.asyncio
@patch(
    "app.feature.train_times.services.TrainTimeService.calculate_train_destination_arrival",
    new_callable=AsyncMock,
)
async def test_train_times_success(mock_calculate_train_destination_arrival):
    """Test the /traintimes endpoint with a successful response."""
    mock_calculate_train_destination_arrival.return_value = mock_train_response

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/traintimes", json=mock_train_schedule)

    assert response.status_code == 200
    data = response.json()
    assert "arrival_time" in data
    assert data["arrival_time"] == mock_train_response["arrival_time"]

    mock_calculate_train_destination_arrival.assert_called_once_with(
        TrainTimeRequest(**mock_train_schedule)
    )


@pytest.mark.asyncio
@patch(
    "app.feature.train_times.services.TrainTimeService.calculate_train_destination_arrival",
    new_callable=AsyncMock,
)
async def test_train_times_error(mock_calculate_train_destination_arrival):
    """Test the /traintimes endpoint when an error occurs."""
    mock_calculate_train_destination_arrival.side_effect = Exception(
        "Unexpected error!"
    )

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/traintimes", json=mock_train_schedule)

    assert response.status_code == 500
    data = response.json()
    assert "message" in data
    assert data["message"] == "An unexpected error occurred. Please try again later."

    mock_calculate_train_destination_arrival.assert_called_once()
