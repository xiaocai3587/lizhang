"""称谓推算引擎

从"我"出发 BFS 遍历关系图，根据关系路径+性别+排行推算称谓。
覆盖常见家族称谓：父母/爷爷奶奶/姑姑舅舅/姨/兄弟姐妹/堂表/侄甥等。
推不准的返回空字符串（前端显示"?"或留空）。
"""
from __future__ import annotations

from typing import Optional
from collections import deque

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from ..models import Person, Relation


# ── 基础关系查询 ──────────────────────────────────────────────────
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
    """亲兄弟姐妹（同父母）"""
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


# ── 排行计算 ──────────────────────────────────────────────────────
def _rank_ordinal(idx: int, total: int) -> str:
    """根据排行返回前缀
    idx=0 第1个 → '大'
    idx=1 第2个 → '二'
    最后一个 → '小'
    独生(total=1)也返回 '大'（符合 大姑/大舅 的习惯）
    """
    if total <= 1:
        return "大"  # 独生也叫"大X"
    if idx == total - 1:
        return "小"  # 最后一个叫"小"
    cn_nums = ["大", "二", "三", "四", "五", "六", "七", "八", "九"]
    if idx < len(cn_nums):
        return cn_nums[idx]
    return str(idx + 1)


def _rank_of(db: Session, person: Person, siblings: list[Person]) -> tuple[int, int]:
    """此人在兄弟姐妹中的排行索引(0-based)。
    优先按出生年份排序；年份为空时按 parent_child 关系的 rowid(插入)顺序。
    """
    all_sibs = [person] + [s for s in siblings if s.id != person.id]
    # 去重
    seen = set()
    unique = []
    for s in all_sibs:
        if s.id not in seen:
            seen.add(s.id)
            unique.append(s)

    # 若所有人都没有 birth_year，用 rowid 顺序
    has_year = any(_safe_year(s.birth_year) for s in unique)
    if not has_year:
        # 按其在 relations 表中 parent_child 关系的 rowid 排序
        # 找共同父母
        parents = _get_parents(db, person.id)
        if parents:
            parent_id = parents[0].id
            # 原生 SQL 按 rowid 取顺序
            from sqlalchemy import text
            rows = db.execute(
                text("SELECT to_id FROM relations WHERE type='parent_child' AND from_id=:pid ORDER BY rowid"),
                {"pid": parent_id},
            ).fetchall()
            order_map = {r[0]: i for i, r in enumerate(rows)}
            # 给每个人分配顺序，没找到的放最后
            def key_fn(p: Person):
                return order_map.get(p.id, 9999)
            unique.sort(key=key_fn)
            for i, p in enumerate(unique):
                if p.id == person.id:
                    return i, len(unique)
        return 0, len(unique)

    # 有 birth_year 的按年份排
    def sort_key(p: Person):
        y = _safe_year(p.birth_year)
        return (0, y) if y else (1, 0)
    unique.sort(key=sort_key)
    for i, p in enumerate(unique):
        if p.id == person.id:
            return i, len(unique)
    return 0, len(unique)


