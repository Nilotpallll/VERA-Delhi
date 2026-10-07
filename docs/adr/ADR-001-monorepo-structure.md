# ADR-001: Monorepo Architecture with Strict Package Boundaries

## Status
Accepted

## Context
VERA comprises a Next.js web application, a FastAPI forensic backend, shared data schemas, and machine learning models. A multi-repo setup creates contract drift, divergent versioning, and complex integration testing. Conversely, an undisciplined monorepo risks tight coupling between frontend and backend.

## Decision
We adopt a monorepo structure utilizing npm workspaces for the TypeScript layer (`packages/contracts`, `apps/web`) alongside a dedicated Python package structure (`apps/api`):

```
vera/
├── apps/
│   ├── web/        # Next.js 14 Frontend
│   └── api/        # FastAPI Python Backend
├── packages/
│   └── contracts/  # Shared TypeScript & JSON Schema Contracts
├── ml/             # ML Model Registry & Specs
├── data/           # Database Schema & Migrations
├── infra/          # Infrastructure blueprints & Compose
└── docs/           # Architecture docs & ADRs
```

## Consequences
- Single pull request spans contract updates, backend implementations, and frontend interfaces.
- Clear boundary enforcement: `apps/web` cannot import from `apps/api` directly; communication occurs exclusively via HTTP over `@vera/contracts`.
- Avoids multiple microservices per Architecture Rule 14.
