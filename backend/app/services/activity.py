from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from ..models import ActivityEvent


def record_activity(
    db: Session,
    *,
    user_id: uuid.UUID,
    activity_type: str,
    details: dict | None = None,
) -> None:
    db.add(ActivityEvent(user_id=user_id, activity_type=activity_type, details=details))
