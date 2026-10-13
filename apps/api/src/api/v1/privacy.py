"""Privacy / Right-to-Erasure API endpoints.

GDPR Art 17 / DPDP Act §13: authenticated users may request deletion of all
their data. Analyst/admin role required (JWT).

No PII is returned in responses — only counts and a request_id.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from ...core.auth import AuthenticatedUser, require_auth
from ...core.database import get_db_session
from ...core.observability import logger
from ...services.data_retention import retention_service

router = APIRouter(prefix="/privacy", tags=["Privacy"])


class DeletionResponse(BaseModel):
    message: str
    deleted_investigations: int
    deleted_evidence: int
    request_id: str


@router.delete(
    "/my-data",
    response_model=DeletionResponse,
    summary="Delete all my data (Right to Erasure)",
    description=(
        "Deletes all investigations and evidence associated with the authenticated user. "
        "This action is irreversible. Compliant with GDPR Art 17 and DPDP Act §13."
    ),
    status_code=status.HTTP_200_OK,
)
async def delete_my_data(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_auth),
    db=Depends(get_db_session),
) -> DeletionResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    user_id = current_user.user_id

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized", "request_id": request_id},
        )

    # No PII in log — user_id is deliberately omitted
    logger.info("Data deletion request received", extra={"request_id": request_id})

    result = await retention_service.delete_user_data(str(user_id), db)

    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "DeletionFailed",
                "message": "Data deletion could not be completed. Please try again.",
                "request_id": request_id,
            },
        )

    return DeletionResponse(
        message="All your data has been permanently deleted.",
        deleted_investigations=result["deleted_investigations"],
        deleted_evidence=result["deleted_evidence"],
        request_id=request_id,
    )


@router.post(
    "/retention-cleanup",
    summary="Trigger manual retention cleanup (admin)",
    tags=["Privacy"],
    status_code=status.HTTP_200_OK,
)
async def trigger_retention_cleanup(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_auth),
    db=Depends(get_db_session),
) -> dict:
    """Admin-only: trigger immediate data retention sweep."""
    request_id = getattr(request.state, "request_id", "unknown")
    if current_user.role not in ("admin", "analyst"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Forbidden", "request_id": request_id},
        )

    result = await retention_service.run_cleanup(db)
    return {"status": "ok", "result": result, "request_id": request_id}
