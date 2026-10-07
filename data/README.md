# VERA Data Architecture & Contracts

This directory manages the database schema, pgvector embeddings, and persistent storage abstractions for the VERA platform.

## Architecture Invariants

1. **Supabase PostgreSQL & pgvector**  
   All entity metadata, canonical evidence, and investigation manifests reside in Supabase PostgreSQL. Vector embeddings (1024 dimensions via BGE-M3) are indexed via `pgvector` with HNSW for hybrid semantic retrieval.

2. **Supabase Storage Isolation (Architecture Rule 10)**  
   Persistent media files (videos, audio recordings, screenshots, APK binaries) **must never depend on the local filesystem** of ephemeral hosts (such as Render). Instead, all assets are pushed to Supabase Storage (`evidence-vault` bucket), and database records store immutable `StorageReference` objects.

3. **Deterministic Auditability (Architecture Rule 13)**  
   The `analyzer_execution_records` table preserves raw findings, semver codes, and weights digests for every execution pass, ensuring full reproducibility.
