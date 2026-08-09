"""礼金管理路由"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Gift, GiftParticipant, Person
from ..schemas import GiftCreate, GiftOut

router = APIRouter(prefix="/api/gifts", tags=["gifts"])


def _gift_to_out(gift: Gift, db: Session) -> GiftOut:
    """将 Gift 转为 GiftOut，附带 participants 列表"""
    participants = db.execute(
        select(GiftParticipant).where(GiftParticipant.gift_id == gift.id)
    ).scalars().all()
    parts_list = []
    for p in participants:
        person = db.get(Person, p.person_id)
        parts_list.append({
            "person_id": p.person_id,
            "person_name": person.name if person else "",
            "role": p.role,
        })
    return GiftOut(
        id=gift.id,
        event_id=gift.event_id,
        amount=float(gift.amount) if gift.amount is not None else 0.0,
        is_shared=gift.is_shared,
        notes=gift.notes or "",
        participants=parts_list,
    )


@router.get("", response_model=List[GiftOut])
def list_gifts(event_id: str = "", person_id: str = "", db: Session = Depends(get_db)):
    """列出礼金

    - event_id: 按事件过滤
    - person_id: 按参与人过滤（通过 GiftParticipant）
    """
    if person_id:
        # 查涉及此人的礼金
        participant_rows = db.execute(
            select(GiftParticipant.gift_id).where(GiftParticipant.person_id == person_id)
        ).all()
        gift_ids = [r[0] for r in participant_rows]
        if not gift_ids:
            return []
        stmt = select(Gift).where(Gift.id.in_(gift_ids))
    else:
        stmt = select(Gift)

    if event_id:
        stmt = stmt.where(Gift.event_id == event_id)

    stmt = stmt.order_by(Gift.created_at.desc())
    gifts = db.execute(stmt).scalars().all()
    return [_gift_to_out(g, db) for g in gifts]


@router.post("", response_model=GiftOut)
def create_gift(data: GiftCreate, db: Session = Depends(get_db)):
    """创建礼金 + 关联的 GiftParticipant 记录"""
    gift = Gift(
        event_id=data.event_id,
        amount=data.amount,
        is_shared=data.is_shared,
        notes=data.notes,
    )
    db.add(gift)
    db.flush()  # 拿到 gift.id

    for part in data.participants:
        gp = GiftParticipant(
            gift_id=gift.id,
            person_id=part.person_id,
            role=part.role,
        )
        db.add(gp)

    db.commit()
    db.refresh(gift)
    return _gift_to_out(gift, db)


@router.put("/{gift_id}", response_model=GiftOut)
def update_gift(gift_id: str, data: GiftCreate, db: Session = Depends(get_db)):
    """更新礼金，删除旧 participants，创建新的"""
    gift = db.get(Gift, gift_id)
    if not gift:
        raise HTTPException(status_code=404, detail="礼金不存在")

    gift.event_id = data.event_id
    gift.amount = data.amount
    gift.is_shared = data.is_shared
    gift.notes = data.notes

    # 删除旧 participants
    old_parts = db.execute(
        select(GiftParticipant).where(GiftParticipant.gift_id == gift_id)
    ).scalars().all()
    for op in old_parts:
        db.delete(op)

    # 创建新 participants
    for part in data.participants:
        gp = GiftParticipant(
            gift_id=gift_id,
            person_id=part.person_id,
            role=part.role,
        )
        db.add(gp)

    db.commit()
    db.refresh(gift)
    return _gift_to_out(gift, db)


@router.delete("/{gift_id}")
def delete_gift(gift_id: str, db: Session = Depends(get_db)):
    """删除礼金（级联删除其 participants）"""
    gift = db.get(Gift, gift_id)
    if not gift:
        raise HTTPException(status_code=404, detail="礼金不存在")
    db.delete(gift)
    db.commit()
    return {"ok": True}
