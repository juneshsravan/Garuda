// Types matching docs/ARCHITECTURE.md Section 6 & 8

export type RiskLevel =
  | "likely_safe"
  | "suspicious"
  | "medium"
  | "high"
  | "critical"
  | "unable_to_verify";

export interface RiskAssessment {
  score: number;
  level: RiskLevel | string;
  label: string;
}

export interface ThreatIndicator {
  code: string;
  label: string;
  severity: "low" | "medium" | "high" | "critical" | string;
  weight: number;
  evidence?: string | null;
}

export interface LegitimacySignal {
  code: string;
  label: string;
  weight: number;
  evidence?: string | null;
}

export interface ThreatCategory {
  code: string;
  label: string;
}

export interface ExtractedData {
  urls: any[];
  qr?: any;
  upi?: any;
  phone?: string[] | null;
  language?: string | null;
}

export interface IntelItem {
  source: string;
  status: string;
  details?: Record<string, any> | null;
}

export interface MessageDetail {
  content: string;
  detected_language?: string | null;
}

export interface AnalysisResponse {
  scan_id?: string | null;
  scan_type: "message" | "url" | "qr" | "image" | string;
  risk: RiskAssessment;
  confidence: number;
  verification_status: string;
  category: ThreatCategory;
  summary: string;
  indicators: ThreatIndicator[];
  legitimacy_signals: LegitimacySignal[];
  recommendations: string[];
  verify_steps: string[];
  extracted: ExtractedData;
  intel: IntelItem[];
  engine_version: string;
  created_at?: string | null;
  message?: MessageDetail | null;
}

export interface ScanListItem {
  id: string;
  scan_type: "message" | "url" | "qr" | "image" | string;
  status: string;
  created_at: string;
  risk: RiskAssessment;
  category: ThreatCategory;
  confidence: number;
  verification_status: string;
  summary?: string | null;
  content_preview?: string | null;
}

export interface ScanListResponse {
  items: ScanListItem[];
  next_cursor?: string | null;
  has_more: boolean;
}
