"""关系管理路由"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Relation, Person
from ..schemas import RelationCreate, RelationOut

router = APIRouter(prefix="/api/relations", tags=["relations"])


@router.get("", response_model=List[RelationOut])
def list_relations(person_id: str = "", db: Session = Depends(get_db)):
    """列出关系，可按 person_id 过滤（from_id 或 to_id 匹配）

    返回 from_name 和 to_name
    """
    stmt = select(Relation)
    if person_id:
        stmt = stmt.where(or_(Relation.from_id == person_id, Relation.to_id == person_id))
    relations = db.execute(stmt).scalars().all()

    result = []
    for r in relations:
        from_person = db.get(Person, r.from_id)
        to_person = db.get(Person, r.to_id)
        result.append(RelationOut(
            id=r.id,
            from_id=r.from_id,
            to_id=r.to_id,
            type=r.type,
            notes=r.notes or "",
            from_name=from_person.name if from_person else "",
            to_name=to_person.name if to_person else "",
        ))
    return result


@router.post("", response_model=RelationOut)
def create_relation(data: RelationCreate, db: Session = Depends(get_db)):
    """创建关系"""
    relation = Relation(
        from_id=data.from_id,
        to_id=data.to_id,
        type=data.type,
        notes=data.notes,
    )
    db.add(relation)
    db.commit()
    db.refresh(relation)

    from_person = db.get(Person, relation.from_id)
    to_person = db.get(Person, relation.to_id)
    return RelationOut(
        id=relation.id,
        from_id=relation.from_id,
        to_id=relation.to_id,
        type=relation.type,
        notes=relation.notes or "",
        from_name=from_person.name if from_person else "",
        to_name=to_person.name if to_person else "",
    )


@router.delete("/{relation_id}")
def delete_relation(relation_id: str, db: Session = Depends(get_db)):
    """删除关系"""
    relation = db.get(Relation, relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="关系不存在")
    db.delete(relation)
    db.commit()
    return {"ok": True}
