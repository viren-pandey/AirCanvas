from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models import User
from ..schemas import DesktopLaunchResponse
from ..security import create_access_token
from ..services.activity import record_activity


router = APIRouter(prefix="/desktop", tags=["desktop"])
_desktop_processes: dict[uuid.UUID, subprocess.Popen] = {}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _running_process_for(user_id: uuid.UUID) -> subprocess.Popen | None:
    proc = _desktop_processes.get(user_id)
    if proc is None:
        return None
    if proc.poll() is not None:
        _desktop_processes.pop(user_id, None)
        return None
    return proc


@router.post("/launch", response_model=DesktopLaunchResponse)
def launch_desktop(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DesktopLaunchResponse:
    running = _running_process_for(current_user.id)
    if running is not None:
        return DesktopLaunchResponse(
            started=True,
            already_running=True,
            pid=running.pid,
            message="AirCanvas4 desktop is already running.",
        )

    repo_root = _project_root()
    main_path = repo_root / "main.py"
    if not main_path.exists():
        raise HTTPException(status_code=500, detail=f"Desktop launcher not found at {main_path}")

    token = create_access_token(subject=str(current_user.id), is_admin=current_user.is_admin)
    api_base_url = str(request.base_url).rstrip("/")
    env = os.environ.copy()
    env["API_BASE_URL"] = api_base_url
    env["AIRCANVAS_API_BASE_URL"] = api_base_url
    env["AIRCANVAS_JWT_TOKEN"] = token

    popen_kwargs: dict[str, object] = {
        "cwd": str(repo_root),
        "env": env,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        creation_flags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creation_flags |= int(subprocess.CREATE_NEW_PROCESS_GROUP)
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creation_flags |= int(subprocess.DETACHED_PROCESS)
        popen_kwargs["creationflags"] = creation_flags
    else:
        popen_kwargs["start_new_session"] = True

    try:
        proc = subprocess.Popen(  # noqa: S603,S607 - internal local launcher
            [sys.executable, str(main_path)],
            **popen_kwargs,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to launch desktop app: {exc}") from exc

    _desktop_processes[current_user.id] = proc
    record_activity(
        db,
        user_id=current_user.id,
        activity_type="desktop_app_launched",
        details={"pid": proc.pid},
    )
    db.commit()

    return DesktopLaunchResponse(
        started=True,
        already_running=False,
        pid=proc.pid,
        message="AirCanvas4 desktop launched.",
    )


@router.get("/status", response_model=DesktopLaunchResponse)
def desktop_status(current_user: User = Depends(get_current_user)) -> DesktopLaunchResponse:
    running = _running_process_for(current_user.id)
    if running is None:
        return DesktopLaunchResponse(
            started=False,
            already_running=False,
            pid=None,
            message="Desktop app is not running.",
        )
    return DesktopLaunchResponse(
        started=True,
        already_running=True,
        pid=running.pid,
        message="Desktop app is running.",
    )
