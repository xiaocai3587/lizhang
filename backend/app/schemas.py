"""Pydantic schemas — API 数据契约"""
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ── Person ──────────────────────────────────────────────────────────
class PersonBase(BaseModel):
    name: str
    nickname: str = ""
    group: str
    gender: str = ""
    birth_year: str = ""
    is_self: bool = False
    title: str = ""  # 称谓(手动覆盖)
    gift_status: str = "normal"  # normal/excluded
    notes: str = ""


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    group: Optional[str] = None
    gender: Optional[str] = None
    birth_year: Optional[str] = None
    is_self: Optional[bool] = None
    title: Optional[str] = None
    gift_status: Optional[str] = None
    notes: Optional[str] = None


class PersonOut(PersonBase):
    id: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Relation ────────────────────────────────────────────────────────
class RelationBase(BaseModel):
    from_id: str
    to_id: str
    type: str
    notes: str = ""


class RelationCreate(RelationBase):
    pass


class RelationOut(BaseModel):
    id: str
    from_id: str
    to_id: str
    type: str
    notes: str = ""
    from_name: Optional[str] = None
    to_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ── Event ───────────────────────────────────────────────────────────
class EventBase(BaseModel):
    title: str
    event_type: str = ""
    date: str
    role: str
    notes: str = ""


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    event_type: Optional[str] = None
    date: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None


class EventOut(EventBase):
    id: str
    gift_count: int = 0
    gift_total: float = 0.0
    model_config = ConfigDict(from_attributes=True)


# ── Gift ────────────────────────────────────────────────────────────
class GiftParticipantCreate(BaseModel):
    person_id: str
    role: str  # giver/receiver


class GiftBase(BaseModel):
    event_id: str
    amount: Decimal
    is_shared: bool = False
    notes: str = ""
    participants: List[GiftParticipantCreate] = []


class GiftCreate(GiftBase):
    pass


class GiftOut(BaseModel):
    id: str
    event_id: str
    amount: float
    is_shared: bool
    notes: str
    participants: List[dict] = []
    model_config = ConfigDict(from_attributes=True)


# ── Graph ───────────────────────────────────────────────────────────
class GraphNode(BaseModel):
    id: str
    name: str
    gender: str = ""
    group: str = ""
    is_self: bool = False
    birth_year: str = ""
    depth: int = 0
    total_amount: float = 0


class GraphLink(BaseModel):
    source: str
    target: str
    type: str
    amount: Optional[float] = None


class GraphData(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]


# ── 家庭单元族谱 ───────────────────────────────────────────────────
class HouseholdMember(BaseModel):
    id: str
    name: str
    nickname: str = ""
    gender: str = ""
    group: str = ""
    is_self: bool = False
    birth_year: str = ""
    title: str = ""  # 最终显示的称谓（优先手动title，否则自动推算）


class HouseholdNode(BaseModel):
    id: str  # household id
    members: List[HouseholdMember]  # 1或2人
    depth: int = 0
    is_anchor: bool = False
    side: str = "self"  # paternal(父系左) / maternal(母系右) / self(中间)


class HouseholdGraphData(BaseModel):
    nodes: List[HouseholdNode]
    links: List[GraphLink]


# ── Stats ───────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    persons_count: int
    events_count: int
    gifts_count: int
    total_received: float
    total_given: float
    net: float
    recent_events: List[dict] = []
    top_persons: List[dict] = []
    monthly_trend: List[dict] = []


class PersonStats(BaseModel):
    total_gave: float
    total_received: float
    net: float
    gift_count: int


# ── Suggestion ─────────────────────────────────────────────────────
class GiftSuggestion(BaseModel):
    person_id: str
    person_name: str
    suggested_amount: float
    last_gift_amount: Optional[float] = None
    last_gift_date: Optional[str] = None
    reason: str = ""


# ── Data import/export ─────────────────────────────────────────────
class ImportResult(BaseModel):
    persons: int = 0
    relations: int = 0
    events: int = 0
    gifts: int = 0
    errors: List[str] = []
