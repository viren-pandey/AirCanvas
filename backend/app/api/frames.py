from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import get_current_user, get_db
from ..limiter import limiter
from ..models import CanvasSession, SavedFrame, User
from ..schemas import (
    FrameCompleteResponse,
    FrameOut,
    FramesPage,
    FrameUploadUrlRequest,
    FrameUploadUrlResponse,
)
from ..services.activity import record_activity
from ..services.storage import storage_service


router = APIRouter(prefix="/frames", tags=["frames"])


@router.post(
    "/upload-url",
    response_model=FrameUploadUrlResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("120/minute")
def create_upload_url(
    request: Request,
    payload: FrameUploadUrlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FrameUploadUrlResponse:
    session_id = payload.session_id
    if session_id is not None:
        session = db.get(CanvasSession, session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    frame_key = storage_service.build_frame_key(current_user.id, extension=payload.frame_extension)
    thumb_key = storage_service.build_thumbnail_key(
        current_user.id, extension=payload.thumbnail_extension
    )

    frame = SavedFrame(
        user_id=current_user.id,
        session_id=session_id,
        frame_url=storage_service.object_uri(frame_key),
        thumbnail_url=storage_service.object_uri(thumb_key),
        brush_mode=payload.brush_mode,
        shape_mode=payload.shape_mode,
    )
    db.add(frame)
    db.flush()
    record_activity(
        db,
        user_id=current_user.id,
        activity_type="frame_upload_requested",
        details={
            "frame_id": str(frame.id),
            "session_id": str(session_id) if session_id else None,
            "brush_mode": payload.brush_mode,
            "shape_mode": payload.shape_mode,
        },
    )
    db.commit()
    db.refresh(frame)

    return FrameUploadUrlResponse(
        frame_id=frame.id,
        frame_object_key=frame_key,
        thumbnail_object_key=thumb_key,
        frame_upload_url=storage_service.generate_upload_url(frame_key, "image/png"),
        thumbnail_upload_url=storage_service.generate_upload_url(thumb_key, "image/jpeg"),
        expires_in=settings.signed_url_ttl_seconds,
    )


@router.post("/{frame_id}/complete", response_model=FrameCompleteResponse)
@limiter.limit("180/minute")
def complete_upload(
    request: Request,
    frame_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FrameCompleteResponse:
    frame = db.get(SavedFrame, frame_id)
    if frame is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frame not found")
    if frame.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    frame_url = storage_service.generate_download_url_from_uri(frame.frame_url)
    thumbnail_url = None
    if frame.thumbnail_url:
        thumbnail_url = storage_service.generate_download_url_from_uri(frame.thumbnail_url)

    record_activity(
        db,
        user_id=current_user.id,
        activity_type="frame_upload_completed",
        details={
            "frame_id": str(frame.id),
            "session_id": str(frame.session_id) if frame.session_id else None,
            "brush_mode": frame.brush_mode,
            "shape_mode": frame.shape_mode,
        },
    )
    db.commit()

    return FrameCompleteResponse(
        id=frame.id,
        frame_url=frame_url,
        thumbnail_url=thumbnail_url,
        created_at=frame.created_at,
    )


@router.get("", response_model=FramesPage)
def list_frames(
    limit: int = Query(default=30, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session_id: uuid.UUID | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FramesPage:
    statement = select(SavedFrame)
    count_statement = select(func.count(SavedFrame.id))

    if current_user.is_admin:
        if user_id is not None:
            statement = statement.where(SavedFrame.user_id == user_id)
            count_statement = count_statement.where(SavedFrame.user_id == user_id)
    else:
        statement = statement.where(SavedFrame.user_id == current_user.id)
        count_statement = count_statement.where(SavedFrame.user_id == current_user.id)

    if session_id is not None:
        statement = statement.where(SavedFrame.session_id == session_id)
        count_statement = count_statement.where(SavedFrame.session_id == session_id)

    total = db.scalar(count_statement) or 0
    frames = (
        db.execute(statement.order_by(SavedFrame.created_at.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )

    items: list[FrameOut] = []
    for frame in frames:
        signed_frame = storage_service.generate_download_url_from_uri(frame.frame_url)
        signed_thumb = None
        if frame.thumbnail_url:
            signed_thumb = storage_service.generate_download_url_from_uri(frame.thumbnail_url)
        items.append(
            FrameOut(
                id=frame.id,
                user_id=frame.user_id,
                session_id=frame.session_id,
                frame_url=signed_frame,
                thumbnail_url=signed_thumb,
                created_at=frame.created_at,
                brush_mode=frame.brush_mode,
                shape_mode=frame.shape_mode,
            )
        )

    return FramesPage(total=total, items=items)
