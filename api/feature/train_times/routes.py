from fastapi import APIRouter, HTTPException, Depends
from api.feature.train_times.models import TrainTimeResponse, TrainTimeRequest
from api.feature.train_times.services import TrainTimeService
from api.utils.logger import logger
from api.connectors.db.db_connector import (
    db_connector,
)

router = APIRouter()


def get_train_time_service():
    return TrainTimeService(db_connector)


@router.post(
    "/traintimes",
    response_model=TrainTimeResponse,
    response_model_exclude_none=True,
    summary="Get the last train arrival time",
    description="Fetches the arrival time based on a list of train station codes and start time",
    tags=["Train Times"],
)
async def train_time(
    request: TrainTimeRequest,
    train_time_service: TrainTimeService = Depends(get_train_time_service),
):
    logger.info("Request received for Train times")
    logger.debug(f"Received request: {request}")

    result = await train_time_service.calculate_train_destination_arrival(request)

    logger.info("Result generated for train times")
    logger.debug(f"Result: {result}")

    return result
