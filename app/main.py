from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.feature.train_times.routes import router as train_times_router
from app.utils.config_loader import load_config
from app.utils.error_handler import (
    TrainServiceError,
    train_service_error,
    http_exception_handler,
    general_exception_handler,
)


config = load_config()

origins = config["app"]["cors_origins"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(TrainServiceError, train_service_error)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(train_times_router)


@app.get(
    "/",
    summary="API Root Endpoint",
    description=(
        "Welcome to the Contilio Train API! This is the root endpoint, providing basic information "
        "and navigation links for the API documentation. Access the following resources:\n\n"
        "- **Swagger UI**: Interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)\n"
        "- **ReDoc**: Alternative API documentation at [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)\n"
        "- **OpenAPI JSON**: Raw OpenAPI specification at [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)"
    ),
)
async def root():
    return {
        "message": (
            "Welcome to the Contilio Train API, "
            "Swagger UI: Navigate to http://127.0.0.1:8000/docs, "
            "ReDoc: Navigate to http://127.0.0.1:8000/redoc, "
            "OpenAPI JSON: Access the raw JSON at http://127.0.0.1:8000/openapi.json"
        )
    }