# ── 称谓推算主函数 ────────────────────────────────────────────────
def compute_titles(db: Session, self_id: str) -> dict[str, str]:
    """从 self 出发，推算每个人的称谓。
    返回 {person_id: title}。手动设置 person.title 的优先返回。
    """
    self_person = db.get(Person, self_id)
    if not self_person:
        return {}

    # BFS：每个人记录 (path, generation, side, via_person_id)
    # path 步骤: ('up', parent_person), ('down', child_person),
    #           ('sibling', sib_person), ('spouse', spouse_person)
    # generation: 相对辈分 (我=0, 父母=+1, 子女=-1)
    # side: 'self'/'paternal'/'maternal' (首次上行决定)
    visited: dict[str, dict] = {}  # person_id -> {path, gen, side}
    queue = deque()

    visited[self_id] = {"path": [], "gen": 0, "side": "self"}
    queue.append(self_id)

    while queue:
        cur_id = queue.popleft()
        cur_info = visited[cur_id]
        cur = db.get(Person, cur_id)
        if not cur:
            continue

        # 1. 向上：父母
        for parent in _get_parents(db, cur_id):
            if parent.id in visited:
                continue
            # 决定 side
            if cur_info["gen"] == 0:
                # 我的父母：父→paternal，母→maternal
                side = "paternal" if (parent.gender or "").lower() in ("male", "男") else "maternal"
            else:
                side = cur_info["side"]  # 继承上一辈的 side
            visited[parent.id] = {
                "path": cur_info["path"] + [("up", parent)],
                "gen": cur_info["gen"] + 1,
                "side": side,
            }
            queue.append(parent.id)

        # 2. 向下：子女
        for child in _get_children(db, cur_id):
            if child.id in visited:
                continue
            visited[child.id] = {
                "path": cur_info["path"] + [("down", child)],
                "gen": cur_info["gen"] - 1,
                "side": cur_info["side"],
            }
            queue.append(child.id)

        # 3. 横向：兄弟姐妹（只在 gen=0 时展开我的兄弟姐妹；其他辈分也展开以便覆盖堂表）
        for sib in _get_siblings(db, cur_id):
            if sib.id in visited:
                continue
            visited[sib.id] = {
                "path": cur_info["path"] + [("sibling", sib)],
                "gen": cur_info["gen"],  # 同辈
                "side": cur_info["side"],
            }
            queue.append(sib.id)

        # 4. 配偶
        sp = _get_spouse(db, cur_id)
        if sp and sp.id not in visited:
            visited[sp.id] = {
                "path": cur_info["path"] + [("spouse", sp)],
                "gen": cur_info["gen"],  # 配偶同辈
                "side": cur_info["side"],
            }
            queue.append(sp.id)

    # ── 推算称谓 ──
    titles: dict[str, str] = {}
    for pid, info in visited.items():
        p = db.get(Person, pid)
        if not p:
            continue
        # 手动设置的优先
        if p.title and p.title.strip():
            titles[pid] = p.title.strip()
            continue
        # 我自己
        if pid == self_id:
            titles[pid] = "我"
            continue
        titles[pid] = _infer_title(db, p, info, self_person)

    return titles


def _infer_title(db: Session, person: Person, info: dict, self_person: Person) -> str:
    """根据 BFS 信息推算单个人的称谓"""
    path = info["path"]
    gen = info["gen"]
    side = info["side"]
    gender = (person.gender or "").lower()
    is_male = gender in ("male", "男")
    is_female = gender in ("female", "女")

    # 最后一步是 spouse → 配偶称谓
    if path and path[-1][0] == "spouse":
        # 当前人通过 spouse 关系到达；其配偶 = 路径上前一步对应的人
        # path 形如 [..., (step, spouse_obj), (spouse, self_person_obj)]
        # 配偶是 path[-2][1]（即上一步到达的人）；若只有一步 spouse，配偶是 self_person
        if len(path) >= 2:
            spouse_person = path[-2][1]
        else:
            spouse_person = self_person
        # 配偶的血亲路径 = 去掉最后一步 spouse
        spouse_info = {
            "path": path[:-1],
            "gen": gen,
            "side": side,
        }
        spouse_title = _infer_title(db, spouse_person, spouse_info, self_person)
        return _spouse_title(spouse_title, is_male, is_female)

    # 直系血亲称谓
    return _blood_title(db, person, info, self_person)


