import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_SCAM_TYPES = {"sms", "whatsapp", "call", "link", "qr_upi", "email", "other"}
VALID_STATUSES = {"submitted", "reviewed"}


class ReportCreateRequest(BaseModel):
    scan_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional scan ID linked to this report",
    )
    scam_type: str = Field(
        ...,
        description="Scam vector: sms, whatsapp, call, link, qr_upi, email, other",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Scam message or incident content (1 to 5000 characters).",
    )
    scammer_phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Scammer phone number if known",
    )
    scammer_upi: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Scammer UPI ID/VPA if known",
    )
    scammer_url: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Scammer website / phishing link if known",
    )
    amount_lost: Optional[float] = Field(
        default=None,
        ge=0,
        le=100_000_000,
        description="Amount lost in INR (0 to 10 crore)",
    )
    incident_date: Optional[datetime] = Field(
        default=None,
        description="Date/time when incident occurred",
    )

    @field_validator("scam_type")
    @classmethod
    def validate_scam_type(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in VALID_SCAM_TYPES:
            raise ValueError(
                f"Invalid scam_type '{v}'. Must be one of: {', '.join(sorted(VALID_SCAM_TYPES))}"
            )
        return cleaned

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content cannot be empty or whitespace only.")
        return v.strip()

    @field_validator("scammer_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return None

    @field_validator("scammer_upi")
    @classmethod
    def validate_upi(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return None

    @field_validator("scammer_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference_code: str
    user_id: uuid.UUID
    scan_id: Optional[uuid.UUID] = None
    scam_type: str
    content: str
    scammer_phone: Optional[str] = None
    scammer_upi: Optional[str] = None
    scammer_url: Optional[str] = None
    amount_lost: Optional[float] = None
    incident_date: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
