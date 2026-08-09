"""朋友图谱算法

聚合 friends 分组的人物节点、friend 类型关系，
并将朋友间的礼金往来作为额外的边（type=gift），节点累计金额用于节点大小。
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Person, Relation, Gift, GiftParticipant


def build_friend_graph(db: Session) -> dict:
    """构建朋友图谱

    Returns:
        {"nodes": [...], "links": [...]}
    """
    # 所有 friends 分组的人
    persons = db.execute(select(Person).where(Person.group == "friends")).scalars().all()
    person_ids = {p.id for p in persons}

    # friend 类型的关系
    relations = db.execute(select(Relation).where(Relation.type == "friend")).scalars().all()

    # 聚合礼金金额: (id1, id2) -> total_amount
    gift_amounts: dict = {}

    nodes = [
        {
            "id": p.id,
            "name": p.name,
            "gender": p.gender,
            "group": "friends",
            "is_self": p.is_self,
            "birth_year": p.birth_year,
            "depth": 0,
            "total_amount": 0.0,
        }
        for p in persons
    ]

    # friend 关系作为实线边
    links: list = []
    for r in relations:
        # 只在两端都是 friend 时才画
        if r.from_id in person_ids and r.to_id in person_ids:
            links.append({"source": r.from_id, "target": r.to_id, "type": "friend"})

    # 礼金往来作为虚线边（type=gift）
    gifts = db.execute(select(Gift)).scalars().all()
    for g in gifts:
        participants = db.execute(
            select(GiftParticipant).where(GiftParticipant.gift_id == g.id)
        ).scalars().all()
        givers = [p.person_id for p in participants if p.role == "giver" and p.person_id in person_ids]
        receivers = [p.person_id for p in participants if p.role == "receiver" and p.person_id in person_ids]
        amount = float(g.amount) if g.amount is not None else 0.0
        for gv in givers:
            for rc in receivers:
                if gv != rc:
                    key = tuple(sorted([gv, rc]))
                    gift_amounts[key] = gift_amounts.get(key, 0.0) + amount

    for (id1, id2), amount in gift_amounts.items():
        links.append({"source": id1, "target": id2, "type": "gift", "amount": amount})

    # 更新节点 total_amount（用于节点大小可视化）
    for node in nodes:
        total = 0.0
        for (id1, id2), amount in gift_amounts.items():
            if node["id"] in (id1, id2):
                total += amount
        node["total_amount"] = total

    return {"nodes": nodes, "links": links}
