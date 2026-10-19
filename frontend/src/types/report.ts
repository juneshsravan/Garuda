export type ScamType =
  | "sms"
  | "whatsapp"
  | "call"
  | "link"
  | "qr_upi"
  | "email"
  | "other";

export type ReportStatus = "submitted" | "reviewed";

export interface CreateReportRequest {
  scan_id?: string | null;
  scam_type: ScamType;
  content: string;
  scammer_phone?: string | null;
  scammer_upi?: string | null;
  scammer_url?: string | null;
  amount_lost?: number | null;
  incident_date?: string | null;
}

export interface ReportItem {
  id: string;
  user_id: string;
  scan_id: string | null;
  scam_type: ScamType;
  content: string;
  scammer_phone: string | null;
  scammer_upi: string | null;
  scammer_url: string | null;
  amount_lost: number | null;
  incident_date: string | null;
  status: ReportStatus;
  created_at: string;
}

export interface ReportListResponse {
  items: ReportItem[];
  total: number;
}
