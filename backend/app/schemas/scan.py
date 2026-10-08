import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageAnalyzeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Message content to analyze (1 to 5000 characters).",
    )
    save: bool = Field(
        default=True,
        description="Whether to persist the scan and its results in the database.",
    )

    @field_validator("text")
    @classmethod
    def validate_non_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message text cannot be empty or whitespace only.")
        return v


class RiskInfo(BaseModel):
    score: int
    level: str
    label: str


class CategoryInfo(BaseModel):
    code: str
    label: str


class IndicatorInfo(BaseModel):
    code: str
    label: str
    severity: str
    weight: float
    evidence: Optional[str] = None


class LegitimacySignalInfo(BaseModel):
    code: str
    label: str
    weight: float
    evidence: Optional[str] = None


class IntelStatusInfo(BaseModel):
    source: str
    status: str
    details: Optional[Dict[str, Any]] = None


class ExtractedEntities(BaseModel):
    urls: List[Dict[str, Any]] = Field(default_factory=list)
    qr: Optional[Dict[str, Any]] = None
    upi: Optional[Dict[str, Any]] = None
    phone: Optional[List[str]] = Field(default_factory=list)
    language: Optional[str] = None


class MessageDetail(BaseModel):
    content: str
    detected_language: Optional[str] = None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: Optional[str] = None
    scan_type: str = "message"
    risk: RiskInfo
    confidence: float
    verification_status: str
    category: CategoryInfo
    summary: str
    indicators: List[IndicatorInfo] = Field(default_factory=list)
    legitimacy_signals: List[LegitimacySignalInfo] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    verify_steps: List[str] = Field(default_factory=list)
    extracted: ExtractedEntities
    intel: List[IntelStatusInfo] = Field(default_factory=list)
    engine_version: str = "2.0.0"
    created_at: Optional[datetime] = None
    message: Optional[MessageDetail] = None


class ScanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scan_type: str
    status: str
    created_at: datetime
    risk: RiskInfo
    category: CategoryInfo
    confidence: float
    verification_status: str
    summary: Optional[str] = None
    content_preview: Optional[str] = None


class ScanListResponse(BaseModel):
    items: List[ScanListItem]
    next_cursor: Optional[str] = None
    has_more: bool
