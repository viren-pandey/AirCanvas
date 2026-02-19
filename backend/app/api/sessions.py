from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models import CanvasSession, User
from ..schemas import SessionCreateRequest, SessionEndRequest, SessionOut
from ..services.activity import record_activity


router = APIRouter(prefix="/sessions", tags=["sessions"])


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def start_session(
    payload: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionOut:
    session = CanvasSession(
        user_id=current_user.id,
        session_start=_as_utc(payload.session_start) or datetime.now(timezone.utc),
    )
    db.add(session)
    db.flush()
    record_activity(
        db,
        user_id=current_user.id,
        activity_type="session_started",
        details={"session_id": str(session.id)},
    )
    db.commit()
    db.refresh(session)
    return SessionOut.model_validate(session)


@router.patch("/{session_id}/end", response_model=SessionOut)
def end_session(
    session_id: uuid.UUID,
    payload: SessionEndRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionOut:
    session = db.get(CanvasSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    session.session_end = _as_utc(payload.session_end) or datetime.now(timezone.utc)
    if payload.avg_fps is not None:
        session.avg_fps = float(payload.avg_fps)

    record_activity(
        db,
        user_id=current_user.id,
        activity_type="session_ended",
        details={
            "session_id": str(session.id),
            "avg_fps": session.avg_fps,
        },
    )
    db.commit()
    db.refresh(session)
    return SessionOut.model_validate(session)
