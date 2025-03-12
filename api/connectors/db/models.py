from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    String,
    DateTime,
    UniqueConstraint,
)
from api.connectors.db.base import Base


class TrainSchedule(Base):
    __tablename__ = "train_schedule"

    id = Column(Integer, primary_key=True, index=True)
    origin_station_code = Column(String, nullable=False, index=True)
    destination_station_code = Column(String, nullable=False, index=True)
    origin_expected_departure_time = Column(DateTime, nullable=False, index=True)
    origin_expected_arrival_time = Column(DateTime, nullable=False)
    destination_aimed_arrival_time = Column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "origin_expected_departure_time < origin_expected_arrival_time",
            name="check_departure_before_arrival",
        ),
    )


class APICallTracker(Base):
    __tablename__ = "api_call_tracker"

    id = Column(Integer, primary_key=True, index=True)
    origin_station_code = Column(String, nullable=False, index=True)
    destination_station_code = Column(String, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    last_fetched = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "origin_station_code",
            "destination_station_code",
            "start_time",
            name="unique_station_time",
        ),
    )
