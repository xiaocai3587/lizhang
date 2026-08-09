"""回礼建议算法

找所有"received"事件中给我随过钱的人，按其最近一次礼金金额
以 3% 年通胀率计算建议回礼金额；无历史记录时默认 500 元。
仅显示"净欠礼金 > 0"的人（即对方给我随的钱 > 我已回给对方的钱）。
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Person, Event, Gift, GiftParticipant


def get_suggestions(db: Session) -> List[dict]:
    """生成回礼建议列表（仅包含净欠礼金 > 0 的人）"""
    # 找"我"
    self_person = db.execute(select(Person).where(Person.is_self == True)).scalars().first()
    if not self_person:
        return []

    # 1. 收集 received 事件中每个 giver 给我的钱 (amount, date)
    received_events = db.execute(select(Event).where(Event.role == "received")).scalars().all()
    giver_data: dict = {}  # person_id -> list of (amount, date)
    for event in received_events:
        gifts = db.execute(select(Gift).where(Gift.event_id == event.id)).scalars().all()
        for g in gifts:
            participants = db.execute(
                select(GiftParticipant).where(
                    GiftParticipant.gift_id == g.id, GiftParticipant.role == "giver"
                )
            ).scalars().all()
            amount = float(g.amount) if g.amount is not None else 0.0
            for p in participants:
                giver_data.setdefault(p.person_id, []).append((amount, event.date))

    # 2. 收集 given 事件中我给每个 receiver 的钱总额（已回礼部分）
    given_events = db.execute(select(Event).where(Event.role == "given")).scalars().all()
    i_gave_total: dict = {}  # person_id -> 已回礼总额
    for event in given_events:
        gifts = db.execute(select(Gift).where(Gift.event_id == event.id)).scalars().all()
        for g in gifts:
            participants = db.execute(
                select(GiftParticipant).where(
                    GiftParticipant.gift_id == g.id, GiftParticipant.role == "receiver"
                )
            ).scalars().all()
            amount = float(g.amount) if g.amount is not None else 0.0
            for p in participants:
                i_gave_total[p.person_id] = i_gave_total.get(p.person_id, 0.0) + amount

    suggestions: List[dict] = []
    now = datetime.now()
    for person_id, records in giver_data.items():
        person = db.get(Person, person_id)
        if not person:
            continue

        # 被标记为 excluded 的人（不来往/已平账）不显示在回礼建议
        if (person.gift_status or "normal") == "excluded":
            continue

        # 对方给我随的总额
        gave_to_me = sum(a for a, _ in records)
        # 我已回给对方的总额
        i_gave = i_gave_total.get(person_id, 0.0)
        # 净欠礼金 = 对方给我 - 我给对方
        net_owed = round(gave_to_me - i_gave, 2)

        # 净欠 <= 0 则不显示（不欠礼金或已超额回礼）
        if net_owed <= 0:
            continue

        # 按日期降序，取最近一次
        records.sort(key=lambda x: x[1] or "", reverse=True)
        last_amount, last_date = records[0]

        # 计算距今年数
        years = 0.0
        if last_date:
            try:
                last_dt = datetime.strptime(last_date, "%Y-%m-%d")
                years = max((now - last_dt).days / 365.25, 0.0)
            except (ValueError, TypeError):
                years = 0.0

        # 建议金额 = 最近一次金额 * (1 + 0.03)^(年数)
        if last_amount and last_amount > 0:
            suggested = last_amount * (1 + 0.03) ** years
        else:
            suggested = 500.0  # 无历史，默认 500

        suggestions.append({
            "person_id": person_id,
            "person_name": person.name,
            "suggested_amount": round(suggested, 2),
            "last_gift_amount": last_amount,
            "last_gift_date": last_date,
            "reason": f"对方累计随礼 {gave_to_me} 元，已回礼 {i_gave} 元，净欠 {net_owed} 元（基于最近一次 {last_date or '未知日期'} 的 {last_amount} 元按 3% 年通胀调整）",
        })

    # 按建议金额降序
    suggestions.sort(key=lambda x: x["suggested_amount"], reverse=True)
    return suggestions
