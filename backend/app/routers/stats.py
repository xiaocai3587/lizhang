"""统计路由（仪表盘 + 回礼建议）"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Person, Event, Gift, GiftParticipant, Relation
from ..schemas import DashboardStats, GiftSuggestion
from ..services.suggestion import get_suggestions
from ..routers.events import _event_to_out


def _spouse_ids(db: Session, person_id: str) -> set[str]:
    """返回某人的配偶ID集合（双向配偶关系）"""
    rels = db.execute(
        select(Relation).where(
            Relation.type == "spouse",
            or_(Relation.from_id == person_id, Relation.to_id == person_id),
        )
    ).scalars().all()
    ids = set()
    for rel in rels:
        other = rel.to_id if rel.from_id == person_id else rel.from_id
        ids.add(other)
    return ids

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """仪表盘统计"""
    # 计数
    persons_count = db.execute(select(func.count()).select_from(Person)).scalar() or 0
    events_count = db.execute(select(func.count()).select_from(Event)).scalar() or 0
    gifts_count = db.execute(select(func.count()).select_from(Gift)).scalar() or 0

    # 收/送总额：join Event + Gift
    total_received = db.execute(
        select(func.coalesce(func.sum(Gift.amount), 0))
        .join(Event, Gift.event_id == Event.id)
        .where(Event.role == "received")
    ).scalar() or 0
    total_received = float(total_received)

    total_given = db.execute(
        select(func.coalesce(func.sum(Gift.amount), 0))
        .join(Event, Gift.event_id == Event.id)
        .where(Event.role == "given")
    ).scalar() or 0
    total_given = float(total_given)

    net = total_received - total_given

    # 最近 5 个事件（含 gift_count, gift_total）
    recent_events_rows = db.execute(
        select(Event).order_by(Event.date.desc()).limit(5)
    ).scalars().all()
    recent_events = []
    for e in recent_events_rows:
        out = _event_to_out(e, db)
        recent_events.append({
            "id": out.id,
            "title": out.title,
            "event_type": out.event_type,
            "date": out.date,
            "role": out.role,
            "gift_count": out.gift_count,
            "gift_total": out.gift_total,
        })

    # 往来金额最大的 5 个人（排除"我"及其配偶）
    all_persons = db.execute(select(Person)).scalars().all()
    # 找出"我"
    self_person = next((p for p in all_persons if p.is_self), None)
    excluded_ids: set[str] = set()
    if self_person:
        excluded_ids.add(self_person.id)
        excluded_ids |= _spouse_ids(db, self_person.id)

    person_totals = []
    for person in all_persons:
        if person.id in excluded_ids:
            continue
        participants = db.execute(
            select(GiftParticipant).where(GiftParticipant.person_id == person.id)
        ).scalars().all()
        total = 0.0
        for p in participants:
            gift = db.get(Gift, p.gift_id)
            if gift and gift.amount is not None:
                total += float(gift.amount)
        if total > 0:
            person_totals.append({
                "person_id": person.id,
                "name": person.name,
                "total_amount": round(total, 2),
            })
    person_totals.sort(key=lambda x: x["total_amount"], reverse=True)
    top_persons = person_totals[:5]

    # 按月统计收/送礼金
    all_events = db.execute(select(Event)).scalars().all()
    monthly_data: dict = {}
    for event in all_events:
        month = event.date[:7] if event.date else ""
        if not month:
            continue
        gifts = db.execute(select(Gift).where(Gift.event_id == event.id)).scalars().all()
        total = sum(float(g.amount) for g in gifts if g.amount is not None)
        bucket = monthly_data.setdefault(month, {"month": month, "received": 0.0, "given": 0.0})
        if event.role == "received":
            bucket["received"] += total
        elif event.role == "given":
            bucket["given"] += total
    monthly_trend = sorted(monthly_data.values(), key=lambda x: x["month"])
    # 四舍五入
    for m in monthly_trend:
        m["received"] = round(m["received"], 2)
        m["given"] = round(m["given"], 2)

    return DashboardStats(
        persons_count=persons_count,
        events_count=events_count,
        gifts_count=gifts_count,
        total_received=round(total_received, 2),
        total_given=round(total_given, 2),
        net=round(net, 2),
        recent_events=recent_events,
        top_persons=top_persons,
        monthly_trend=monthly_trend,
    )


@router.get("/suggestions", response_model=List[GiftSuggestion])
def get_suggestions_route(db: Session = Depends(get_db)):
    """回礼建议"""
    return get_suggestions(db)
