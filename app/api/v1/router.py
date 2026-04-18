"""
API v1 router — aggregates all v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import screening

api_router = APIRouter()

api_router.include_router(
    screening.router,
    prefix="/screen",
    tags=["Virtual Screening"],
)
