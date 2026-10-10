"""Configuration module for VERA Backend.

Architecture Rule 11: Secrets must never be committed.
All settings read from environment variables or .env file with fail-safe defaults.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Service Info ──────────────────────────────────────────────────────────
    PROJECT_NAME: str = "VERA Fraud Investigation Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── Supabase (Database, Auth, Storage) ────────────────────────────────────
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_STORAGE_BUCKET: str = "evidence-vault"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vera_db"

    # ── Upstash Redis & Rate Limiting ─────────────────────────────────────────
    UPSTASH_REDIS_REST_URL: str | None = None
    UPSTASH_REDIS_REST_TOKEN: str | None = None
    UPSTASH_QSTASH_URL: str | None = None
    UPSTASH_QSTASH_TOKEN: str | None = None

    # ── Rate Limits ───────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60          # requests per IP per minute
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 10   # uploads per IP per minute
    RATE_LIMIT_INVESTIGATION_PER_MINUTE: int = 20

    # ── Upload Limits ─────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024   # 50 MB
    ALLOWED_MIME_TYPES: list[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "application/pdf",
        "text/plain",
        "text/csv",
        "application/json",
        "video/mp4",
        "video/webm",
        "audio/mpeg",
        "audio/wav",
        "audio/ogg",
    ]

    # ── AI Providers (Zero-cost requirement / Architecture Rule 15) ───────────
    LLM_PROVIDER: str = "gemini"  # gemini | ollama | groq | mock
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # ── Observability ─────────────────────────────────────────────────────────
    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # ── Security ──────────────────────────────────────────────────────────────
    API_KEY_SECRET: str = "dev-insecure-secret-key-change-in-prod"
    JWT_SECRET_KEY: str = "dev-jwt-secret-change-in-prod-32bytes"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Idempotency key TTL (seconds)
    IDEMPOTENCY_KEY_TTL: int = 86400  # 24 hours

    # ── SSRF Protection ───────────────────────────────────────────────────────
    SSRF_BLOCKED_PREFIXES: list[str] = [
        "http://localhost",
        "http://127.",
        "http://0.",
        "http://10.",
        "http://172.",
        "http://192.168.",
        "https://localhost",
        "https://127.",
        "https://0.",
        "https://10.",
        "https://172.",
        "https://192.168.",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
