import os
from dotenv import load_dotenv
from pathlib import Path

# Load dotenv as early as possible so all modules (including logger) can read settings
if os.environ.get("IS_DEV") != "false":
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

import logging
import uvicorn
import logfire

# Configure Logging early so config.py and secret_manager.py can log properly
import utils.logger

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.config import settings
from app.errors import ErrorKey, status_for
from app.api.routes import router
from utils.route_loader import get_ai_service_route

logger = logging.getLogger(__name__)

PREFIX, _ = get_ai_service_route()

app = FastAPI(title="Ringisho AI Service")

logfire.instrument_fastapi(app)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    key = ErrorKey.VALIDATION
    return JSONResponse(status_code=status_for(key), content={"error_key": key.value})


@app.exception_handler(Exception)
async def internal_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    key = ErrorKey.INTERNAL
    return JSONResponse(status_code=status_for(key), content={"error_key": key.value})


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "ai-service"}

app.include_router(router, prefix=PREFIX)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
