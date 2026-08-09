"""图谱路由（族谱 + 朋友图谱）"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Person
from ..schemas import GraphData, HouseholdGraphData
from ..services.family_tree import build_family_tree
from ..services.friend_graph import build_friend_graph

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/family", response_model=HouseholdGraphData)
def get_family_tree(anchor_id: str = "", group: str = "", db: Session = Depends(get_db)):
    """获取家庭单元族谱图数据

    - anchor_id 为空时，用 is_self=True 的人作为锚点
    - group 可选过滤分组
    - 以夫妻对(household)为节点，展示双方兄弟姐妹
    """
    if not anchor_id:
        anchor = db.execute(select(Person).where(Person.is_self == True)).scalars().first()
        if not anchor:
            return HouseholdGraphData(nodes=[], links=[])
        anchor_id = anchor.id

    data = build_family_tree(db, anchor_id, group if group else None)
    return HouseholdGraphData(**data)


@router.get("/friends", response_model=GraphData)
def get_friend_graph(db: Session = Depends(get_db)):
    """获取朋友图谱数据"""
    data = build_friend_graph(db)
    return GraphData(**data)
