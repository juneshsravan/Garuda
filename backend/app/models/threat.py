import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Threat(Base, TimestampMixin):
    __tablename__ = "threats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    threat_type: Mapped[str] = mapped_column(String(50), nullable=False)  # domain | url | qr_payload | phone | upi
    value_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    scan_links = relationship("ScanThreat", back_populates="threat", cascade="all, delete-orphan")
    intelligence = relationship("ThreatIntelligence", back_populates="threat")


class ScanThreat(Base, TimestampMixin):
    __tablename__ = "scan_threats"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        primary_key=True,
    )
    threat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threats.id", ondelete="CASCADE"),
        primary_key=True,
    )

    scan = relationship("Scan", back_populates="threat_links")
    threat = relationship("Threat", back_populates="scan_links")


class ThreatIntelligence(Base, TimestampMixin):
    __tablename__ = "threat_intelligence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    threat_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threats.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    indicator_type: Mapped[str] = mapped_column(String(50), nullable=False)  # domain | url | ip | hash | phone | upi
    indicator_value: Mapped[str] = mapped_column(Text, nullable=False)
    indicator_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    verdict: Mapped[str] = mapped_column(String(50), nullable=False)  # phishing | malware | gambling | adult | ...
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("source", "indicator_hash", name="uq_threat_intel_source_indicator_hash"),
        Index("ix_threat_intel_type_hash", "indicator_type", "indicator_hash"),
    )

    threat = relationship("Threat", back_populates="intelligence")
