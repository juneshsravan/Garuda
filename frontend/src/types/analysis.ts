export type RiskLevel =
  | "likely_safe"
  | "suspicious"
  | "medium"
  | "high"
  | "critical"
  | "unable_to_verify";

export interface RiskAssessment {
  score: number;
  level: RiskLevel;
  label: string;
}

export interface ThreatIndicator {
  code: string;
  label: string;
  severity: "low" | "medium" | "high" | "critical";
  weight: number;
  evidence: string;
}

export interface LegitimacySignal {
  code: string;
  label: string;
  weight: number;
  evidence: string;
}

export interface ThreatCategory {
  code: string;
  label: string;
}

export interface ExtractedData {
  urls: string[];
  qr?: string | null;
  upi?: {
    payee_vpa?: string;
    payee_name?: string;
    amount?: string;
    note?: string;
  } | null;
  language: string;
}

export interface IntelItem {
  source: string;
  status: "found" | "not_found" | "error";
  verdict?: string;
}

export interface AnalysisResponse {
  scan_id: string;
  scan_type: "message" | "url" | "qr" | "image";
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
}
