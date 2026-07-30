from fastapi import APIRouter

from app.api.v1 import admin, auth, books, chat, conversations, memory, quran

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(conversations.router)
api_router.include_router(memory.router)
api_router.include_router(quran.router)
api_router.include_router(books.router)
api_router.include_router(admin.router)
