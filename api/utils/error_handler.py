import traceback
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.utils.logger import logger


class TrainServiceError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


async def pydantic_validation_error_handler(request: Request, exc: ValidationError):
    error_details = exc.errors()

    for error in error_details:
        field = error.get("loc", ["Unknown field"])[-1]
        message = error.get("msg", "Unknown error")
        error_type = error.get("type", "Unknown type")
        logger.error(
            f"Validation error in field '{field}': {message} (type: {error_type})"
        )

    logger.error(f"Validation error details: {error_details}")

    return JSONResponse(
        status_code=400, content={"message": "Validation error, check logs for details"}
    )


async def general_exception_handler(request: Request, exc: Exception):
    error_message = "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    logger.error(f"Unexpected error: {error_message}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."},
    )


async def train_service_error(request: Request, exc: TrainServiceError):
    logger.error(f"Train Service Error: {exc.message}")
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message})