def _blood_title(db: Session, person: Person, info: dict, self_person: Person) -> str:
    """推算直系血亲称谓（不含配偶）"""
    path = info["path"]
    gen = info["gen"]
    side = info["side"]
    gender = (person.gender or "").lower()
    is_male = gender in ("male", "男")
    is_female = gender in ("female", "女")
    pid = person.id

    # ── 辈分 +1：父母辈 ──
    if gen == 1:
        # 我直系父母
        if len(path) == 1 and path[0][0] == "up":
            return "父亲" if is_male else "母亲"
        # 父亲的兄弟（大爷/二大爷）
        if side == "paternal":
            if is_male:
                parents_of_person = _get_parents(db, pid)
                if parents_of_person:
                    idx, total = _gender_rank(db, person, parents_of_person[0])
                    prefix = _rank_ordinal(idx, total)
                    # 大爷/二大爷/三大爷/小大爷
                    if not prefix:
                        return "伯"
                    if prefix == "大":
                        return "大爷"
                    return f"{prefix}大爷"
            else:
                # 父亲的姐妹 → 姑
                parents_of_person = _get_parents(db, pid)
                if parents_of_person:
                    idx, total = _gender_rank(db, person, parents_of_person[0])
                    prefix = _rank_ordinal(idx, total)
                    return f"{prefix}姑" if prefix else "姑姑"
        # 母亲的兄弟（舅）
        elif side == "maternal":
            if is_male:
                parents_of_person = _get_parents(db, pid)
                if parents_of_person:
                    idx, total = _gender_rank(db, person, parents_of_person[0])
                    prefix = _rank_ordinal(idx, total)
                    return f"{prefix}舅" if prefix else "舅"
            else:
                # 母亲的姐妹 → 姨
                parents_of_person = _get_parents(db, pid)
                if parents_of_person:
                    idx, total = _gender_rank(db, person, parents_of_person[0])
                    prefix = _rank_ordinal(idx, total)
                    return f"{prefix}姨" if prefix else "姨"
        return ""

    # ── 辈分 +2：祖父母辈 ──
    if gen == 2:
        if side == "paternal":
            return "爷爷" if is_male else "奶奶"
        elif side == "maternal":
            return "姥爷" if is_male else "姥姥"
        return ""

    # ── 辈分 0：同辈（兄弟姐妹/堂表） ──
    if gen == 0:
        # 我的亲兄弟姐妹
        if len(path) == 1 and path[0][0] == "sibling":
            sibs = _get_siblings(db, self_person.id)
            idx, total = _rank_of(db, person, sibs)
            if is_male:
                # 比我大→哥，比我小→弟
                self_idx, _ = _rank_of(db, self_person, sibs)
                return "哥" if idx < self_idx else "弟"
            else:
                self_idx, _ = _rank_of(db, self_person, sibs)
                return "姐" if idx < self_idx else "妹"
        # 父系同辈（堂兄弟姐妹）：父亲的兄弟的孩子
        if side == "paternal":
            if is_male:
                return _cousin_brother_title(db, person, self_person)
            else:
                return _cousin_sister_title(db, person, self_person)
        # 母系同辈（表兄弟姐妹）：母亲或父系姐妹的孩子
        if side == "maternal":
            if is_male:
                return _cousin_brother_title(db, person, self_person, maternal=True)
            else:
                return _cousin_sister_title(db, person, self_person, maternal=True)
        return ""

    # ── 辈分 -1：子侄辈 ──
    if gen == -1:
        # 我自己的子女
        if len(path) == 1 and path[0][0] == "down":
            return "儿子" if is_male else "女儿"
        # 其他子侄辈：根据"这个子女的父母(=path倒数第二个人)"的性别判定
        # 规则：兄弟/堂兄弟/表兄弟(男性)的子女 → 侄子/侄女；
        #       姐妹/堂姐妹/表姐妹(女性)的子女 → 外甥/外甥女
        if len(path) >= 2:
            parent = path[-2][1]  # 该子女的父母
            parent_gender = (parent.gender or "").lower()
            parent_is_male = parent_gender in ("male", "男")
            if parent_is_male:
                return "侄子" if is_male else "侄女"
            return "外甥" if is_male else "外甥女"
        return ""

    # ── 辈分 -2：孙辈 ──
    if gen == -2:
        if is_male:
            return "孙子"
        else:
            return "孙女"

    # 其他更远的不推算
    return ""


