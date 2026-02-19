from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Float, and_, cast, func, select
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models import (
    ActivityEvent,
    CommunityPost,
    CommunityPostComment,
    CommunityPostVote,
    User,
)
from ..schemas import (
    ActivityEventOut,
    ActivityEventsPage,
    CommunityCommentCreate,
    CommunityCommentOut,
    CommunityCommentsPage,
    CommunityPostCreate,
    CommunityPostOut,
    CommunityPostsPage,
    CommunityVoteRequest,
)
from ..services.activity import record_activity


router = APIRouter(prefix="/community", tags=["community"])


def _build_title(title: str, content: str) -> str:
    cleaned = title.strip()
    if cleaned:
        return cleaned[:220]
    for line in content.splitlines():
        line = line.strip()
        if line:
            return line[:220]
    return "Untitled post"


@router.get("/posts", response_model=CommunityPostsPage)
def list_posts(
    limit: int = Query(default=30, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="hot", pattern="^(hot|new|top)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommunityPostsPage:
    total = db.scalar(select(func.count(CommunityPost.id))) or 0

    comment_counts = (
        select(
            CommunityPostComment.post_id.label("post_id"),
            func.count(CommunityPostComment.id).label("comment_count"),
        )
        .group_by(CommunityPostComment.post_id)
        .subquery()
    )

    user_vote = CommunityPostVote
    statement = (
        select(
            CommunityPost,
            User.name.label("user_name"),
            func.coalesce(comment_counts.c.comment_count, 0).label("comment_count"),
            func.coalesce(user_vote.vote_value, 0).label("user_vote"),
        )
        .join(User, User.id == CommunityPost.user_id)
        .outerjoin(comment_counts, comment_counts.c.post_id == CommunityPost.id)
        .outerjoin(
            user_vote,
            and_(user_vote.post_id == CommunityPost.id, user_vote.user_id == current_user.id),
        )
    )

    if sort == "new":
        statement = statement.order_by(CommunityPost.created_at.desc())
    elif sort == "top":
        statement = statement.order_by(CommunityPost.score.desc(), CommunityPost.created_at.desc())
    else:
        age_hours = func.greatest(
            cast(func.extract("epoch", func.now() - CommunityPost.created_at) / 3600.0, Float),
            0.0,
        )
        hot_rank = (CommunityPost.score * 4.0) - (age_hours / 6.0)
        statement = statement.order_by(hot_rank.desc(), CommunityPost.created_at.desc())

    rows = db.execute(statement.offset(offset).limit(limit)).all()
    items = [
        CommunityPostOut(
            id=post.id,
            user_id=post.user_id,
            user_name=user_name,
            title=post.title,
            content=post.content,
            score=int(post.score or 0),
            comment_count=int(comment_count or 0),
            user_vote=int(user_vote_value or 0),
            created_at=post.created_at,
        )
        for post, user_name, comment_count, user_vote_value in rows
    ]
    return CommunityPostsPage(total=int(total), items=items)


@router.post("/posts", response_model=CommunityPostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: CommunityPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommunityPostOut:
    title = _build_title(payload.title, payload.content)
    post = CommunityPost(user_id=current_user.id, title=title, content=payload.content)
    db.add(post)
    db.flush()
    record_activity(
        db,
        user_id=current_user.id,
        activity_type="community_post_created",
        details={
            "post_id": str(post.id),
            "title": title,
            "content_preview": payload.content[:160],
        },
    )
    db.commit()
    db.refresh(post)

    return CommunityPostOut(
        id=post.id,
        user_id=post.user_id,
        user_name=current_user.name,
        title=post.title,
        content=post.content,
        score=int(post.score or 0),
        comment_count=0,
        user_vote=0,
        created_at=post.created_at,
    )


@router.post("/posts/{post_id}/vote", response_model=CommunityPostOut)
def vote_post(
    post_id: uuid.UUID,
    payload: CommunityVoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommunityPostOut:
    post = db.get(CommunityPost, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    existing_vote = db.scalar(
        select(CommunityPostVote).where(
            CommunityPostVote.post_id == post.id,
            CommunityPostVote.user_id == current_user.id,
        )
    )
    previous_value = int(existing_vote.vote_value) if existing_vote is not None else 0
    next_value = int(payload.value)
    delta = next_value - previous_value

    if existing_vote is None and next_value != 0:
        db.add(
            CommunityPostVote(
                post_id=post.id,
                user_id=current_user.id,
                vote_value=next_value,
            )
        )
    elif existing_vote is not None:
        if next_value == 0:
            db.delete(existing_vote)
        else:
            existing_vote.vote_value = next_value

    if delta != 0:
        post.score = int(post.score or 0) + delta
        record_activity(
            db,
            user_id=current_user.id,
            activity_type="community_post_voted",
            details={
                "post_id": str(post.id),
                "vote_value": next_value,
                "score_after": int(post.score),
            },
        )

    db.commit()
    db.refresh(post)

    comment_count = (
        db.scalar(select(func.count(CommunityPostComment.id)).where(CommunityPostComment.post_id == post.id))
        or 0
    )
    post_owner_name = db.scalar(select(User.name).where(User.id == post.user_id)) or "Unknown"
    return CommunityPostOut(
        id=post.id,
        user_id=post.user_id,
        user_name=post_owner_name,
        title=post.title,
        content=post.content,
        score=int(post.score or 0),
        comment_count=int(comment_count),
        user_vote=next_value,
        created_at=post.created_at,
    )


@router.get("/posts/{post_id}/comments", response_model=CommunityCommentsPage)
def list_comments(
    post_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CommunityCommentsPage:
    post = db.get(CommunityPost, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    total = (
        db.scalar(
            select(func.count(CommunityPostComment.id)).where(CommunityPostComment.post_id == post_id)
        )
        or 0
    )
    rows = db.execute(
        select(CommunityPostComment, User.name)
        .join(User, User.id == CommunityPostComment.user_id)
        .where(CommunityPostComment.post_id == post_id)
        .order_by(CommunityPostComment.created_at.asc())
        .offset(offset)
        .limit(limit)
    ).all()

    items = [
        CommunityCommentOut(
            id=comment.id,
            post_id=comment.post_id,
            user_id=comment.user_id,
            user_name=user_name,
            parent_comment_id=comment.parent_comment_id,
            content=comment.content,
            created_at=comment.created_at,
        )
        for comment, user_name in rows
    ]
    return CommunityCommentsPage(total=int(total), items=items)


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommunityCommentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: uuid.UUID,
    payload: CommunityCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommunityCommentOut:
    post = db.get(CommunityPost, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if payload.parent_comment_id is not None:
        parent = db.get(CommunityPostComment, payload.parent_comment_id)
        if parent is None or parent.post_id != post_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid parent comment",
            )

    comment = CommunityPostComment(
        post_id=post_id,
        user_id=current_user.id,
        parent_comment_id=payload.parent_comment_id,
        content=payload.content,
    )
    db.add(comment)
    db.flush()
    record_activity(
        db,
        user_id=current_user.id,
        activity_type="community_comment_created",
        details={
            "post_id": str(post_id),
            "comment_id": str(comment.id),
            "content_preview": payload.content[:120],
        },
    )
    db.commit()
    db.refresh(comment)

    return CommunityCommentOut(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        user_name=current_user.name,
        parent_comment_id=comment.parent_comment_id,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.get("/activity", response_model=ActivityEventsPage)
def list_activity(
    limit: int = Query(default=40, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivityEventsPage:
    target_user_id = current_user.id
    if current_user.is_admin and user_id is not None:
        target_user_id = user_id

    count_statement = select(func.count(ActivityEvent.id)).where(ActivityEvent.user_id == target_user_id)
    statement = (
        select(ActivityEvent)
        .where(ActivityEvent.user_id == target_user_id)
        .order_by(ActivityEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    total = db.scalar(count_statement) or 0
    events = db.execute(statement).scalars().all()
    items = [
        ActivityEventOut(
            id=item.id,
            user_id=item.user_id,
            activity_type=item.activity_type,
            details=item.details,
            created_at=item.created_at,
        )
        for item in events
    ]
    return ActivityEventsPage(total=int(total), items=items)
