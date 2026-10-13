# Supabase Backup and Disaster Recovery Runbook

## Overview
Supabase Free Tier projects do not include automated point-in-time recovery (PITR) or automated backups.
Furthermore, idle Supabase Free Tier projects automatically pause after 7 consecutive days of inactivity.

This runbook documents the disaster recovery and resilience mitigations implemented for VERA.

---

## 1. Automated Mitigations
- **Idle Pause Prevention**: `.github/workflows/keepalive-supabase.yml` executes every 3 days at 04:00 UTC, triggering a lightweight ping query (`SELECT 1`) to reset the 7-day idle timer.
- **Daily Automated Backup**: `.github/workflows/backup-supabase.yml` runs daily at 02:00 UTC, taking a full `pg_dump` compressed with gzip (`.sql.gz`) and uploading it to secure 14-day GitHub Actions Artifact storage.

---

## 2. Manual Backup Export
To generate an immediate snapshot from an administrator machine:

```bash
# Set direct database connection string (Transaction Pooler or Direct URI)
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# Execute pg_dump
pg_dump "$DATABASE_URL" \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  --quote-all-identifiers \
  | gzip > "vera_manual_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
```

---

## 3. Disaster Recovery / Full Restoration Procedure

If the Supabase project is corrupted, accidentally deleted, or unpaused with schema inconsistencies:

### Step 3.1: Provision or Reset Supabase Project
1. Log in to [Supabase Dashboard](https://supabase.com/dashboard).
2. Create a new project or navigate to the existing project settings.
3. Ensure `vector` extension is enabled:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   ```

### Step 3.2: Decompress and Restore SQL Snapshot
```bash
# Decompress the latest daily artifact
gunzip -c vera_backup_YYYYMMDD_HHMMSS.sql.gz > restore.sql

# Restore into target database
psql "$NEW_DATABASE_URL" -f restore.sql
```

### Step 3.3: Verify Migration Integrity via Alembic
```bash
# Validate alembic version matches head
alembic current
alembic upgrade head
```

### Step 3.4: Verify Application Readiness
Query the `/ready` probe:
```bash
curl -s http://localhost:8000/ready | jq .
# Expected output:
# {
#   "status": "ready",
#   "checks": {
#     "database": "connected",
#     "redis": "connected",
#     ...
#   }
# }
```
If the database was paused and has not yet completed waking, `/ready` will report:
`"database": "db paused/unreachable"`.
