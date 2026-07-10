from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.risk_profile_repository import RiskProfileRepository
from app.schemas.risk_profile import QuizQuestionRead, QuizSubmission, RiskProfileRead
from app.services.risk_quiz import QUIZ_QUESTIONS, InvalidQuizAnswer, score_quiz

router = APIRouter(prefix="/quiz", tags=["risk-quiz"])


@router.get("", response_model=list[QuizQuestionRead])
async def get_quiz(current_user: User = Depends(get_current_user)):
    """
    The risk tolerance quiz questions, as the single source of truth the
    frontend renders from -- not hardcoded twice.
    """
    return QUIZ_QUESTIONS


@router.get("/profile", response_model=RiskProfileRead)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = RiskProfileRepository(db)
    profile = await repo.get_for_user(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You haven't taken the risk tolerance quiz yet.",
        )
    return profile


@router.post("/submit", response_model=RiskProfileRead)
async def submit_quiz(
    payload: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Scores the submitted answers and stores (or overwrites) the user's risk
    profile. This immediately affects how Top Opportunities is ranked on
    their dashboard -- see app/services/dashboard.py.
    """
    try:
        raw_score, risk_level, normalized = score_quiz(payload.answers)
    except InvalidQuizAnswer as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    repo = RiskProfileRepository(db)
    profile = await repo.upsert(
        user_id=current_user.id,
        answers=payload.answers,
        risk_score=raw_score,
        risk_level=risk_level,
    )
    await db.commit()
    return profile
