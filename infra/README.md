# VERA Infrastructure Architecture

This directory details infrastructure provisioning, local emulation, and cloud operational topology for VERA.

## Services & Topology

| Layer | Service / Provider | Purpose | Free Tier Compliance |
| :--- | :--- | :--- | :--- |
| **Compute - Web** | Next.js on Vercel / Docker | Analyst UI & Case Management | Free Hobby Tier |
| **Compute - API** | FastAPI on Render / Docker | Forensic ingestion & scoring engine | Free Tier / Container |
| **State & Database** | Supabase PostgreSQL + pgvector | Evidence records & vector similarity | Free Tier (500MB DB) |
| **Persistent Storage** | Supabase Storage (`evidence-vault`) | APKs, videos, call recordings | Free Tier (1GB Storage) |
| **Caching & Rate Limit** | Upstash Redis & Upstash Ratelimit | Token bucket rate-limiting | Free Tier (10k req/day) |
| **Async Tasks** | Upstash QStash | Distributed background webhook queue | Free Tier |
| **Local LLM** | Ollama | Private on-premise execution | Free / Local CPU/GPU |
| **Cloud LLM** | Google Gemini Free Tier | Multi-modal claim reasoning & synthesis | Free Rate Limit Tier |

## Environment Isolation Invariant (Architecture Rule 10)

Under no circumstances should uploaded binary assets or forensic artifacts be written to ephemeral disks as permanent storage. Render nodes recycle filesystems on sleep or restart. All file uploads write directly to Supabase Storage, and only metadata + hashes are persisted in PostgreSQL.
