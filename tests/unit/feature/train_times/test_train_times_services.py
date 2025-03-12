import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from api.feature.train_times.services import TrainTimeService
from api.feature.train_times.models import TrainTimeRequest, TrainTimeResponse
from api.connectors.db.models import TrainSchedule
from api.utils.error_handler import TrainServiceError


# Opted to only test a few files, but in real world scenario ideally test most code and ensure coverage 80+
@pytest.fixture
def mock_db_connector():
    mock_db = MagicMock()
    mock_db.get_train_schedule = MagicMock()
    mock_db.has_recent_api_call = MagicMock(return_value=False)
    mock_db.add_train_schedule = MagicMock()
    mock_db.add_api_call_tracker = MagicMock()
    return mock_db


@pytest.fixture
def train_time_service(mock_db_connector):
    return TrainTimeService(mock_db_connector)


@pytest.fixture
def mock_train_schedule():
    return TrainSchedule(
        origin_station_code="LBG",
        destination_station_code="DFD",
        origin_expected_departure_time=datetime(
            2024, 8, 4, 15, 30, tzinfo=timezone.utc
        ),
        origin_expected_arrival_time=datetime(2024, 8, 4, 16, 10, tzinfo=timezone.utc),
        destination_aimed_arrival_time=datetime(
            2024, 8, 4, 16, 15, tzinfo=timezone.utc
        ),
    )


@pytest.fixture(autouse=True)
def patch_fetch_train_times():
    with patch(
        "app.feature.train_times.services.fetch_train_times", new=AsyncMock()
    ) as mock_fetch:
        yield mock_fetch


@pytest.mark.asyncio
async def test_fetch_and_store_train_data(
    train_time_service, mock_db_connector, mock_train_schedule, patch_fetch_train_times
):
    """Test fetching train data and storing it in the database."""
    mock_api_response = MagicMock()
    mock_api_response.departures = [mock_train_schedule]

    patch_fetch_train_times.return_value = mock_api_response

    await train_time_service.fetch_and_store_train_data(
        "LBG", "DFD", datetime(2024, 8, 4, 15, 30, tzinfo=timezone.utc)
    )

    mock_db_connector.add_train_schedule.assert_called_once()
    mock_db_connector.add_api_call_tracker.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_train_schedule_found(
    train_time_service, mock_db_connector, mock_train_schedule
):
    """Test fetching a train schedule when data exists in DB."""
    mock_db_connector.get_train_schedule.return_value = mock_train_schedule

    result = train_time_service.fetch_train_schedule(
        "LBG", "DFD", datetime(2024, 8, 4, 15, 30), 60
    )

    assert result == mock_train_schedule
    mock_db_connector.get_train_schedule.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_train_schedule_not_found(train_time_service, mock_db_connector):
    """Test fetching a train schedule when data does not exist in DB."""
    mock_db_connector.get_train_schedule.return_value = None

    with pytest.raises(TrainServiceError):
        await train_time_service.fetch_train_schedule(
            "LBG", "DFD", datetime(2024, 8, 4, 15, 30), 60
        )


@pytest.mark.asyncio
async def test_handle_train_schedule_check_no_refresh(
    train_time_service, mock_db_connector
):
    """Test handling the train schedule check when cache exists (no API call needed)."""
    mock_db_connector.has_recent_api_call.return_value = True

    request = TrainTimeRequest(
        station_codes=["LBG", "DFD"],
        start_time="2024-08-04 15:30",
        max_wait_time=60,
        force_cache_refresh=False,
    )

    with patch.object(
        train_time_service, "fetch_and_store_train_data", new=AsyncMock()
    ) as mock_fetch:
        await train_time_service._handle_train_schedule_check(
            request, "LBG", "DFD", datetime(2024, 8, 4, 16, 10)
        )

    mock_fetch.assert_not_called()


@pytest.mark.asyncio
async def test_handle_train_schedule_check_with_refresh(
    train_time_service, mock_db_connector
):
    """Test handling the train schedule check when cache does not exist (API call needed)."""
    mock_db_connector.has_recent_api_call.return_value = False

    request = TrainTimeRequest(
        station_codes=["LBG", "DFD"],
        start_time="2024-08-04 15:30",
        max_wait_time=60,
        force_cache_refresh=False,
    )

    with patch.object(
        train_time_service, "fetch_and_store_train_data", new=AsyncMock()
    ) as mock_fetch:
        await train_time_service._handle_train_schedule_check(
            request, "LBG", "DFD", datetime(2024, 8, 4, 16, 10)
        )

    mock_fetch.assert_called_once()


@pytest.mark.asyncio
async def test_calculate_train_destination_arrival(
    train_time_service, mock_db_connector, mock_train_schedule
):
    """Test calculating train destination arrival time with multiple stations."""
    mock_db_connector.get_train_schedule.return_value = mock_train_schedule

    request = TrainTimeRequest(
        station_codes=["LBG", "DFD", "LUT"],
        start_time="2024-08-04 15:30",
        max_wait_time=60,
        force_cache_refresh=False,
    )

    result = await train_time_service.calculate_train_destination_arrival(request)

    assert isinstance(result, TrainTimeResponse)
    assert result.arrival_time == mock_train_schedule.destination_aimed_arrival_time


