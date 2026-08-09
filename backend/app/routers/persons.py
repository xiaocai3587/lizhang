"""人物管理路由"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Person, GiftParticipant, Gift, Event
from ..schemas import PersonCreate, PersonUpdate, PersonOut, PersonStats

router = APIRouter(prefix="/api/persons", tags=["persons"])


@router.get("", response_model=List[PersonOut])
def list_persons(search: str = "", group: str = "", db: Session = Depends(get_db)):
    """列出人物，可按姓名搜索、按分组过滤"""
    stmt = select(Person)
    if search:
        stmt = stmt.where(Person.name.like(f"%{search}%"))
    if group:
        stmt = stmt.where(Person.group == group)
    stmt = stmt.order_by(Person.created_at.desc())
    persons = db.execute(stmt).scalars().all()
    return persons


@router.post("", response_model=PersonOut)
def create_person(data: PersonCreate, db: Session = Depends(get_db)):
    """创建人物"""
    person = Person(
        name=data.name,
        nickname=data.nickname,
        group=data.group,
        gender=data.gender,
        birth_year=data.birth_year,
        is_self=data.is_self,
        title=data.title,
        gift_status=data.gift_status,
        notes=data.notes,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.get("/{person_id}", response_model=PersonOut)
def get_person(person_id: str, db: Session = Depends(get_db)):
    """获取单个人物"""
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="人物不存在")
    return person


@router.put("/{person_id}", response_model=PersonOut)
def update_person(person_id: str, data: PersonUpdate, db: Session = Depends(get_db)):
    """更新人物信息"""
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="人物不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(person, key, value)
    db.commit()
    db.refresh(person)
    return person


@router.delete("/{person_id}")
def delete_person(person_id: str, db: Session = Depends(get_db)):
    """删除人物（级联删除其关联的关系和礼金参与者记录）"""
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="人物不存在")
    db.delete(person)
    db.commit()
    return {"ok": True}


@router.get("/{person_id}/stats", response_model=PersonStats)
def get_person_stats(person_id: str, db: Session = Depends(get_db)):
    """统计某人物的礼金往来

    - total_gave: 此人给我随的钱（event.role=received 且 participant.role=giver）
    - total_received: 我给此人随的钱（event.role=given 且 participant.role=receiver）
    - net: total_gave - total_received
    - gift_count: 涉及此人的礼金数
    """
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="人物不存在")

    participants = db.execute(
        select(GiftParticipant).where(GiftParticipant.person_id == person_id)
    ).scalars().all()

    total_gave = 0.0
    total_received = 0.0
    seen_gift_ids = set()

    for p in participants:
        gift = db.get(Gift, p.gift_id)
        if not gift:
            continue
        if gift.id not in seen_gift_ids:
            seen_gift_ids.add(gift.id)
        event = db.get(Event, gift.event_id)
        if not event:
            continue
        amount = float(gift.amount) if gift.amount is not None else 0.0
        # received 事件 + giver → 此人给我随钱
        if event.role == "received" and p.role == "giver":
            total_gave += amount
        # given 事件 + receiver → 我给此人随钱
        elif event.role == "given" and p.role == "receiver":
            total_received += amount

    return PersonStats(
        total_gave=round(total_gave, 2),
        total_received=round(total_received, 2),
        net=round(total_gave - total_received, 2),
        gift_count=len(seen_gift_ids),
    )
