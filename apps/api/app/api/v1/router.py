from fastapi import APIRouter

from app.api.v1 import ai_summary, auth, brokerage, confidence, dashboard, quiz, scanner, watchlists

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(watchlists.router)
api_router.include_router(scanner.router)
api_router.include_router(confidence.router)
api_router.include_router(ai_summary.router)
api_router.include_router(dashboard.router)
api_router.include_router(quiz.router)
api_router.include_router(brokerage.router)
