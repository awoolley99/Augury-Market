"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { EvidenceMark } from "@/components/EvidenceMark";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <EvidenceMark className="w-full h-16 mb-8" />

        <h1 className="font-display text-3xl text-parchment mb-1">Augury Market</h1>
        <p className="text-hush text-sm mb-8">
          It doesn&apos;t guess. It reads the evidence.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-xs uppercase tracking-wide text-hush mb-1.5">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md bg-ink-800 border border-ink-700 px-3 py-2.5 text-parchment placeholder:text-hush/60 focus:outline-none focus:ring-2 focus:ring-signal/50 focus:border-signal/50"
              placeholder="you@firm.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-xs uppercase tracking-wide text-hush mb-1.5">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md bg-ink-800 border border-ink-700 px-3 py-2.5 text-parchment placeholder:text-hush/60 focus:outline-none focus:ring-2 focus:ring-signal/50 focus:border-signal/50"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p role="alert" className="text-fall text-sm">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-signal text-ink-950 font-medium py-2.5 hover:bg-signal-dim transition-colors disabled:opacity-50"
          >
            {submitting ? "Reading the signs…" : "Sign in"}
          </button>
        </form>

        <p className="text-hush text-sm mt-6 text-center">
          New here?{" "}
          <Link href="/register" className="text-signal hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </main>
  );
}
