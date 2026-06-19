"""Relational records. The graph lives in Neo4j; Postgres holds the operational
system-of-record: tenants, users, generated skills, executions, approvals, and
the corrections that drive the learning loop. Multi-tenancy is enforced by a
``company_id`` on every row (RBAC checks build on top of this)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    email: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String, default="member")  # owner|admin|member
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class SkillRecord(Base):
    __tablename__ = "skills"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    goal: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, default=1)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    freshness: Mapped[float] = mapped_column(Float, default=0.0)
    definition: Mapped[dict] = mapped_column(JSON)  # full Skill JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ExecutionRecord(Base):
    __tablename__ = "executions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    result: Mapped[dict] = mapped_column(JSON)  # full ExecutionResult JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ApprovalRecord(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"), index=True)
    action: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|approved|overridden
    reason: Mapped[str] = mapped_column(Text, default="")
    decided_by: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class CorrectionRecord(Base):
    __tablename__ = "corrections"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"), index=True)
    original_action: Mapped[str] = mapped_column(String)
    corrected_action: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
