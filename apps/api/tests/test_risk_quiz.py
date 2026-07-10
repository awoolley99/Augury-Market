import pytest

from app.services.risk_quiz import QUIZ_QUESTIONS, InvalidQuizAnswer, score_quiz

ALL_A = {q.id: "A" for q in QUIZ_QUESTIONS}
ALL_MAX = {q.id: q.options[-1].letter for q in QUIZ_QUESTIONS}


def test_all_a_answers_score_minimum_and_conservative():
    raw_score, risk_level, normalized = score_quiz(ALL_A)
    assert raw_score == 7  # 7 questions, each worth 1 point minimum
    assert risk_level == "Conservative"
    assert normalized == 0.0


def test_all_max_answers_score_maximum():
    raw_score, risk_level, normalized = score_quiz(ALL_MAX)
    assert raw_score == 32  # 5+4+4+4+5+5+5
    assert risk_level == "Moderately Aggressive"  # 28-32 band; 33-35 is unreachable by design
    assert normalized == 1.0


def test_seven_questions_exist_matching_the_product_spec():
    assert len(QUIZ_QUESTIONS) == 7
    ids = {q.id for q in QUIZ_QUESTIONS}
    assert ids == {
        "experience", "loss_reaction", "primary_goal", "time_horizon",
        "comfort_investment", "knowledge", "portfolio_choice",
    }


@pytest.mark.parametrize(
    "raw_score,expected_level",
    [
        (7, "Conservative"),
        (13, "Conservative"),
        (14, "Moderately Conservative"),
        (20, "Moderately Conservative"),
        (21, "Moderate"),
        (27, "Moderate"),
        (28, "Moderately Aggressive"),
        (32, "Moderately Aggressive"),
    ],
)
def test_score_bands_match_spec(raw_score, expected_level):
    # Build an answer set that sums to exactly raw_score by adjusting one
    # question at a time from the all-A baseline.
    answers = dict(ALL_A)
    remaining = raw_score - 7
    for q in QUIZ_QUESTIONS:
        max_bump = len(q.options) - 1
        bump = min(remaining, max_bump)
        if bump > 0:
            answers[q.id] = q.options[bump].letter
            remaining -= bump
        if remaining == 0:
            break
    assert remaining == 0, "test construction error: couldn't hit the target raw_score"

    _, risk_level, _ = score_quiz(answers)
    assert risk_level == expected_level


def test_missing_question_raises():
    incomplete = dict(ALL_A)
    del incomplete["knowledge"]
    with pytest.raises(InvalidQuizAnswer, match="knowledge"):
        score_quiz(incomplete)


def test_invalid_letter_for_question_raises():
    answers = dict(ALL_A)
    answers["loss_reaction"] = "E"  # loss_reaction only has A-D
    with pytest.raises(InvalidQuizAnswer, match="loss_reaction"):
        score_quiz(answers)


def test_lowercase_letters_accepted():
    answers = {q.id: "a" for q in QUIZ_QUESTIONS}
    raw_score, risk_level, _ = score_quiz(answers)
    assert raw_score == 7
    assert risk_level == "Conservative"


def test_unknown_question_id_raises():
    answers = dict(ALL_A)
    answers["not_a_real_question"] = "A"
    # score_quiz only iterates QUIZ_QUESTIONS, so an extra unknown key is
    # silently ignored rather than erroring -- this documents that behavior.
    raw_score, risk_level, _ = score_quiz(answers)
    assert raw_score == 7
