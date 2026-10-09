"""Security utilities: file validation, path traversal, SSRF protection.

Architecture Rule: All uploads must be validated before acceptance.
"""

import hashlib

from fastapi import HTTPException, UploadFile, status

from .config import settings
from .observability import logger

# ── MIME magic-byte prefixes (fallback when python-magic is unavailable) ──────
_MAGIC_BYTES: dict[str, list[bytes]] = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/gif": [b"GIF87a", b"GIF89a"],
    "image/webp": [b"RIFF"],   # bytes 8-12 are "WEBP" but we check both
    "application/pdf": [b"%PDF"],
    "video/mp4": [b"\x00\x00\x00\x18ftyp", b"\x00\x00\x00\x20ftyp"],
    "video/webm": [b"\x1a\x45\xdf\xa3"],
    "audio/mpeg": [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],
    "audio/wav": [b"RIFF"],
    "audio/ogg": [b"OggS"],
}


def validate_file_size(content: bytes, max_bytes: int | None = None) -> None:
    """Raise 413 if content exceeds the configured or provided limit."""
    limit = max_bytes or settings.MAX_UPLOAD_SIZE_BYTES
    if len(content) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": "file_too_large",
                "message": f"File size {len(content):,} bytes exceeds the {limit:,} byte limit.",
                "max_bytes": limit,
                "actual_bytes": len(content),
            },
        )


def validate_mime_type(
    content: bytes,
    declared_mime: str,
    allowed_types: list[str] | None = None,
) -> str:
    """
    Validate that the declared MIME type is allowed and matches the file magic bytes.
    Returns the validated MIME type.
    """
    allowed = allowed_types or settings.ALLOWED_MIME_TYPES
    declared = declared_mime.lower().split(";")[0].strip()

    if declared not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error": "unsupported_media_type",
                "message": f"MIME type '{declared}' is not permitted.",
                "allowed_types": allowed,
            },
        )

    # Magic byte verification (best-effort, no hard error if type unknown)
    if declared in _MAGIC_BYTES:
        magic_sigs = _MAGIC_BYTES[declared]
        if not any(content.startswith(sig) for sig in magic_sigs):
            logger.warning(
                "MIME mismatch: declared=%s magic bytes do not match",
                declared,
            )
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "error": "mime_magic_mismatch",
                    "message": (
                        f"File content does not match declared type '{declared}'. "
                        "Possible spoofing attempt."
                    ),
                },
            )

    return declared


def sanitize_storage_path(raw_path: str) -> str:
    """
    Remove path traversal sequences and normalize storage keys.
    """
    # Normalize separators
    normalized = raw_path.replace("\\", "/")
    # Remove leading slashes
    normalized = normalized.lstrip("/")

    # Collapse relative traversal segments
    parts = []
    for part in normalized.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
        else:
            parts.append(part)

    clean = "/".join(parts)
    return clean or "unnamed_file"


def is_safe_url(url: str) -> bool:
    """Check if URL does not point to internal, localhost, link-local, or non-http(s) targets."""
    import ipaddress
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False

        hostname = (parsed.hostname or "").lower()
        if not hostname or hostname in ("localhost", "127.0.0.1", "::1"):
            return False

        # Check for blocked prefixes or link-local/private IPs
        for blocked in settings.SSRF_BLOCKED_PREFIXES:
            if url.lower().startswith(blocked.lower()):
                return False

        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        except ValueError:
            pass

        return True
    except Exception:
        return False


def validate_file_bytes(
    content: bytes,
    filename: str,
    max_bytes: int | None = None,
) -> tuple[bool, str, str, str | None]:
    """
    Validate binary content, match magic bytes/extension, compute SHA256.
    Returns: (is_valid, mime_type, sha256_hash, error_message)
    """
    limit = max_bytes or settings.MAX_UPLOAD_SIZE_BYTES
    if len(content) > limit:
        return False, "", "", f"File size {len(content)} exceeds limit {limit}"

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    disallowed_extensions = {"exe", "dll", "bat", "cmd", "sh", "ps1", "vbs", "msi"}
    if ext in disallowed_extensions:
        return False, "", "", f"Disallowed file extension: .{ext}"

    # Determine MIME from magic bytes or extension
    detected_mime = "application/octet-stream"
    for mime, signatures in _MAGIC_BYTES.items():
        if any(content.startswith(sig) for sig in signatures):
            detected_mime = mime
            break

    # Extension mapping fallback
    ext_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "pdf": "application/pdf",
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "apk": "application/vnd.android.package-archive",
    }

    if detected_mime == "application/octet-stream" and ext in ext_map:
        detected_mime = ext_map[ext]

    if detected_mime == "application/octet-stream" and ext not in ext_map:
        return False, "", "", f"Unsupported file type: {filename}"

    sha256_hex = compute_sha256(content)
    return True, detected_mime, sha256_hex, None


def validate_ssrf_url(url: str) -> str:
    """
    Reject URLs that point to private/internal networks.
    Raises 400 for any blocked prefix.
    """
    if not is_safe_url(url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ssrf_blocked",
                "message": "URL points to a private, reserved, or disallowed network address.",
            },
        )
    return url


def compute_sha256(content: bytes) -> str:
    """Return hex SHA-256 digest of content."""
    return hashlib.sha256(content).hexdigest()


async def read_and_validate_upload(
    file: UploadFile,
    max_bytes: int | None = None,
    allowed_types: list[str] | None = None,
) -> tuple[bytes, str, str]:
    """
    Read an UploadFile, enforce size + MIME constraints, compute SHA-256.

    Returns: (content_bytes, validated_mime_type, sha256_hex)
    """
    content = await file.read()
    validate_file_size(content, max_bytes)

    declared_mime = file.content_type or "application/octet-stream"
    validated_mime = validate_mime_type(content, declared_mime, allowed_types)
    sha256 = compute_sha256(content)

    logger.info(
        "File validated",
        extra={
            "filename": file.filename,
            "size_bytes": len(content),
            "mime_type": validated_mime,
            "sha256": sha256[:16] + "...",
        },
    )

    return content, validated_mime, sha256

