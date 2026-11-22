export type Role = 'SUPER_ADMIN' | 'DEPARTMENT_ADMIN' | 'DEPARTMENT_USER';
export interface User {
  id: number; email: string; full_name: string; role: Role; department_id: number | null;
}
export interface ScanListItem {
  id: number; client_scan_id: string; sample_id: string; batch_id: string | null; lot_id: string | null;
  device_id: string; department_id: number; department_name?: string | null; processing_status: string;
  quality_verdict: string | null; analyzed_at: string; completed_at: string | null; grain_count?: number | null;
  avg_length_mm?: number | null; avg_breadth_mm?: number | null; rice_age?: Record<string, unknown> | null;
  report_available: boolean; attachments: string[];
}
export interface QualityParameter {
  code: string; name: string | null; permissible_limit: string | null; mass_percent: number | null;
  count_percent: number | null; kernel_count: number | null; estimated_mass_g: number | null; status: string | null;
}
export interface AgeColorReference { detected_color: string; estimated_age: string; status?: string | null; color_hex?: string | null; }
export interface Attachment { role: string; content_type: string; size_bytes: number; verified: boolean; sha256: string; url: string; }
export interface ScanDetail extends Omit<ScanListItem, 'attachments'> {
  department?: { id: number; code: string; name: string; location: string | null } | null;
  device?: { device_id: string; friendly_name?: string | null; model?: string | null; firmware_version?: string | null };
  analysis: Record<string, unknown>;
  evaluation: Record<string, unknown>;
  rice_age_result: { value: string | null; unit: string | null; category: string | null; model_version: string | null; confidence: number | null; validation_status: string | null; sample_uniformity?: string | null; age_breakdown?: string | null; freshness_rating?: string | null; testing_station?: string | null; color_reference_guide?: AgeColorReference[] | null } | null;
  quality_parameters: QualityParameter[]; measurements: Array<{ metric_code: string; value: number; unit: string | null; basis: string | null; measured_vs_estimated: string | null; source_path: string }>;
  attachments: Attachment[]; advisory_only: boolean;
}
export interface DashboardSummary {
  role: Role; department: { id: number; code: string; name: string; location: string | null } | null;
  counts: { total_scans: number; completed_scans: number; flagged_scans: number; devices: number };
  latest_scan: ScanDetail | null; recent_scans: ScanListItem[];
  departments: Array<{ id: number; code: string; name: string; is_active: boolean; device_count: number; completed_scans: number }>;
}
export interface PaginatedScans { items: ScanListItem[]; total: number; page: number; page_size: number; pages: number; }
