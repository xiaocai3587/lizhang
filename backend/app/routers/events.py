"""事件管理路由"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event, Gift
from ..schemas import EventCreate, EventUpdate, EventOut

router = APIRouter(prefix="/api/events", tags=["events"])


def _event_to_out(event: Event, db: Session) -> EventOut:
    """将 Event 转为 EventOut，并计算 gift_count / gift_total"""
    gifts = db.execute(select(Gift).where(Gift.event_id == event.id)).scalars().all()
    gift_count = len(gifts)
    gift_total = sum(float(g.amount) for g in gifts if g.amount is not None)
    return EventOut(
        id=event.id,
        title=event.title,
        event_type=event.event_type,
        date=event.date,
        role=event.role,
        notes=event.notes,
        gift_count=gift_count,
        gift_total=round(gift_total, 2),
    )


@router.get("", response_model=List[EventOut])
def list_events(search: str = "", role: str = "", db: Session = Depends(get_db)):
    """列出事件，按日期降序，可按标题搜索、按角色过滤"""
    stmt = select(Event)
    if search:
        stmt = stmt.where(Event.title.like(f"%{search}%"))
    if role:
        stmt = stmt.where(Event.role == role)
    stmt = stmt.order_by(Event.date.desc())
    events = db.execute(stmt).scalars().all()
    return [_event_to_out(e, db) for e in events]


@router.post("", response_model=EventOut)
def create_event(data: EventCreate, db: Session = Depends(get_db)):
    """创建事件"""
    event = Event(
        title=data.title,
        event_type=data.event_type,
        date=data.date,
        role=data.role,
        notes=data.notes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _event_to_out(event, db)


# /types 必须在 /{event_id} 之前定义，否则会被当成 event_id
@router.get("/types", response_model=List[str])
def get_all_event_types(db: Session = Depends(get_db)):
    """返回去重的 event_type 列表"""
    rows = db.execute(select(distinct(Event.event_type)).where(Event.event_type != "")).all()
    return [r[0] for r in rows if r[0]]


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    """获取单个事件（含 gift_count 和 gift_total）"""
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    return _event_to_out(event, db)


@router.put("/{event_id}", response_model=EventOut)
def update_event(event_id: str, data: EventUpdate, db: Session = Depends(get_db)):
    """更新事件"""
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return _event_to_out(event, db)


@router.delete("/{event_id}")
def delete_event(event_id: str, db: Session = Depends(get_db)):
    """删除事件（级联删除其下所有礼金）"""
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    db.delete(event)
    db.commit()
    return {"ok": True}