def _get_siblings_of_person_via_parent(
    db: Session, person_id: str, parent: Person, gender_filter: Optional[str] = None
) -> list[Person]:
    """通过指定父母获取此人的兄弟姐妹（用于排行）。
    gender_filter 给定时只返回该性别（'male'/'female'）的兄弟姐妹。
    """
    siblings = []
    seen = {person_id}
    for child_rel in db.execute(
        select(Relation).where(
            Relation.type == "parent_child",
            Relation.from_id == parent.id,
        )
    ).scalars().all():
        if child_rel.to_id not in seen:
            sib = db.get(Person, child_rel.to_id)
            if sib:
                if gender_filter and (sib.gender or "").lower() not in (gender_filter,):
                    continue
                siblings.append(sib)
                seen.add(sib.id)
    return siblings


def _gender_rank(db: Session, person: Person, parent: Person) -> tuple[int, int]:
    """此人在同性别兄弟姐妹中的排行(0-based)，用于父母辈称谓推算。"""
    g = (person.gender or "").lower()
    gf = "male" if g in ("male", "男") else ("female" if g in ("female", "女") else None)
    sibs = _get_siblings_of_person_via_parent(db, person.id, parent, gender_filter=gf)
    return _rank_of(db, person, sibs)


def _cousin_brother_title(db: Session, person: Person, self_person: Person, maternal: bool = False) -> str:
    """堂/表哥/弟"""
    # 找此人和我的共同长辈，判断辈分大小
    # 简化：按出生年份判断比我大还是小
    self_year = _safe_year(self_person.birth_year)
    person_year = _safe_year(person.birth_year)
    older = person_year < self_year if (self_year and person_year) else False

    if maternal:
        # 母系：表
        return "表哥" if older else "表弟"
    else:
        # 父系：堂
        return "堂哥" if older else "堂弟"


def _cousin_sister_title(db: Session, person: Person, self_person: Person, maternal: bool = False) -> str:
    """堂/表姐/妹"""
    self_year = _safe_year(self_person.birth_year)
    person_year = _safe_year(person.birth_year)
    older = person_year < self_year if (self_year and person_year) else False

    if maternal:
        return "表姐" if older else "表妹"
    else:
        return "堂姐" if older else "堂妹"


def _safe_year(birth_year: str) -> Optional[int]:
    if not birth_year:
        return None
    try:
        return int(birth_year)
    except (ValueError, TypeError):
        return None


# ── 配偶称谓映射 ──────────────────────────────────────────────────
def _spouse_title(spouse_blood_title: str, is_male: bool, is_female: bool) -> str:
    """根据配偶的血亲称谓，推算其配偶（即此人）的称谓"""
    # 直接配偶
    if not spouse_blood_title or spouse_blood_title == "我":
        # 我的直接配偶
        return "老婆" if is_female else "老公"

    mapping = {
        # 父母辈
        "父亲": "母亲",
        "母亲": "父亲",
        # 父系长辈
        "大爷": "大娘",
        "二大爷": "二大娘",
        "三大爷": "三大娘",
        "四大爷": "四大娘",
        "小大爷": "小大娘",
        "伯": "伯母",
        "大姑": "大姑父",
        "二姑": "二姑父",
        "三姑": "三姑父",
        "小姑": "小姑父",
        "姑姑": "姑父",
        # 母系长辈
        "大舅": "大舅妈",
        "二舅": "二舅妈",
        "三舅": "三舅妈",
        "小舅": "小舅妈",
        "舅": "舅妈",
        "大姨": "大姨夫",
        "二姨": "二姨夫",
        "三姨": "三姨夫",
        "四姨": "四姨夫",
        "小姨": "小姨夫",
        "姨": "姨夫",
        # 同辈
        "哥": "嫂子",
        "弟": "弟妹",
        "姐": "姐夫",
        "妹": "妹夫",
        "堂哥": "堂嫂",
        "堂弟": "堂弟妹",
        "堂姐": "堂姐夫",
        "堂妹": "堂妹夫",
        "表哥": "表嫂",
        "表弟": "表弟妹",
        "表姐": "表姐夫",
        "表妹": "表妹夫",
        # 子侄辈的配偶
        "儿子": "儿媳",
        "侄子": "侄媳",
        "外甥": "外甥媳",
    }
    return mapping.get(spouse_blood_title, "")
