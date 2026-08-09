"""SQLAlchemy ORM 模型"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import String, Boolean, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(50), index=True)
    nickname: Mapped[str] = mapped_column(String(50), default="")  # 小名
    group: Mapped[str] = mapped_column(String(20), index=True)  # my_family/wife_family/friends
    gender: Mapped[str] = mapped_column(String(10), default="")
    birth_year: Mapped[str] = mapped_column(String(10), default="")
    is_self: Mapped[bool] = mapped_column(Boolean, default=False)
    title: Mapped[str] = mapped_column(String(20), default="")  # 称谓(手动覆盖；为空则自动推算)
    gift_status: Mapped[str] = mapped_column(String(20), default="normal")  # normal/excluded
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    relations_from: Mapped[List["Relation"]] = relationship(
        foreign_keys="Relation.from_id", back_populates="from_person", cascade="all, delete-orphan"
    )
    relations_to: Mapped[List["Relation"]] = relationship(
        foreign_keys="Relation.to_id", back_populates="to_person", cascade="all, delete-orphan"
    )


class Relation(Base):
    __tablename__ = "relations"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=gen_id)
    from_id: Mapped[str] = mapped_column(String(12), ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    to_id: Mapped[str] = mapped_column(String(12), ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(20), index=True)  # parent_child/spouse/sibling
    notes: Mapped[str] = mapped_column(String(100), default="")

    from_person: Mapped["Person"] = relationship(foreign_keys=[from_id], back_populates="relations_from")
    to_person: Mapped["Person"] = relationship(foreign_keys=[to_id], back_populates="relations_to")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=gen_id)
    title: Mapped[str] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(50), default="")
    date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    role: Mapped[str] = mapped_column(String(10))  # received/given
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    gifts: Mapped[List["Gift"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Gift(Base):
    __tablename__ = "gifts"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=gen_id)
    event_id: Mapped[str] = mapped_column(String(12), ForeignKey("events.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event: Mapped["Event"] = relationship(back_populates="gifts")
    participants: Mapped[List["GiftParticipant"]] = relationship(
        back_populates="gift", cascade="all, delete-orphan"
    )


class GiftParticipant(Base):
    __tablename__ = "gift_participants"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=gen_id)
    gift_id: Mapped[str] = mapped_column(String(12), ForeignKey("gifts.id", ondelete="CASCADE"), index=True)
    person_id: Mapped[str] = mapped_column(String(12), ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(10))  # giver/receiver

    gift: Mapped["Gift"] = relationship(back_populates="participants")
    person: Mapped["Person"] = relationship()
