from datetime import datetime, timedelta, timezone
import json
from urllib.parse import quote
import httpx
from api.utils.api_client import fetch_data
from api.utils.config_loader import load_config
from api.utils.date_helpers import (
    adjust_arrival_date,
    format_datetime_ISO8601,
    get_start_window,
    parse_time_with_date,
)
from api.utils.error_handler import TrainServiceError
from api.utils.logger import logger
from api.connectors.train_api.models import TrainStationData, TrainDeparture
from dotenv import load_dotenv
import os

load_dotenv()

config = load_config()["connectors"]["train_times_api"]
DEV_MODE = config.get("dev_mode", False)
MOCK_DATA_PATH = config.get("mock_data_path", "")
SAVE_RAW_DATA = config.get("save_raw_data", False)


def crs_me_please(code: str) -> str:
    return code if code.startswith("crs:") else f"crs:{code}"


def fetch_mock_data():
    """Load train schedule data from a local JSON file for development mode."""
    try:
        with open(MOCK_DATA_PATH, "r") as file:
            mock_data = json.load(file)
            logger.info("Successfully loaded mock data.")
            return map_api_response_to_model(mock_data)
    except Exception as e:
        logger.error(f"Error loading mock data: {e}")
        raise


# Rate limiting/throttling?
# Example URL: "https://transportapi.com/v3/uk/train/station_timetables/crs%3ALBG.json?datetime=2024-08-04T00%3A00%3A00%2B01%3A00&from_offset=PT00%3A00%3A00&to_offset=PT23%3A59%3A59&limit=1000&live=true&train_status=passenger&station_detail=destination&type=departure&destination=crs%3ADFD&app_key=97089d7ffa372eea52a6c828d9e2f18e&app_id=acbc2224"
async def fetch_train_times(
    origin_station_code: str, destination_station_code: str, arrivaltime: str
):
    if DEV_MODE:
        logger.info("Dev mode enabled. Fetching mock data from JSON file.")
        return fetch_mock_data()

    try:
        base_url = config["base_url"]
        app_key = os.getenv("TRAIN_API_APP_KEY")
        app_id = os.getenv("TRAIN_API_APP_ID")

        station_param = crs_me_please(origin_station_code)

        url = f"{base_url}/station_timetables/{quote(station_param)}.json"

        params = {
            "datetime": format_datetime_ISO8601(get_start_window(arrivaltime)),
            "from_offset": "PT00:00:00",  # Was thinking of doing -24 for 48hr window but max limit is 1k and may have to implement pagination
            "to_offset": "PT23:59:59",  # PT24:00:00 Errors?
            "limit": 1000,
            "live": "true",
            "train_status": "passenger",
            "station_detail": "destination",
            "type": "departure",
            "destination": crs_me_please(destination_station_code),
            "app_key": app_key,
            "app_id": app_id,
        }

        logger.debug(f"Making API call to {url}, with query params {params}")
        logger.debug(f"Requesting URL: {url}?{httpx.QueryParams(params)}")

        response = await fetch_data(url, params=params)
        if not response:
            raise TrainServiceError(
                f"No data received from API for {origin_station_code} at {arrivaltime}"
            )

        # My API limits were 30 per day so I was using this to help
        if SAVE_RAW_DATA:
            timestamp = datetime.now(timezone.utc).isoformat()
            safe_timestamp = timestamp.replace(":", "-").replace("+", "_")
            raw_data_path = f"./api_raw_data/{origin_station_code}_TO_{destination_station_code}_AT_{arrivaltime}_{safe_timestamp}.json"
            try:
                with open(raw_data_path, "w", encoding="utf-8") as f:
                    json.dump(response, f, indent=4)
                logger.debug(f"Raw train API response saved to {raw_data_path}")
            except Exception as e:
                logger.error(f"Failed to save raw API response: {e}")

        return map_api_response_to_model(response)

    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTP error while fetching train times: {exc}")
        raise
    except httpx.RequestError as exc:
        logger.error(f"Request error while fetching train times: {exc}")
        raise


def map_api_response_to_model(api_response: dict) -> TrainStationData:
    station_code = api_response.get("station_code", "").replace("crs:", "")
    request_time = api_response.get("request_time", "")
    base_date = api_response.get("date", "")

    departures = []
    departure_data = api_response.get("departures", {}).get("all", [])

    for train in departure_data:
        try:
            origin_departure_time_str = train.get("expected_departure_time")
            origin_arrival_time_str = train.get("expected_arrival_time")
            destination_aimed_arrival_time_str = (
                train.get("station_detail", {})
                .get("destination", {})
                .get("aimed_arrival_time")
            )
            train_status = train.get("status", "")

            origin_departure_time_dt = parse_time_with_date(
                base_date, origin_departure_time_str
            )
            origin_arrival_time_dt = None

            if origin_arrival_time_str is None:
                origin_arrival_time_dt = (
                    origin_departure_time_dt - timedelta(minutes=10)
                    if origin_departure_time_dt
                    else None
                )
                if train_status == "STARTS HERE":
                    logger.debug(
                        f"Train {train.get('train_uid')} starts here, setting arrival time 10 minutes before departure."
                    )
                else:
                    logger.error(
                        f"Expected_arrival_time is missing for train {train.get('train_uid')}, status {train_status}. Setting arrival time 10 minutes before departure."
                    )
            else:
                origin_arrival_time_dt = parse_time_with_date(
                    base_date, origin_arrival_time_str
                )

            destination_aimed_arrival_time_dt = parse_time_with_date(
                base_date, destination_aimed_arrival_time_str
            )
            if (
                destination_aimed_arrival_time_dt.time()
                < origin_departure_time_dt.time()
            ):
                logger.debug(
                    f"Adjusting destination arrival date from {destination_aimed_arrival_time_dt} "
                    f"because it arrives after midnight relative to departure {origin_departure_time_dt}."
                )
                destination_aimed_arrival_time_dt += timedelta(days=1)

            if origin_departure_time_dt and origin_arrival_time_dt:
                origin_arrival_time_dt = adjust_arrival_date(
                    origin_departure_time_dt, origin_arrival_time_dt
                )

            departure = TrainDeparture(
                origin_station_code=station_code,
                destination_station_code=train.get("station_detail", {})
                .get("destination", {})
                .get("station_code", ""),
                origin_expected_departure_time=origin_departure_time_dt,
                origin_expected_arrival_time=origin_arrival_time_dt,
                destination_aimed_arrival_time=destination_aimed_arrival_time_dt,
            )

            departures.append(departure)

        except Exception as e:
            logger.error(f"Error mapping train data: {e}")

    return TrainStationData(
        station_code=station_code,
        request_time=request_time,
        departures=departures,
        date=base_date,
    )
