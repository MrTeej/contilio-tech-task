import asyncio
from datetime import datetime, timedelta
from fastapi import Depends
from sqlalchemy.orm import Session
from app.connectors.db.models import TrainSchedule
from app.feature.train_times.models import TrainTimeResponse, TrainTimeRequest
from app.connectors.train_api.train_api_connector import fetch_train_times
from app.utils.error_handler import TrainServiceError
from app.utils.logger import logger
from app.connectors.db.db_connector import DatabaseConnector


class TrainTimeService:
    def __init__(self, db_connector: DatabaseConnector):
        self.db_connector = db_connector

    async def fetch_and_store_train_data(
        self,
        origin_station_code: str,
        destination_station_code: str,
        start_time: datetime,
    ):
        """Fetch train data from the API and store it in the database."""
        logger.info(
            f"Fetching live data from API for {origin_station_code}, to {destination_station_code} at {start_time}"
        )

        api_data = await fetch_train_times(
            origin_station_code, destination_station_code, start_time
        )

        logger.debug("Fetched and transformed API data")

        if not api_data or not api_data.departures:
            raise TrainServiceError(
                f"No train data available for {origin_station_code} at {start_time}"
            )

        logger.debug("Loading API data into DB")
        for train in api_data.departures:
            self.db_connector.add_train_schedule(
                origin_station_code,
                train.destination_station_code,
                train.origin_expected_departure_time,
                train.destination_aimed_arrival_time,
                train.destination_aimed_arrival_time,
            )

        logger.info("Adding API data into tracker for caching")
        self.db_connector.add_api_call_tracker(
            origin_station_code, destination_station_code, start_time
        )

    def fetch_train_schedule(
        self,
        origin_station_code: str,
        destination_station_code: str,
        start_datetime: datetime,
        max_wait_time: int,
    ) -> TrainSchedule:
        """Fetch a train schedule from the database."""
        train_schedule = self.db_connector.get_train_schedule(
            origin_station_code, destination_station_code, start_datetime, max_wait_time
        )

        if not train_schedule:
            raise TrainServiceError(
                f"No schedule found for {origin_station_code}, to {destination_station_code} at {start_datetime}, within {max_wait_time} minutes"
            )

        return train_schedule

    async def _handle_train_schedule_check(
        self,
        request: TrainTimeRequest,
        current_stn_code: str,
        destination_stn_code: str,
        arrival_time: datetime,
    ):
        """Helper method to check cache and fetch train data if necessary."""
        if not request.force_cache_refresh and self.db_connector.has_recent_api_call(
            current_stn_code, destination_stn_code, arrival_time
        ):
            logger.info(
                f"Fetching cached data for {current_stn_code}, to {destination_stn_code} at {arrival_time}"
            )
        else:
            await self.fetch_and_store_train_data(
                current_stn_code, destination_stn_code, arrival_time
            )

    async def calculate_train_destination_arrival(
        self, request: TrainTimeRequest
    ) -> TrainTimeResponse:
        """Calculate the arrival time at the final destination station."""
        station_codes = request.station_codes
        start_time = request.start_time

        if not station_codes or len(station_codes) < 2:
            raise ValueError("At least two station codes are required.")

        start_datetime = datetime.fromisoformat(start_time)
        arrival_datetime = start_datetime

        for i in range(len(station_codes) - 1):
            current_stn_code = station_codes[i]
            destination_stn_code = station_codes[i + 1]

            max_wait_delta = timedelta(minutes=request.max_wait_time)
            new_arrival_time = arrival_datetime + max_wait_delta

            await self._handle_train_schedule_check(
                request, current_stn_code, destination_stn_code, arrival_datetime
            )

            days_difference = (new_arrival_time.date() - arrival_datetime.date()).days

            # Loop through each day difference and make a request for each day
            # Could potentially call a fetch_train_schedule after each api call to terminate earlier
            tasks = [
                self._handle_train_schedule_check(
                    request,
                    current_stn_code,
                    destination_stn_code,
                    arrival_datetime + timedelta(days=day),
                )
                for day in range(1, days_difference + 1)
            ]

            if tasks:
                logger.info(
                    f"Train arrival spans {days_difference} days. Checking all days in parallel."
                )
                await asyncio.gather(*tasks)

            train_schedule = self.fetch_train_schedule(
                current_stn_code,
                destination_stn_code,
                arrival_datetime,
                request.max_wait_time,
            )
            logger.info(
                f"\n ---Found train schedule---\n"
                f"Origin: {train_schedule.origin_station_code} > Destination: {train_schedule.destination_station_code} \n"
                f"origin_expected_departure_time: {train_schedule.origin_expected_departure_time.strftime('%Y-%m-%d %H:%M')} \n"
                f"destination_aimed_arrival_time: {train_schedule.destination_aimed_arrival_time.strftime('%Y-%m-%d %H:%M')} \n"
                f"-----------------------"
            )

            arrival_datetime = train_schedule.destination_aimed_arrival_time

        return TrainTimeResponse(arrival_time=arrival_datetime)
