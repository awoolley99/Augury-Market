"""
Risk tolerance quiz.

Question text/options live here as the single source of truth -- the
frontend renders them from GET /quiz rather than hardcoding a duplicate
copy that could drift out of sync with the scoring logic below.

Scoring: each option is worth its letter position (A=1, B=2, C=3, D=4,
E=5), summed across all seven questions, then mapped to a risk category:

  7-13   Conservative
  14-20  Moderately Conservative
  21-27  Moderate
  28-32  Moderately Aggressive
  33-35  Aggressive

Note: not every question offers an E option, so the maximum attainable raw
score is 32, not 35 -- the "Aggressive" band as specified is technically
unreachable with the current seven questions. That's not a bug in this
implementation; the classification table is used exactly as given. If a
future question adds a 5th option, "Aggressive" becomes reachable without
any code changes here.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuizOption:
    letter: str
    label: str


@dataclass(frozen=True)
class QuizQuestion:
    id: str
    prompt: str
    options: list[QuizOption]


QUIZ_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="experience",
        prompt="How would you describe your investing experience?",
        options=[
            QuizOption("A", "I have never invested before."),
            QuizOption("B", "I have invested in savings accounts, CDs, or bonds only."),
            QuizOption("C", "I have invested in mutual funds or ETFs."),
            QuizOption("D", "I have invested in individual stocks."),
            QuizOption("E", "I regularly invest in stocks, options, cryptocurrency, or other advanced investments."),
        ],
    ),
    QuizQuestion(
        id="loss_reaction",
        prompt=(
            "If your investment portfolio lost 15% of its value over a few months "
            "due to market volatility, what would you most likely do?"
        ),
        options=[
            QuizOption("A", "Sell everything immediately."),
            QuizOption("B", "Sell some investments to limit further losses."),
            QuizOption("C", "Hold my investments and wait for the market to recover."),
            QuizOption("D", "Buy more while prices are lower."),
        ],
    ),
    QuizQuestion(
        id="primary_goal",
        prompt="Which statement best describes your primary investment goal?",
        options=[
            QuizOption("A", "Preserve my money with little or no risk."),
            QuizOption("B", "Generate steady income while limiting risk."),
            QuizOption("C", "Balance growth and stability."),
            QuizOption("D", "Maximize long-term growth, even if my portfolio experiences significant ups and downs."),
        ],
    ),
    QuizQuestion(
        id="time_horizon",
        prompt="How long do you expect to keep most of your investments before needing the money?",
        options=[
            QuizOption("A", "Less than 2 years."),
            QuizOption("B", "2-5 years."),
            QuizOption("C", "5-10 years."),
            QuizOption("D", "More than 10 years."),
        ],
    ),
    QuizQuestion(
        id="comfort_investment",
        prompt="Which investment would you feel most comfortable owning?",
        options=[
            QuizOption("A", "A savings account earning a guaranteed return."),
            QuizOption("B", "Government or high-quality corporate bonds."),
            QuizOption("C", "A diversified stock index fund."),
            QuizOption("D", "A portfolio of individual growth stocks."),
            QuizOption("E", "High-growth or speculative investments with the potential for large gains and losses."),
        ],
    ),
    QuizQuestion(
        id="knowledge",
        prompt="Which statement best describes your knowledge of investing?",
        options=[
            QuizOption("A", "I know very little about investing."),
            QuizOption("B", "I understand the basics but rely on others for guidance."),
            QuizOption("C", "I am comfortable evaluating common investments like ETFs and mutual funds."),
            QuizOption("D", "I regularly research investments and understand concepts like diversification, valuation, and risk."),
            QuizOption("E", "I actively manage investments and understand advanced topics such as options, leverage, or portfolio optimization."),
        ],
    ),
    QuizQuestion(
        id="portfolio_choice",
        prompt="If you had $100,000 to invest, which portfolio would you choose?",
        options=[
            QuizOption("A", "100% cash or CDs with guaranteed returns."),
            QuizOption("B", "70% bonds / 30% stocks."),
            QuizOption("C", "50% bonds / 50% stocks."),
            QuizOption("D", "20% bonds / 80% stocks."),
            QuizOption("E", "100% stocks or other high-growth investments."),
        ],
    ),
]

_QUESTIONS_BY_ID = {q.id: q for q in QUIZ_QUESTIONS}

_MIN_POSSIBLE_SCORE = sum(1 for _ in QUIZ_QUESTIONS)  # every question's A is worth 1
_MAX_POSSIBLE_SCORE = sum(len(q.options) for q in QUIZ_QUESTIONS)

_RISK_BANDS: list[tuple[int, int, str]] = [
    (7, 13, "Conservative"),
    (14, 20, "Moderately Conservative"),
    (21, 27, "Moderate"),
    (28, 32, "Moderately Aggressive"),
    (33, 35, "Aggressive"),
]


class InvalidQuizAnswer(Exception):
    pass


def _points_for(question_id: str, letter: str) -> int:
    question = _QUESTIONS_BY_ID.get(question_id)
    if not question:
        raise InvalidQuizAnswer(f"Unknown question id: {question_id}")

    valid_letters = {opt.letter for opt in question.options}
    letter = letter.strip().upper()
    if letter not in valid_letters:
        raise InvalidQuizAnswer(
            f"'{letter}' is not a valid answer for question '{question_id}' "
            f"(valid options: {sorted(valid_letters)})"
        )
    return ord(letter) - ord("A") + 1  # A=1, B=2, C=3, D=4, E=5


def _risk_level_for(raw_score: int) -> str:
    for low, high, label in _RISK_BANDS:
        if low <= raw_score <= high:
            return label
    # Below the lowest band or above the highest -- clamp to the nearest end
    # rather than raising, since this is a display classification, not a
    # hard validation boundary.
    return _RISK_BANDS[0][2] if raw_score < _RISK_BANDS[0][0] else _RISK_BANDS[-1][2]


def score_quiz(answers: dict[str, str]) -> tuple[int, str, float]:
    """
    Takes {question_id: letter} for all seven questions, returns
    (raw_score, risk_level_label, normalized_0_to_1).

    Raises InvalidQuizAnswer if a question is missing or a letter is invalid
    for that question.
    """
    missing = [q.id for q in QUIZ_QUESTIONS if q.id not in answers]
    if missing:
        raise InvalidQuizAnswer(f"Missing answers for: {', '.join(missing)}")

    raw_score = sum(_points_for(q.id, answers[q.id]) for q in QUIZ_QUESTIONS)
    risk_level = _risk_level_for(raw_score)
    normalized = (raw_score - _MIN_POSSIBLE_SCORE) / (_MAX_POSSIBLE_SCORE - _MIN_POSSIBLE_SCORE)
    return raw_score, risk_level, round(normalized, 4)
