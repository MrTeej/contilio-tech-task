import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from app.connectors.train_api.train_api_connector import map_api_response_to_model
from app.connectors.train_api.models import TrainStationData, TrainDeparture

TEST_DATA_PATH = "tests/data/test_train_api_responses.json"

with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
    test_cases = json.load(f)


@pytest.mark.parametrize("case_name, test_data", test_cases.items())
def test_map_api_response_to_model(case_name, test_data):
    """Test that map_api_response_to_model correctly adjusts arrival times when crossing midnight and for 'STARTS HERE' trains."""

    api_response = test_data["api_response"]
    expected_arrival_adjusted = test_data["expected_arrival_adjusted"]

    result = map_api_response_to_model(api_response)

    assert isinstance(result, TrainStationData)
    assert len(result.departures) > 0

    departure = result.departures[0]

    if case_name == "train_starts_here":
        expected_arrival_time = departure.origin_expected_departure_time - timedelta(
            minutes=10
        )
        assert (
            departure.origin_expected_arrival_time == expected_arrival_time
        ), f"Test case '{case_name}' failed: Expected arrival time to be 10 minutes before departure, but got {departure.origin_expected_arrival_time}"
    elif expected_arrival_adjusted:
        assert (
            departure.destination_aimed_arrival_time.date()
            > datetime.fromisoformat(api_response["date"]).date()
        ), f"Test case '{case_name}' failed: Expected next-day adjustment, but got {departure.destination_aimed_arrival_time}"

    else:
        assert (
            departure.destination_aimed_arrival_time.date()
            == datetime.fromisoformat(api_response["date"]).date()
        ), f"Test case '{case_name}' failed: Did not expect next-day adjustment, but it changed."
