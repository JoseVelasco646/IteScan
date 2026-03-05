from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import AuditLog
from app.auth import require_role

router = APIRouter()


@router.get("/api/audit")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    action: Optional[str] = None,
    username: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    _role=Depends(require_role("admin"))
):
    query = db.query(AuditLog)

    if category:
        query = query.filter(AuditLog.category == category)
    if action:
        query = query.filter(AuditLog.action == action)
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))
    if date_from:
        try:
            from_dt = datetime.fromisoformat(date_from)
            query = query.filter(AuditLog.created_at >= from_dt)
        except ValueError:
            pass
    if date_to:
        try:
            to_dt = datetime.fromisoformat(date_to)
            query = query.filter(AuditLog.created_at <= to_dt)
        except ValueError:
            pass

    total = query.count()
    entries = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": e.id,
                "user_id": e.user_id,
                "username": e.username,
                "action": e.action,
                "category": e.category,
                "description": e.description,
                "details": e.details,
                "ip_address": e.ip_address,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ]
    }


@router.get("/api/audit/stats")
async def get_audit_stats(db: Session = Depends(get_db), _role=Depends(require_role("admin"))):
    total = db.query(AuditLog).count()

    by_category = db.query(
        AuditLog.category, func.count(AuditLog.id)
    ).group_by(AuditLog.category).all()

    by_action = db.query(
        AuditLog.action, func.count(AuditLog.id)
    ).group_by(AuditLog.action).all()

    by_user = db.query(
        AuditLog.username, func.count(AuditLog.id)
    ).filter(AuditLog.username.isnot(None)).group_by(AuditLog.username).all()

    return {
        "total": total,
        "by_category": {cat: count for cat, count in by_category},
        "by_action": {act: count for act, count in by_action},
        "by_user": {user: count for user, count in by_user},
    }
