from __future__ import annotations

import hmac
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

try:
    from fastapi.templating import Jinja2Templates
except ImportError:  # pragma: no cover - optional dependency
    Jinja2Templates = None  # type: ignore[assignment]

try:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware

    HAS_SLOWAPI = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_SLOWAPI = False

from .api import admin, auth, community, desktop, frames, sessions
from .config import settings
from .limiter import limiter


app_kwargs: dict[str, Any] = {
    "title": settings.app_name,
    "debug": settings.debug,
}
if not settings.expose_api_docs:
    app_kwargs.update({"docs_url": None, "redoc_url": None, "openapi_url": None})
app = FastAPI(**app_kwargs)
app.state.limiter = limiter
if HAS_SLOWAPI:
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
cors_origins = settings.cors_origin_list()
allow_credentials = settings.cors_allow_credentials and cors_origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(sessions.router, prefix=settings.api_prefix)
app.include_router(frames.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(community.router, prefix=settings.api_prefix)
app.include_router(desktop.router, prefix=settings.api_prefix)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    return response

templates = None
template_dir = Path(__file__).resolve().parent / "templates"
if Jinja2Templates is not None:
    try:
        templates = Jinja2Templates(directory=str(template_dir))
    except Exception:
        templates = None


def render_template(template_name: str, context: dict[str, Any]) -> HTMLResponse:
    if templates is not None:
        return templates.TemplateResponse(template_name, context)

    template_path = template_dir / template_name
    html = template_path.read_text(encoding="utf-8")
    rendered = html
    for key, value in context.items():
        if key == "request":
            continue
        rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
    return HTMLResponse(content=rendered)


def _enforce_health_access(request: Request) -> None:
    if settings.expose_health_endpoints:
        return
    expected_secret = (settings.healthcheck_secret or "").strip()
    presented_secret = request.headers.get("x-aircanvas-health-key", "").strip()
    if expected_secret and hmac.compare_digest(presented_secret, expected_secret):
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")


@app.get("/health")
def health(request: Request) -> dict[str, str]:
    _enforce_health_access(request)
    return {"status": "ok"}


@app.get("/healthz")
def healthz(request: Request) -> dict[str, str]:
    _enforce_health_access(request)
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    if not settings.expose_backend_pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return RedirectResponse(url="/dashboard", status_code=307)


@app.get("/dashboard", response_class=HTMLResponse)
def user_dashboard(request: Request):
    if not settings.expose_backend_pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return render_template(
        "dashboard.html",
        {
            "request": request,
            "api_prefix": settings.api_prefix,
            "app_name": settings.app_name,
        },
    )


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    if not settings.expose_backend_pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return render_template("admin.html", {"request": request, "api_prefix": settings.api_prefix})
