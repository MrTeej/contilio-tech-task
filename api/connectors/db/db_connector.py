from typing import Optional
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from api.connectors.db.base import Base
from api.utils.date_helpers import get_start_window
from api.connectors.db.models import TrainSchedule, APICallTracker
from api.utils.config_loader import load_config


class DatabaseConnector:
    """Handles database operations for train schedules and API tracking."""

    def create_db(self):
        Base.metadata.create_all(bind=self.engine)

    def __init__(self):
        config = load_config()
        self.SQLALCHEMY_DATABASE_URL = config["db"]["database_url"]

        self.engine = create_engine(
            self.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.Base = declarative_base()

        self.session = self.SessionLocal()

    def close(self):
        self.session.close()

    def get_train_schedule(
        self,
        origin_station_code: str,
        destination_station_code: str,
        start_time: datetime,
        max_wait_time: int,
    ) -> Optional[TrainSchedule]:
        start_window = start_time
        end_window = start_time + timedelta(minutes=max_wait_time)

        return (
            self.session.query(TrainSchedule)
            .filter(
                TrainSchedule.origin_station_code == origin_station_code,
                TrainSchedule.destination_station_code == destination_station_code,
                TrainSchedule.origin_expected_departure_time >= start_window,
                TrainSchedule.origin_expected_departure_time < end_window,
            )
            .order_by(TrainSchedule.origin_expected_departure_time)
            .first()
        )

    def add_train_schedule(
        self,
        origin_station_code: str,
        destination_code: str,
        origin_departure_time: datetime,
        origin_arrival_time: datetime,
        destination_aimed_arrival_time: datetime,
    ):
        new_entry = TrainSchedule(
            origin_station_code=origin_station_code,
            destination_station_code=destination_code,
            origin_expected_departure_time=origin_departure_time,
            origin_expected_arrival_time=origin_arrival_time,
            destination_aimed_arrival_time=destination_aimed_arrival_time,
        )

        self.session.add(new_entry)
        self.session.commit()
        self.session.refresh(new_entry)
        return new_entry

    def has_recent_api_call(
        self,
        origin_station_code: str,
        destination_station_code: str,
        start_time: datetime,
    ) -> bool:
        normalised_start_time = get_start_window(start_time)

        recent_call = (
            self.session.query(APICallTracker)
            .filter_by(
                origin_station_code=origin_station_code,
                destination_station_code=destination_station_code,
                start_time=normalised_start_time,
            )
            .first()
        )

        return recent_call is not None

    def add_api_call_tracker(
        self,
        origin_station_code: str,
        destination_station_code: str,
        start_time: datetime,
    ):
        start_window = get_start_window(start_time)

        new_tracker = APICallTracker(
            origin_station_code=origin_station_code,
            destination_station_code=destination_station_code,
            start_time=start_window,
            last_fetched=datetime.now(timezone.utc),
        )
        try:
            self.session.add(new_tracker)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

    def update_api_call_tracker(self, origin_station_code: str, start_time: datetime):
        tracker = (
            self.session.query(APICallTracker)
            .filter_by(
                origin_station_code=origin_station_code,
                start_time=get_start_window(start_time),
            )
            .first()
        )
        if tracker:
            tracker.last_fetched = datetime.now(timezone.utc)
            self.session.commit()


db_connector = DatabaseConnector()
