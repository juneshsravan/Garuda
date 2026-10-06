import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Scan(Base, TimestampMixin):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scan_type: Mapped[str] = mapped_column(String(50), nullable=False)  # message | url | qr | image
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="done")  # done | failed
    input_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    persisted_content: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_scans_user_id_created_at_desc", "user_id", text("created_at DESC")),
    )

    # Relationships
    user = relationship("User", back_populates="scans")
    message = relationship("Message", back_populates="scan", uselist=False, cascade="all, delete-orphan")
    images = relationship("Image", back_populates="scan", cascade="all, delete-orphan")
    qr_codes = relationship("QRCode", back_populates="scan", cascade="all, delete-orphan")
    urls = relationship("URL", back_populates="scan", cascade="all, delete-orphan")
    analysis_result = relationship("AnalysisResult", back_populates="scan", uselist=False, cascade="all, delete-orphan")
    threat_links = relationship("ScanThreat", back_populates="scan", cascade="all, delete-orphan")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    detected_language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    scan = relationship("Scan", back_populates="message")


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    scan = relationship("Scan", back_populates="images")
    qr_codes = relationship("QRCode", back_populates="image")


class QRCode(Base, TimestampMixin):
    __tablename__ = "qr_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    payload_type: Mapped[str] = mapped_column(String(50), nullable=False)  # url | upi | text | wifi | other
    upi_payee: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    upi_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    upi_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    scan = relationship("Scan", back_populates="qr_codes")
    image = relationship("Image", back_populates="qr_codes")


class URL(Base, TimestampMixin):
    __tablename__ = "urls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False)
    registered_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # direct | message | qr | ocr

    scan = relationship("Scan", back_populates="urls")


class AnalysisResult(Base, TimestampMixin):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    legitimacy_signals: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    recommendations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    verify_steps: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    intel_status: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False, default="2.0.0")

    scan = relationship("Scan", back_populates="analysis_result")
    threat_indicators = relationship("ThreatIndicator", back_populates="analysis", cascade="all, delete-orphan")


class ThreatIndicator(Base, TimestampMixin):
    __tablename__ = "threat_indicators"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    analysis = relationship("AnalysisResult", back_populates="threat_indicators")
