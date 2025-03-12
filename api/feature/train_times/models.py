from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, field_validator, model_serializer


class TrainTimeRequest(BaseModel):
    station_codes: List[str] = Field(
        ...,
        min_length=2,
        description="Must contain at least two station codes.",
        examples=[["LBG", "DFD", "LUT"]],
    )
    start_time: str = Field(
        ...,
        pattern=r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}",
        description="Format: YYYY-MM-DD HH:MM",
        examples=["2024-08-04 15:30"],
    )
    max_wait_time: int = Field(
        ...,
        ge=10,
        le=9999,
        description="Must be between 10 and 9999 minutes.",
        examples=[120],
    )
    force_cache_refresh: bool = Field(
        default=False,
        description="Set to true to force refresh from API.",
        examples=[False],
    )

    @field_validator("station_codes", mode="before")
    @classmethod
    def validate_station_codes(cls, station_codes):
        if not all(len(code) == 3 and code.isalpha() for code in station_codes):
            raise ValueError("Each station code must be exactly 3 letters.")
        return [code.upper() for code in station_codes]


class TrainTimeResponse(BaseModel):
    arrival_time: datetime

    @model_serializer
    def serialize_model(self):
        return {"arrival_time": self.arrival_time.strftime("%Y-%m-%d %H:%M:%S")}
