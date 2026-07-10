"use client";

import { useEffect, useState } from "react";
import { api, QuizQuestionRead, ApiError } from "@/lib/api";

interface RiskQuizModalProps {
  accessToken: string;
  onComplete: (riskLevel: string) => void;
  onSkip: () => void;
}

export function RiskQuizModal({ accessToken, onComplete, onSkip }: RiskQuizModalProps) {
  const [questions, setQuestions] = useState<QuizQuestionRead[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getQuiz(accessToken)
      .then(setQuestions)
      .catch(() => setError("Couldn't load the quiz. You can try again later."))
      .finally(() => setLoading(false));
  }, [accessToken]);

  const allAnswered = questions.length > 0 && questions.every((q) => answers[q.id]);

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      const profile = await api.submitQuiz(accessToken, answers);
      onComplete(profile.risk_level);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save your answers. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/80 px-4 py-8 overflow-y-auto">
      <div className="w-full max-w-2xl rounded-lg border border-ink-700 bg-ink-900 p-6 my-auto">
        <h2 className="font-display text-2xl text-parchment mb-1">
          Before we begin — how do you invest?
        </h2>
        <p className="text-hush text-sm mb-6">
          Seven quick questions. Your answers shape how Top Opportunities is ranked for
          you — nothing here changes the evidence or the confidence score itself, just
          what gets surfaced first.
        </p>

        {loading ? (
          <p className="text-hush text-sm">Loading questions…</p>
        ) : questions.length === 0 ? (
          <p className="text-fall text-sm">{error ?? "Couldn't load the quiz."}</p>
        ) : (
          <div className="space-y-6">
            {questions.map((q, qIndex) => (
              <div key={q.id}>
                <p className="text-sm text-parchment mb-2">
                  <span className="text-hush mr-1">{qIndex + 1}.</span>
                  {q.prompt}
                </p>
                <div className="space-y-1.5">
                  {q.options.map((opt) => {
                    const selected = answers[q.id] === opt.letter;
                    return (
                      <button
                        key={opt.letter}
                        type="button"
                        onClick={() =>
                          setAnswers((prev) => ({ ...prev, [q.id]: opt.letter }))
                        }
                        className={`w-full text-left rounded-md border px-3 py-2 text-sm transition-colors ${
                          selected
                            ? "border-signal bg-signal/10 text-parchment"
                            : "border-ink-700 bg-ink-800 text-hush hover:border-ink-700/80 hover:text-parchment"
                        }`}
                      >
                        <span className="font-mono text-xs mr-2">{opt.letter}.</span>
                        {opt.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}

            {error && <p className="text-fall text-sm">{error}</p>}

            <div className="flex items-center justify-between pt-2">
              <button
                onClick={onSkip}
                className="text-hush text-sm hover:text-parchment transition-colors"
              >
                Skip for now
              </button>
              <button
                onClick={handleSubmit}
                disabled={!allAnswered || submitting}
                className="rounded-md bg-signal text-ink-950 font-medium px-5 py-2 text-sm hover:bg-signal-dim transition-colors disabled:opacity-40"
              >
                {submitting ? "Saving…" : "See my Top Opportunities"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
