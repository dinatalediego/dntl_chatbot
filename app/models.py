from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("event_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SourceCursor(Base):
    __tablename__ = "source_cursors"
    source_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    watermark: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (UniqueConstraint("source", "source_lead_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(80), default="medallio")
    source_lead_id: Mapped[str] = mapped_column(String(200), nullable=False)
    person_name: Mapped[str | None] = mapped_column(String(240))
    phone_e164: Mapped[str | None] = mapped_column(String(40))
    project: Mapped[str | None] = mapped_column(String(240))
    opted_in: Mapped[bool] = mapped_column(Boolean, default=False)
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False)
    eligible_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (UniqueConstraint("lead_id", "policy_version"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(80), default="immediate-contact-v1")
    experiment_group: Mapped[str] = mapped_column(String(20), nullable=False)
    decision: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Action(Base):
    __tablename__ = "actions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(40))
    provider_message_id: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")
    error_message: Mapped[str | None] = mapped_column(Text)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Outcome(Base):
    __tablename__ = "outcomes"
    __table_args__ = (UniqueConstraint("lead_id", "kind"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
