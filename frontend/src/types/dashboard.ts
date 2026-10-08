export interface DailyScanCount {
  date: string;
  count: number;
}

export interface CategoryCount {
  code: string;
  label: string;
  count: number;
}

export interface DashboardRecentScan {
  id: string;
  scan_type: string;
  preview: string | null;
  risk_score: number;
  risk_level: string;
  risk_label: string;
  created_at: string;
}

export interface DashboardStatsResponse {
  total_scans: number;
  threats_detected: number;
  suspicious: number;
  likely_safe: number;
  risk_distribution: Record<string, number>;
  scans_per_day: DailyScanCount[];
  top_categories: CategoryCount[];
  recent_scans: DashboardRecentScan[];
}
