# ADR 0004: Deterministic confidence scoring, AI only for explanation

## Status
Accepted

## Context
Module 7 (Confidence Score Engine) and Module 8 (AI Summary Engine) could both
be implemented by asking an LLM "how good is this stock," but that makes the
score unreproducible, unauditable, and impossible to backtest.

## Decision
The confidence score is computed by a deterministic weighted formula over
measurable evidence (business quality, momentum, news/catalysts, institutional
activity, sentiment, minus risk adjustment — see Module 7). The AI Summary
Engine (Module 8) only explains a score that has already been computed; it
never assigns or adjusts the score itself.

## Rationale
- Reproducibility: the same evidence packet always yields the same score.
- Backtestability: a deterministic formula can be run against historical
  evidence to validate the weighting scheme.
- Trust: "why did this score change" has a factual, inspectable answer instead
  of "the model felt differently this time."
- This is the platform's core differentiator per the product brief:
  evidence-first architecture, transparent scoring, AI as explainer not oracle.

## Consequences
- The AI Summary Engine's prompt must be constrained to only narrate the
  evidence packet's existing fields — it should not be given free rein to
  invent a rating in prose that contradicts the numeric score.
- Weight tuning (Module 7's 30/20/15/15/10/-15 split) becomes its own
  versioned, testable artifact rather than opaque model behavior.