@pytest.mark.asyncio
async def test_calculate_train_destination_arrival_past_midnight(
    train_time_service, mock_db_connector
):
    """Test that arrival time adjustment correctly calls handle_train_schedule_check for the next day if past midnight."""

    mock_db_connector.get_train_schedule.return_value = TrainSchedule(
        origin_station_code="LBG",
        destination_station_code="DFD",
        origin_expected_departure_time=datetime(
            2024, 8, 4, 23, 30, tzinfo=timezone.utc
        ),
        origin_expected_arrival_time=datetime(2024, 8, 5, 0, 10, tzinfo=timezone.utc),
        destination_aimed_arrival_time=datetime(2024, 8, 5, 0, 15, tzinfo=timezone.utc),
    )

    request = TrainTimeRequest(
        station_codes=["LBG", "DFD"],
        start_time="2024-08-04 23:30",
        max_wait_time=60,
        force_cache_refresh=False,
    )

    with patch.object(
        train_time_service, "_handle_train_schedule_check", new=AsyncMock()
    ) as mock_handle_check:
        result = await train_time_service.calculate_train_destination_arrival(request)

    assert isinstance(result, TrainTimeResponse)
    assert result.arrival_time == datetime(2024, 8, 5, 0, 15, tzinfo=timezone.utc)

    calls = mock_handle_check.call_args_list
    assert len(calls) == 2, f"Expected 2 calls, but got {len(calls)}"

    assert calls[0][0][3].replace(tzinfo=timezone.utc) == datetime(
        2024, 8, 4, 23, 30, tzinfo=timezone.utc
    ), f"Expected first call at 2024-08-04 23:30 UTC, but got {calls[0][0][3]}"

    assert calls[1][0][3].replace(tzinfo=timezone.utc) == datetime(
        2024, 8, 5, 23, 30, tzinfo=timezone.utc
    ), f"Expected second call at 2024-08-05 23:30, but got {calls[1][0][3]}"


@pytest.mark.asyncio
async def test_fetch_train_schedule_increasing_times(
    train_time_service, mock_db_connector
):
    """Test that each call to fetch_train_schedule has an increasing arrival_datetime."""

    train_schedules = [
        TrainSchedule(
            origin_station_code="LBG",
            destination_station_code="DFD",
            origin_expected_departure_time=datetime(
                2024, 8, 4, 15, 30, tzinfo=timezone.utc
            ),
            origin_expected_arrival_time=datetime(
                2024, 8, 4, 16, 10, tzinfo=timezone.utc
            ),
            destination_aimed_arrival_time=datetime(
                2024, 8, 4, 16, 15, tzinfo=timezone.utc
            ),
        ),
        TrainSchedule(
            origin_station_code="DFD",
            destination_station_code="LUT",
            origin_expected_departure_time=datetime(
                2024, 8, 4, 16, 30, tzinfo=timezone.utc
            ),
            origin_expected_arrival_time=datetime(
                2024, 8, 4, 17, 10, tzinfo=timezone.utc
            ),
            destination_aimed_arrival_time=datetime(
                2024, 8, 4, 17, 15, tzinfo=timezone.utc
            ),
        ),
    ]
    mock_db_connector.get_train_schedule.side_effect = train_schedules

    request = TrainTimeRequest(
        station_codes=["LBG", "DFD", "LUT"],
        start_time="2024-08-04 15:30",
        max_wait_time=60,
        force_cache_refresh=False,
    )

    with patch.object(
        train_time_service, "_handle_train_schedule_check", new=AsyncMock()
    ):
        await train_time_service.calculate_train_destination_arrival(request)

    calls = mock_db_connector.get_train_schedule.call_args_list
    assert len(calls) == len(
        train_schedules
    ), "fetch_train_schedule should be called for each station pair"

    for i in range(1, len(calls)):
        prev_call = calls[i - 1]
        curr_call = calls[i]

        prev_arrival_time = prev_call[0][2].replace(tzinfo=timezone.utc)
        curr_arrival_time = curr_call[0][2].replace(tzinfo=timezone.utc)

        assert curr_arrival_time > prev_arrival_time, (
            f"Train schedule {i} departs at {curr_arrival_time} "
            f"which is before or equal to the previous arrival time {prev_arrival_time}"
        )


@pytest.mark.asyncio
async def test_handle_train_schedule_check_multiple_days(train_time_service):
    """Test that _handle_train_schedule_check is called three times if train spans two extra days."""

    with patch.object(
        train_time_service, "_handle_train_schedule_check", new=AsyncMock()
    ) as mock_handle_check:

        request = TrainTimeRequest(
            station_codes=["LBG", "DFD"],
            start_time="2024-08-04 15:30",
            max_wait_time=3000,
            force_cache_refresh=False,
        )

        await train_time_service.calculate_train_destination_arrival(request)

        # Expecting 3 calls (1 for original day + 2 for extra days)
        assert (
            mock_handle_check.call_count == 3
        ), f"Expected 3 calls, got {mock_handle_check.call_count}"

        called_times = [call.args[3] for call in mock_handle_check.call_args_list]

        assert (
            called_times[0].date() == datetime(2024, 8, 4).date()
        ), f"Expected first call on 2024-08-04, got {called_times[0].date()}"

        assert (
            called_times[1].date() == datetime(2024, 8, 5).date()
        ), f"Expected second call on 2024-08-05, got {called_times[1].date()}"

        assert (
            called_times[2].date() == datetime(2024, 8, 6).date()
        ), f"Expected third call on 2024-08-06, got {called_times[2].date()}"
