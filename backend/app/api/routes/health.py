from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.errors import format_error_response
from app.db.session import check_db_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Health check endpoint that verifies API uptime and Supabase PostgreSQL database connectivity.
    """
    is_healthy, error_msg = check_db_connection()
    if not is_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=format_error_response(
                code="DATABASE_UNAVAILABLE",
                message="Database connection failed or is not reachable.",
                details={"database_error": error_msg} if error_msg else {},
            ),
        )

    return {
        "status": "ok",
        "database": "connected",
        "version": "2.0.0",
    }
