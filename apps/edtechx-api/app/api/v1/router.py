"""v1 API surface."""

from fastapi import APIRouter

from app.api.v1 import attendance, auth, experience, people, system

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(people.router)
api_router.include_router(experience.router)
api_router.include_router(attendance.router)
