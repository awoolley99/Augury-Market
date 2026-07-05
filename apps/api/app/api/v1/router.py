from fastapi import APIRouter

from app.api.v1 import auth, scanner, watchlists

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(watchlists.router)
api_router.include_router(scanner.router)
