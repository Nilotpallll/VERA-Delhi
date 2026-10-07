# ADR-005: Stateless Compute and Storage Isolation

## Status
Accepted

## Context
Deploying VERA on container platforms (e.g., Render, Fly.io, AWS ECS, or Kubernetes) means container filesystems are strictly ephemeral. Any forensic artifact (APK files, high-res audio, scraped pages) stored on local disk will disappear upon container recycling, redeployment, or horizontal auto-scaling.

## Decision
1. **Rule 10 (Zero Local Disk Dependency):**
   - The backend service (`apps/api`) is strictly stateless.
   - All uploaded evidence payloads are streamed directly to Supabase Storage (`evidence-vault` bucket) or compatible object storage.
   - The database records only immutable `StorageReference` metadata:
     `{ bucket: string, storagePath: string, provider: "supabase_storage", mimeType: string, sizeBytes: number }`.
2. Temporary forensic extraction (e.g., unpacking APK archives with `apktool` or slicing frames with `ffmpeg`) must execute in ephemeral scratch directories and clean up immediately upon completion.

## Consequences
- The API backend can scale horizontally without shared NFS mounts or volume locks.
- Render node sleep/restart does not cause data loss.
