from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ..dependencies import get_current_admin, get_db
from ..models import CanvasSession, SavedFrame, User
from ..schemas import (
    AdminMetrics,
    FrameOut,
    FramesPage,
    FramesPerUserItem,
    RecentActivityItem,
    RecentActivityResponse,
)
from ..services.storage import storage_service


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics", response_model=AdminMetrics)
def metrics(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdminMetrics:
    total_users = db.scalar(select(func.count(User.id))) or 0
    total_drawings = db.scalar(select(func.count(SavedFrame.id))) or 0

    avg_duration = db.scalar(
        select(func.avg(func.extract("epoch", CanvasSession.session_end - CanvasSession.session_start))).where(
            CanvasSession.session_end.is_not(None)
        )
    )
    average_session_duration_seconds = float(avg_duration or 0.0)

    rows = db.execute(
        select(User.id, User.name, func.count(SavedFrame.id).label("frames"))
        .outerjoin(SavedFrame, SavedFrame.user_id == User.id)
        .group_by(User.id, User.name)
        .order_by(desc("frames"), User.created_at.asc())
    ).all()

    frames_per_user = [
        FramesPerUserItem(user_id=row.id, name=row.name, frames=int(row.frames or 0)) for row in rows
    ]

    return AdminMetrics(
        total_users=int(total_users),
        total_drawings=int(total_drawings),
        average_session_duration_seconds=average_session_duration_seconds,
        frames_per_user=frames_per_user,
    )


@router.get("/recent-activity", response_model=RecentActivityResponse)
def recent_activity(
    limit: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> RecentActivityResponse:
    rows = db.execute(
        select(SavedFrame, User.name)
        .join(User, User.id == SavedFrame.user_id)
        .order_by(SavedFrame.created_at.desc())
        .limit(limit)
    ).all()

    items: list[RecentActivityItem] = []
    for frame, user_name in rows:
        preview = None
        if frame.thumbnail_url:
            preview = storage_service.generate_download_url_from_uri(frame.thumbnail_url)
        items.append(
            RecentActivityItem(
                frame_id=frame.id,
                user_id=frame.user_id,
                user_name=user_name,
                created_at=frame.created_at,
                brush_mode=frame.brush_mode,
                shape_mode=frame.shape_mode,
                preview_url=preview,
            )
        )

    return RecentActivityResponse(items=items)


@router.get("/gallery", response_model=FramesPage)
def gallery(
    limit: int = Query(default=50, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    user_id: uuid.UUID | None = Query(default=None),
    shape_mode: str | None = Query(default=None),
    brush_mode: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> FramesPage:
    statement = select(SavedFrame)
    count_statement = select(func.count(SavedFrame.id))

    if user_id is not None:
        statement = statement.where(SavedFrame.user_id == user_id)
        count_statement = count_statement.where(SavedFrame.user_id == user_id)
    if shape_mode:
        statement = statement.where(SavedFrame.shape_mode == shape_mode)
        count_statement = count_statement.where(SavedFrame.shape_mode == shape_mode)
    if brush_mode:
        statement = statement.where(SavedFrame.brush_mode == brush_mode)
        count_statement = count_statement.where(SavedFrame.brush_mode == brush_mode)
    if created_after is not None:
        statement = statement.where(SavedFrame.created_at >= created_after)
        count_statement = count_statement.where(SavedFrame.created_at >= created_after)
    if created_before is not None:
        statement = statement.where(SavedFrame.created_at <= created_before)
        count_statement = count_statement.where(SavedFrame.created_at <= created_before)

    total = db.scalar(count_statement) or 0
    frames = (
        db.execute(statement.order_by(SavedFrame.created_at.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )

    items: list[FrameOut] = []
    for frame in frames:
        frame_url = storage_service.generate_download_url_from_uri(frame.frame_url)
        thumbnail_url = None
        if frame.thumbnail_url:
            thumbnail_url = storage_service.generate_download_url_from_uri(frame.thumbnail_url)
        items.append(
            FrameOut(
                id=frame.id,
                user_id=frame.user_id,
                session_id=frame.session_id,
                frame_url=frame_url,
                thumbnail_url=thumbnail_url,
                created_at=frame.created_at,
                brush_mode=frame.brush_mode,
                shape_mode=frame.shape_mode,
            )
        )

    return FramesPage(total=int(total), items=items)

