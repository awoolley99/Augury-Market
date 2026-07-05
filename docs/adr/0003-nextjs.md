# ADR 0003: Next.js for the dashboard frontend

## Status
Accepted

## Context
The dashboard (Module 10) needs a fast morning-briefing load, SEO for public
marketing pages later, and a component model the team can iterate on quickly.

## Decision
Next.js (App Router) with the built-in fetch-based API client in `lib/api.ts`,
rather than a separate SPA (Vite + React Router) or a meta-framework tied to a
specific host.

## Rationale
- App Router's server components let expensive briefing aggregation
  (Module 10) run server-side without a separate BFF layer.
- One deployment artifact for both authenticated dashboard and any future
  public marketing/pricing pages.
- Large ecosystem (Vercel or self-hosted via Docker, per apps/web/Dockerfile).

## Consequences
- Ties the frontend to React/Next conventions; acceptable given team
  familiarity assumed from the existing Lyubas project.
