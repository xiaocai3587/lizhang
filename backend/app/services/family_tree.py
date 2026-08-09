"""族谱展开算法（家庭单元版 + 左右分区）

以"夫妻对"(household)为基本单元展开族谱：
- 一个 household = 一对夫妻（或单人）
- 从锚点夫妻出发，向上找双方的父母家庭、向下找子女家庭、横向找双方的兄弟姐妹
- 每个人标记 person_side: paternal(父系左) / maternal(母系右) / self(中间)
- 家庭 side 用于布局：成员 side 一致则取该 side，混合(如父母)则取 self
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from ..models import Person, Relation


def _get_spouse(db: Session, person_id: str) -> Optional[Person]:
    rels = db.execute(
        select(Relation).where(
            Relation.type == "spouse",
            or_(Relation.from_id == person_id, Relation.to_id == person_id),
        )
    ).scalars().all()
    for rel in rels:
        other_id = rel.to_id if rel.from_id == person_id else rel.from_id
        sp = db.get(Person, other_id)
        if sp:
            return sp
    return None


def _get_parents(db: Session, person_id: str) -> list[Person]:
    rels = db.execute(
        select(Relation).where(
            Relation.type == "parent_child", Relation.to_id == person_id
        )
    ).scalars().all()
    parents = []
    for rel in rels:
        p = db.get(Person, rel.from_id)
        if p:
            parents.append(p)
    return parents


def _get_children(db: Session, person_id: str) -> list[Person]:
    rels = db.execute(
        select(Relation).where(
            Relation.type == "parent_child", Relation.from_id == person_id
        )
    ).scalars().all()
    children = []
    for rel in rels:
        c = db.get(Person, rel.to_id)
        if c:
            children.append(c)
    return children


def _get_siblings(db: Session, person_id: str) -> list[Person]:
    parents = _get_parents(db, person_id)
    siblings = []
    seen = {person_id}
    for parent in parents:
        for child_rel in db.execute(
            select(Relation).where(
                Relation.type == "parent_child",
                Relation.from_id == parent.id,
            )
        ).scalars().all():
            if child_rel.to_id not in seen:
                sib = db.get(Person, child_rel.to_id)
                if sib:
                    siblings.append(sib)
                    seen.add(sib.id)
    return siblings


def _make_household_id(person_ids: list[str]) -> str:
    return "h_" + "_".join(sorted(person_ids))


def _person_to_dict(p: Person, title: str = "") -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "nickname": p.nickname or "",
        "gender": p.gender,
        "group": p.group,
        "is_self": p.is_self,
        "birth_year": p.birth_year,
        "title": title,
    }


def build_family_tree(db: Session, anchor_id: str, group: Optional[str] = None) -> dict:
    """构建家庭单元族谱图数据（含左右分区 side）"""
    anchor = db.get(Person, anchor_id)
    if not anchor:
        return {"nodes": [], "links": []}

    # 预计算称谓（从锚点出发）
    from .kinship import compute_titles
    titles: dict = compute_titles(db, anchor_id)

    nodes: dict = {}
    links: list = []
    visited_persons: set = set()
    person_side: dict = {}  # person_id -> 'paternal'/'maternal'/'self'

    def family_side_for(member_ids: list[str]) -> str:
        """根据成员的 person_side 决定家庭的 side"""
        sides = [person_side.get(pid, "self") for pid in member_ids]
        if all(s == "paternal" for s in sides):
            return "paternal"
        if all(s == "maternal" for s in sides):
            return "maternal"
        return "self"  # 混合（如锚点父母：父亲 paternal + 母亲 maternal）

    def add_household(person: Person, depth: int, is_anchor: bool = False) -> Optional[str]:
        if person.id in visited_persons:
            return None
        spouse = _get_spouse(db, person.id)
        member_ids = sorted([person.id] + ([spouse.id] if spouse else []))
        hid = _make_household_id(member_ids)

        if hid not in nodes:
            members = [_person_to_dict(person, titles.get(person.id, ""))]
            if spouse:
                members.append(_person_to_dict(spouse, titles.get(spouse.id, "")))
            nodes[hid] = {
                "id": hid,
                "members": members,
                "depth": depth,
                "is_anchor": is_anchor,
                "side": family_side_for(member_ids),
            }
            visited_persons.add(person.id)
            if spouse:
                visited_persons.add(spouse.id)
        return hid

    def add_link(source_hid: str, target_hid: str) -> None:
        for l in links:
            if l["source"] == source_hid and l["target"] == target_hid:
                return
        links.append({"source": source_hid, "target": target_hid, "type": "parent_child"})

    def walk_up(person: Person, child_hid: str, side: str, depth: int = 1, max_depth: int = 5) -> None:
        if depth > max_depth:
            return
        parents = _get_parents(db, person.id)
        for parent in parents:
            person_side[parent.id] = side  # 标记此人的 side
            # 配偶也标记（同 side）
            sp = _get_spouse(db, parent.id)
            if sp and sp.id not in person_side:
                person_side[sp.id] = side
            parent_hid = add_household(parent, -depth)
            if parent_hid and parent_hid != child_hid:
                add_link(parent_hid, child_hid)
            if parent_hid:
                walk_up(parent, parent_hid, side, depth + 1, max_depth)
            else:
                existing = _make_household_id(sorted([parent.id] + ([sp.id] if sp else [])))
                if existing in nodes:
                    walk_up(parent, existing, side, depth + 1, max_depth)

    def walk_down(person: Person, parent_hid: str, side: str, depth: int = 1, max_depth: int = 3) -> None:
        if depth > max_depth:
            return
        children = _get_children(db, person.id)
        for child in children:
            person_side[child.id] = side
            sp = _get_spouse(db, child.id)
            if sp and sp.id not in person_side:
                person_side[sp.id] = side
            child_hid = add_household(child, depth)
            if child_hid and child_hid != parent_hid:
                add_link(parent_hid, child_hid)
                walk_down(child, child_hid, side, depth + 1, max_depth)

    def walk_siblings(person: Person, depth: int, side: str) -> None:
        siblings = _get_siblings(db, person.id)
        for sib in siblings:
            person_side[sib.id] = side
            sp = _get_spouse(db, sib.id)
            if sp and sp.id not in person_side:
                person_side[sp.id] = side
            sib_hid = add_household(sib, depth)
            if sib_hid:
                sib_parents = _get_parents(db, sib.id)
                for sparent in sib_parents:
                    for hid, node in nodes.items():
                        if any(m["id"] == sparent.id for m in node["members"]):
                            add_link(hid, sib_hid)
                            break

    def get_hid_of_person(person_id: str) -> Optional[str]:
        for hid, node in nodes.items():
            if any(m["id"] == person_id for m in node["members"]):
                return hid
        return None

    def refresh_family_sides() -> None:
        """重新计算所有家庭的 side（person_side 更新后）"""
        for node in nodes.values():
            member_ids = [m["id"] for m in node["members"]]
            node["side"] = family_side_for(member_ids)

    def expand_all_siblings() -> None:
        persons_to_expand = []
        for node in list(nodes.values()):
            for m in node["members"]:
                persons_to_expand.append((m["id"], node["depth"], person_side.get(m["id"], "self")))
        for pid, depth, side in persons_to_expand:
            p = db.get(Person, pid)
            if p:
                walk_siblings(p, depth, side)

    def expand_all_children() -> None:
        persons_to_expand = []
        for node in list(nodes.values()):
            for m in node["members"]:
                persons_to_expand.append((m["id"], node["depth"], person_side.get(m["id"], "self")))
        for pid, depth, side in persons_to_expand:
            p = db.get(Person, pid)
            if p:
                hid = get_hid_of_person(pid)
                if hid:
                    walk_down(p, hid, side, depth + 1)

    # ── 主流程 ──
    # 1. 锚点
    person_side[anchor.id] = "self"
    anchor_spouse = _get_spouse(db, anchor.id)
    if anchor_spouse:
        person_side[anchor_spouse.id] = "self"
    anchor_hid = add_household(anchor, 0, is_anchor=True)
    if not anchor_hid:
        return {"nodes": [], "links": []}

    # 2. 锚点的父母 —— 父亲 paternal，母亲 maternal，父母家庭 side='self'(混合)
    anchor_parents = _get_parents(db, anchor.id)
    for parent in anchor_parents:
        side = "paternal" if parent.gender == "male" else "maternal"
        person_side[parent.id] = side
        # 父母的配偶也标记 person_side
        sp = _get_spouse(db, parent.id)
        if sp and sp.id not in person_side:
            person_side[sp.id] = "paternal" if sp.gender == "male" else "maternal"
        parent_hid = add_household(parent, -1)
        if parent_hid and parent_hid != anchor_hid:
            add_link(parent_hid, anchor_hid)
        # 从 depth=2 开始向上找祖父母（祖父母 depth=-2）
        if parent_hid:
            walk_up(parent, parent_hid, side, depth=2)
        else:
            existing = get_hid_of_person(parent.id)
            if existing:
                walk_up(parent, existing, side, depth=2)

    # 锚点配偶的父母
    if anchor_spouse:
        for parent in _get_parents(db, anchor_spouse.id):
            side = "paternal" if parent.gender == "male" else "maternal"
            person_side[parent.id] = side
            sp = _get_spouse(db, parent.id)
            if sp and sp.id not in person_side:
                person_side[sp.id] = "paternal" if sp.gender == "male" else "maternal"
            parent_hid = add_household(parent, -1)
            if parent_hid and parent_hid != anchor_hid:
                add_link(parent_hid, anchor_hid)
            if parent_hid:
                walk_up(parent, parent_hid, side, depth=2)

    # 3. 锚点的子女
    walk_down(anchor, anchor_hid, "self")
    if anchor_spouse:
        walk_down(anchor_spouse, anchor_hid, "self")

    # 4. 展开兄弟姐妹
    expand_all_siblings()

    # 5. 展开兄弟姐妹的子女
    expand_all_children()

    # 6. 刷新所有家庭的 side（person_side 全部更新后）
    refresh_family_sides()

    return {"nodes": list(nodes.values()), "links": links}
