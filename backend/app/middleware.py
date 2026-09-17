from starlette.responses import JSONResponse
from app import limits


class AnalysisLimitsMiddleware:
    """Reject excess requests before FastAPI parses their multipart bodies."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"].rstrip("/") != "/analyze":
            await self.app(scope, receive, send)
            return

        admission = limits.analysis_admission
        if not admission.usage.reserve():
            response = JSONResponse(
                {"detail": "This demo allows 10 analysis requests per minute across all visitors. Please try again in a minute."},
                status_code=429, headers={"Retry-After": "60"},
            )
            await response(scope, receive, send)
            return
        if not admission.slot.acquire(blocking=False):
            response = JSONResponse(
                {"detail": "Another analysis is running. Please try again shortly."},
                status_code=429, headers={"Retry-After": "5"},
            )
            await response(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        finally:
            admission.slot.release()
