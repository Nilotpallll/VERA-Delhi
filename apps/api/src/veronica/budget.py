"""Budget enforcement and in-memory caching to guarantee zero Gemini free-tier starvation.

Constraints:
- Global LLM limit: 4 RPM (Leaves 11+ RPM for VERA core forensic analysis on 15 RPM free tier)
- Per-session limit: 6 LLM turns per 10-minute window
- LRU Query Cache: 1-hour TTL for identical questions
- Canned & safety answers bypass the LLM entirely (0 tokens)
"""

import hashlib
import time
from collections import deque
from typing import Any


class VeronicaBudgetTracker:
    def __init__(
        self,
        global_rpm_limit: int = 4,
        session_limit_per_10m: int = 6,
        cache_ttl_seconds: int = 3600,
        max_cache_entries: int = 250
    ):
        self.global_rpm_limit = global_rpm_limit
        self.session_limit_per_10m = session_limit_per_10m
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_cache_entries = max_cache_entries

        # Global timestamps for rolling 60s window
        self._global_timestamps: deque[float] = deque()
        # Per-session timestamps for rolling 600s window
        self._session_timestamps: dict[str, deque[float]] = {}
        # Query Cache: hash -> (response_dict, expiry_time)
        self._cache: dict[str, tuple[dict[str, Any], float]] = {}

    def _purge_old_global(self, now: float) -> None:
        window_start = now - 60.0
        while self._global_timestamps and self._global_timestamps[0] < window_start:
            self._global_timestamps.popleft()

    def _purge_old_session(self, session_id: str, now: float) -> None:
        if session_id not in self._session_timestamps:
            return
        window_start = now - 600.0
        q = self._session_timestamps[session_id]
        while q and q[0] < window_start:
            q.popleft()
        if not q:
            del self._session_timestamps[session_id]

    def _purge_expired_cache(self, now: float) -> None:
        expired_keys = [k for k, (_, exp) in self._cache.items() if exp < now]
        for k in expired_keys:
            del self._cache[k]

    def check_llm_budget(self, session_id: str | None = None) -> tuple[bool, str | None]:
        """Checks if a new LLM generation call is permitted within free tier constraints."""
        now = time.time()
        self._purge_old_global(now)

        if len(self._global_timestamps) >= self.global_rpm_limit:
            wait_time = int(60.0 - (now - self._global_timestamps[0])) + 1
            return False, f"Veronica is currently busy assisting other investors. Please retry in {wait_time}s."

        if session_id:
            self._purge_old_session(session_id, now)
            q = self._session_timestamps.get(session_id)
            if q and len(q) >= self.session_limit_per_10m:
                return False, "You have reached your session limit of 6 assistant turns per 10 minutes. Please consult our FAQ chips or the main scanner."

        return True, None

    def record_llm_usage(self, session_id: str | None = None) -> None:
        """Records an authorized LLM generation event."""
        now = time.time()
        self._global_timestamps.append(now)
        if session_id:
            if session_id not in self._session_timestamps:
                self._session_timestamps[session_id] = deque()
            self._session_timestamps[session_id].append(now)

    def get_remaining_global_rpm(self) -> int:
        now = time.time()
        self._purge_old_global(now)
        return max(0, self.global_rpm_limit - len(self._global_timestamps))

    def get_cache(self, query: str, language: str) -> dict[str, Any] | None:
        now = time.time()
        self._purge_expired_cache(now)
        cache_key = hashlib.sha256(f"{language.lower().strip()}:{query.lower().strip()}".encode()).hexdigest()
        item = self._cache.get(cache_key)
        if item:
            data, exp = item
            if exp >= now:
                return data
            else:
                del self._cache[cache_key]
        return None

    def set_cache(self, query: str, language: str, response_data: dict[str, Any]) -> None:
        now = time.time()
        if len(self._cache) >= self.max_cache_entries:
            self._purge_expired_cache(now)
            if len(self._cache) >= self.max_cache_entries:
                # Evict oldest entry
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]

        cache_key = hashlib.sha256(f"{language.lower().strip()}:{query.lower().strip()}".encode()).hexdigest()
        self._cache[cache_key] = (response_data, now + self.cache_ttl_seconds)

    def cache_size(self) -> int:
        return len(self._cache)


# Global singleton instance
veronica_budget = VeronicaBudgetTracker()
