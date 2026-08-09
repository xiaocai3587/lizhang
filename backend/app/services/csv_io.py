"""CSV 导入导出

导出：persons / relations / events / gifts 四张表为 CSV，打包成 zip。
导入：接收上传的 CSV 文件（按文件名识别），写入数据库。
"""
from __future__ import annotations

import io
import json
import zipfile
from typing import Dict

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Person, Relation, Event, Gift, GiftParticipant
from ..schemas import ImportResult


# ── 导出 ────────────────────────────────────────────────────────────
def export_to_csv(db: Session) -> bytes:
    """导出 4 个 CSV 为 zip 字节流"""
    persons = db.execute(select(Person)).scalars().all()
    relations = db.execute(select(Relation)).scalars().all()
    events = db.execute(select(Event)).scalars().all()
    gifts = db.execute(select(Gift)).scalars().all()

    # persons
    persons_df = pd.DataFrame([{
        "id": p.id,
        "name": p.name,
        "group": p.group,
        "gender": p.gender,
        "birth_year": p.birth_year,
        "is_self": p.is_self,
        "notes": p.notes,
        "created_at": p.created_at.isoformat() if p.created_at else "",
    } for p in persons])

    # relations
    relations_df = pd.DataFrame([{
        "id": r.id,
        "from_id": r.from_id,
        "to_id": r.to_id,
        "type": r.type,
        "notes": r.notes,
    } for r in relations])

    # events
    events_df = pd.DataFrame([{
        "id": e.id,
        "title": e.title,
        "event_type": e.event_type,
        "date": e.date,
        "role": e.role,
        "notes": e.notes,
        "created_at": e.created_at.isoformat() if e.created_at else "",
    } for e in events])

    # gifts（participants 以 JSON 字符串内嵌）
    gift_rows = []
    for g in gifts:
        participants = db.execute(
            select(GiftParticipant).where(GiftParticipant.gift_id == g.id)
        ).scalars().all()
        parts_list = [{"person_id": p.person_id, "role": p.role} for p in participants]
        gift_rows.append({
            "id": g.id,
            "event_id": g.event_id,
            "amount": float(g.amount) if g.amount is not None else 0.0,
            "is_shared": g.is_shared,
            "notes": g.notes,
            "participants": json.dumps(parts_list, ensure_ascii=False),
            "created_at": g.created_at.isoformat() if g.created_at else "",
        })
    gifts_df = pd.DataFrame(gift_rows)

    # 打包 zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, df in [
            ("persons.csv", persons_df),
            ("relations.csv", relations_df),
            ("events.csv", events_df),
            ("gifts.csv", gifts_df),
        ]:
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
            zf.writestr(name, csv_buf.getvalue())
    return buf.getvalue()


# ── 导入 ────────────────────────────────────────────────────────────
def _safe_str(val, default: str = "") -> str:
    """安全转换为字符串，处理 NaN/None"""
    if val is None or pd.isna(val):
        return default
    return str(val)


def _safe_bool(val, default: bool = False) -> bool:
    if val is None or pd.isna(val):
        return default
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ("true", "1", "yes", "t")


def import_from_csv(db: Session, files: Dict[str, io.BytesIO]) -> ImportResult:
    """从 CSV 文件导入数据

    Args:
        db: 数据库会话
        files: 文件名 -> 文件内容流 的映射

    Returns:
        ImportResult
    """
    result = ImportResult()

    try:
        # ── persons ──
        if "persons.csv" in files:
            df = pd.read_csv(files["persons.csv"])
            for _, row in df.iterrows():
                try:
                    p = Person(
                        id=_safe_str(row["id"]),
                        name=_safe_str(row["name"]),
                        group=_safe_str(row["group"]),
                        gender=_safe_str(row.get("gender", "")),
                        birth_year=_safe_str(row.get("birth_year", "")),
                        is_self=_safe_bool(row.get("is_self", False)),
                        notes=_safe_str(row.get("notes", "")),
                    )
                    db.merge(p)
                    result.persons += 1
                except Exception as e:
                    result.errors.append(f"persons 行错误: {e}")

        # ── relations ──
        if "relations.csv" in files:
            df = pd.read_csv(files["relations.csv"])
            for _, row in df.iterrows():
                try:
                    r = Relation(
                        id=_safe_str(row["id"]),
                        from_id=_safe_str(row["from_id"]),
                        to_id=_safe_str(row["to_id"]),
                        type=_safe_str(row["type"]),
                        notes=_safe_str(row.get("notes", "")),
                    )
                    db.merge(r)
                    result.relations += 1
                except Exception as e:
                    result.errors.append(f"relations 行错误: {e}")

        # ── events ──
        if "events.csv" in files:
            df = pd.read_csv(files["events.csv"])
            for _, row in df.iterrows():
                try:
                    e = Event(
                        id=_safe_str(row["id"]),
                        title=_safe_str(row["title"]),
                        event_type=_safe_str(row.get("event_type", "")),
                        date=_safe_str(row["date"]),
                        role=_safe_str(row["role"]),
                        notes=_safe_str(row.get("notes", "")),
                    )
                    db.merge(e)
                    result.events += 1
                except Exception as e:
                    result.errors.append(f"events 行错误: {e}")

        # ── gifts（含 participants）──
        if "gifts.csv" in files:
            df = pd.read_csv(files["gifts.csv"])
            for _, row in df.iterrows():
                try:
                    g_id = _safe_str(row["id"])
                    amount_val = row["amount"]
                    amount = float(amount_val) if not pd.isna(amount_val) else 0.0
                    g = Gift(
                        id=g_id,
                        event_id=_safe_str(row["event_id"]),
                        amount=amount,
                        is_shared=_safe_bool(row.get("is_shared", False)),
                        notes=_safe_str(row.get("notes", "")),
                    )
                    db.merge(g)
                    db.flush()

                    # 删除该 gift 的旧 participants，再重新创建
                    old_parts = db.execute(
                        select(GiftParticipant).where(GiftParticipant.gift_id == g_id)
                    ).scalars().all()
                    for op in old_parts:
                        db.delete(op)

                    parts_str = row.get("participants", "")
                    if parts_str is not None and not pd.isna(parts_str) and str(parts_str).strip():
                        try:
                            parts_list = json.loads(str(parts_str))
                        except (json.JSONDecodeError, ValueError):
                            parts_list = []
                        for part in parts_list:
                            gp = GiftParticipant(
                                gift_id=g_id,
                                person_id=_safe_str(part.get("person_id")),
                                role=_safe_str(part.get("role")),
                            )
                            db.add(gp)
                    result.gifts += 1
                except Exception as e:
                    result.errors.append(f"gifts 行错误: {e}")

        db.commit()
    except Exception as e:
        db.rollback()
        result.errors.append(f"全局错误: {e}")

    return result
