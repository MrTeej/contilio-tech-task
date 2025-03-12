from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class TrainDeparture(BaseModel):
    origin_station_code: str
    destination_station_code: str
    origin_expected_departure_time: datetime
    origin_expected_arrival_time: datetime
    destination_aimed_arrival_time: datetime


# Unsure if I need to worry about platform change time / train status i.e. cancelled
# Keeping it simple, will just assume every train will depart and no bus replacement
class TrainStationData(BaseModel):
    station_code: str
    request_time: str
    departures: List[TrainDeparture]
    date: str
