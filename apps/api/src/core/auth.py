"""Authentication boundary for VERA API.

Phase 1 implements:
- API key authentication (X-API-Key header)
- JWT Bearer token validation (stub ready for Supabase Auth integration)

Phase 2 will wire in Supabase Auth JWT verification.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .observability import logger

# ── Security schemes ──────────────────────────────────────────────────────────
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer_scheme = HTTPBearer(auto_error=False)


# ── Models ────────────────────────────────────────────────────────────────────
class AuthenticatedUser:
    def __init__(
        self,
        user_id: str,
        email: str | None = None,
        roles: list[str] | None = None,
        auth_method: str = "api_key",
        role: str | None = None,
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.roles = roles or ([role] if role else ["investigator"])
        self.role = role or (self.roles[0] if self.roles else "investigator")
        self.auth_method = auth_method

    def has_role(self, role: str) -> bool:
        return role in self.roles


AuthPrincipal = AuthenticatedUser


# ── API Key authentication ────────────────────────────────────────────────────
async def verify_api_key(
    api_key: Annotated[str | None, Security(_api_key_header)] = None,
) -> AuthenticatedUser | None:
    """Verify X-API-Key header. Returns None if not present (optional auth)."""
    if api_key is None:
        return None

    # Constant-time comparison to prevent timing attacks
    import hmac
    if not hmac.compare_digest(api_key.encode(), settings.API_KEY_SECRET.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_api_key", "message": "Invalid API key."},
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return AuthenticatedUser(
        user_id="api-key-user",
        roles=["investigator"],
        role="investigator",
        auth_method="api_key",
    )


def _get_jwt():
    try:
        import jwt
        return jwt
    except ImportError:
        try:
            from jose import jwt
            return jwt
        except ImportError:
            raise RuntimeError("Neither 'jwt' (PyJWT) nor 'jose' (python-jose) is installed.")


# ── JWT Bearer authentication ─────────────────────────────────────────────────
async def verify_jwt_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer_scheme)] = None,
) -> AuthenticatedUser | None:
    """Verify JWT Bearer token. Returns None if not present (optional auth)."""
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        jwt = _get_jwt()
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_token", "message": "Token missing subject claim."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check expiry explicitly
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=UTC) < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "token_expired", "message": "Authentication token has expired."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_role = payload.get("role") or (payload.get("roles", ["investigator"])[0] if payload.get("roles") else "investigator")
        return AuthenticatedUser(
            user_id=user_id,
            email=payload.get("email"),
            roles=payload.get("roles", [user_role]),
            role=user_role,
            auth_method="jwt",
        )

    except HTTPException:
        raise
    except Exception as exc:
        if type(exc).__name__ == "ExpiredSignatureError":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "token_expired", "message": "Authentication token has expired."},
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        logger.warning("JWT validation error: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": "Could not validate credentials."},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── Combined auth dependency ──────────────────────────────────────────────────
async def get_current_user_optional(
    api_key_user: Annotated[AuthenticatedUser | None, Depends(verify_api_key)],
    jwt_user: Annotated[AuthenticatedUser | None, Depends(verify_jwt_token)],
) -> AuthenticatedUser | None:
    """Returns authenticated user from either API key or JWT, or None."""
    return api_key_user or jwt_user


get_optional_principal = get_current_user_optional


async def require_auth(
    user: Annotated[AuthenticatedUser | None, Depends(get_current_user_optional)],
) -> AuthenticatedUser:
    """Require authentication — raises 401 if no valid credentials present."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "authentication_required",
                "message": "Authentication is required to access this resource.",
            },
            headers={"WWW-Authenticate": "Bearer, ApiKey"},
        )
    return user


get_authenticated_principal = require_auth


# ── Token creation and decoding ───────────────────────────────────────────────
def create_access_token(
    subject: str,
    roles: list[str] | None = None,
    role: str | None = None,
    expires_delta: timedelta | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Create a signed JWT access token."""
    jwt = _get_jwt()
    assigned_roles = roles or ([role] if role else ["investigator"])
    primary_role = role or assigned_roles[0]

    delta = expires_delta or timedelta(minutes=expires_minutes or settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(UTC) + delta
    payload = {
        "sub": subject,
        "roles": assigned_roles,
        "role": primary_role,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    encoded = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    if isinstance(encoded, bytes):
        encoded = encoded.decode("utf-8")
    return encoded


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token, returning payload dict or None."""
    try:
        jwt = _get_jwt()
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except Exception:
        return None

