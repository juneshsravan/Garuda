import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DailyScanCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    count: int = Field(..., ge=0, description="Number of scans performed on this day")


class CategoryCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(..., description="Category code identifier")
    label: str = Field(..., description="Human-readable category label")
    count: int = Field(..., ge=0, description="Total count of scans in this category")


class DashboardRecentScan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Scan UUID identifier")
    scan_type: str = Field(..., description="Scan modality (message | url | qr | image)")
    preview: Optional[str] = Field(None, description="Short snippet of scanned input")
    risk_score: int = Field(..., ge=0, le=100, description="Evaluated risk score (0-100)")
    risk_level: str = Field(..., description="Evaluated risk level band")
    risk_label: str = Field(..., description="Formatted risk label (e.g. '88 High Risk')")
    created_at: datetime = Field(..., description="Timestamp when scan was performed")


class DashboardStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_scans: int = Field(..., ge=0, description="Total scans evaluated for the current user")
    threats_detected: int = Field(..., ge=0, description="High and Critical risk scans detected")
    suspicious: int = Field(..., ge=0, description="Suspicious and Medium risk scans detected")
    likely_safe: int = Field(..., ge=0, description="Likely Safe scans detected")
    risk_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of scans categorized per risk level",
    )
    scans_per_day: List[DailyScanCount] = Field(
        default_factory=list,
        description="Daily scan counts for the last 14 days",
    )
    top_categories: List[CategoryCount] = Field(
        default_factory=list,
        description="Top 5 threat categories with occurrence counts",
    )
    recent_scans: List[DashboardRecentScan] = Field(
        default_factory=list,
        description="Up to 5 latest scans evaluated for this user",
    )
