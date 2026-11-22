import type { Attachment, DashboardSummary, PaginatedScans, QualityParameter, ScanDetail, ScanListItem, User } from './types';

function toListItem(scan: ScanDetail): ScanListItem {
  return {
    id: scan.id,
    client_scan_id: scan.client_scan_id,
    sample_id: scan.sample_id,
    batch_id: scan.batch_id,
    lot_id: scan.lot_id,
    device_id: scan.device_id,
    department_id: scan.department_id,
    department_name: scan.department_name,
    processing_status: scan.processing_status,
    quality_verdict: scan.quality_verdict,
    analyzed_at: scan.analyzed_at,
    completed_at: scan.completed_at,
    grain_count: scan.grain_count,
    avg_length_mm: scan.avg_length_mm,
    avg_breadth_mm: scan.avg_breadth_mm,
    rice_age: scan.rice_age,
    report_available: scan.report_available,
    attachments: scan.attachments.map(item => item.role),
  };
}

export const mockUser: User = {
  id: 1,
  email: 'admin@grain-analyzer.local',
  full_name: 'Portal Administrator',
  role: 'SUPER_ADMIN',
  department_id: null,
};

const departments = [
  { id: 1, code: 'NQL', name: 'North Quality Lab', location: 'Guwahati', is_active: true },
  { id: 2, code: 'CPR', name: 'Central Procurement', location: 'Hyderabad', is_active: true },
  { id: 3, code: 'CST', name: 'Coastal Storage', location: 'Visakhapatnam', is_active: true },
];

const devices = [
  { device_id: 'GA-DEVICE-001', friendly_name: 'Lab analyzer A', model: 'GA-Optic 2', firmware_version: '1.4.2', department_id: 1 },
  { device_id: 'GA-DEVICE-002', friendly_name: 'Lab analyzer B', model: 'GA-Optic 2', firmware_version: '1.4.2', department_id: 1 },
  { device_id: 'GA-DEVICE-014', friendly_name: 'Procurement bench', model: 'GA-Optic 1', firmware_version: '1.3.8', department_id: 2 },
  { device_id: 'GA-DEVICE-021', friendly_name: 'Storage unit', model: 'GA-Optic 2', firmware_version: '1.4.0', department_id: 3 },
];

type ParamInput = [code: string, name: string, limit: string, mass: number, count: number, kernels: number, massG: number, status: string];

function parameters(rows: ParamInput[]): QualityParameter[] {
  return rows.map(([code, name, permissible_limit, mass_percent, count_percent, kernel_count, estimated_mass_g, status]) => ({
    code, name, permissible_limit, mass_percent, count_percent, kernel_count, estimated_mass_g, status,
  }));
}

const sampleParameters = parameters([
  ['HEAD_RICE', 'Head Rice (Whole Kernels >= 75%)', 'Min 75.00%', 50.68, 39.94, 145, 4.496, 'FLAG'],
  ['BIG_BROKEN', 'Big Broken Grains (25% - 75%)', 'Max 15.00%', 30.68, 50.69, 184, 2.721, 'FLAG'],
  ['SMALL_BROKEN', 'Small Broken Grains (< 25% Fragments)', 'Max 1.00%', 0, 0, 0, 0, 'PASS'],
  ['TOTAL_BROKENS', 'Total Brokens (Big + Small)', 'Max 16.00%', 30.68, 50.69, 184, 2.721, 'FLAG'],
  ['FOREIGN_MATTER', 'Foreign Matter (Inorganic/Organic)', 'Max 0.50%', 0, 0, 0, 0, 'PASS'],
  ['DAMAGED_INSECT_INFESTED', 'Damaged & Insect-Infested Grains', 'Max 2.00%', 0, 0, 0, 0, 'PASS'],
  ['DISCOLOURED_AMBER', 'Discoloured / Amber Grains', 'Max 1.00%', 0, 0, 0, 0, 'PASS'],
  ['CHALKY_GRAINS', 'Chalky Grains (>= 50% Opacity)', 'Max 3.00%', 0, 0, 0, 0, 'PASS'],
  ['DEHUSKED_UNMILLED_PADDY', 'Dehusked / Unmilled Paddy Grains', 'Max 10.00%', 0, 0, 0, 0, 'PASS'],
]);

const passingParameters = parameters([
  ['HEAD_RICE', 'Head Rice (Whole Kernels >= 75%)', 'Min 75.00%', 82.4, 79.1, 612, 14.22, 'PASS'],
  ['BIG_BROKEN', 'Big Broken Grains (25% - 75%)', 'Max 15.00%', 11.2, 13.4, 104, 1.93, 'PASS'],
  ['SMALL_BROKEN', 'Small Broken Grains (< 25% Fragments)', 'Max 1.00%', 0.4, 0.6, 5, 0.07, 'PASS'],
  ['TOTAL_BROKENS', 'Total Brokens (Big + Small)', 'Max 16.00%', 11.6, 14.0, 109, 2.0, 'PASS'],
  ['FOREIGN_MATTER', 'Foreign Matter (Inorganic/Organic)', 'Max 0.50%', 0.1, 0.1, 1, 0.02, 'PASS'],
  ['DAMAGED_INSECT_INFESTED', 'Damaged & Insect-Infested Grains', 'Max 2.00%', 0.3, 0.4, 3, 0.05, 'PASS'],
  ['DISCOLOURED_AMBER', 'Discoloured / Amber Grains', 'Max 1.00%', 0.2, 0.2, 2, 0.03, 'PASS'],
  ['CHALKY_GRAINS', 'Chalky Grains (>= 50% Opacity)', 'Max 3.00%', 1.1, 1.4, 11, 0.19, 'PASS'],
  ['DEHUSKED_UNMILLED_PADDY', 'Dehusked / Unmilled Paddy Grains', 'Max 10.00%', 2.4, 2.8, 22, 0.41, 'PASS'],
]);

const colorGuide = [
  { detected_color: 'Green', estimated_age: '1-2 Months', status: '—', color_hex: '#2f9b55' },
  { detected_color: 'Avocado Green', estimated_age: '3-5 Months', status: '—', color_hex: '#719345' },
  { detected_color: 'Yellow', estimated_age: '6-8 Months', status: '—', color_hex: '#e1c53c' },
  { detected_color: 'Yellow Orange', estimated_age: '8-10 Months', status: 'ACTIVE 100%', color_hex: '#e9a323' },
  { detected_color: 'Orange', estimated_age: '10-11 Months', status: '—', color_hex: '#dc782c' },
  { detected_color: 'Red', estimated_age: 'Above 1 Year', status: '—', color_hex: '#c83b3b' },
];

function hash(seed: string) {
  let value = 2166136261;
  for (let index = 0; index < seed.length; index += 1) value = Math.imul(value ^ seed.charCodeAt(index), 16777619);
  return (value >>> 0).toString(16).padStart(8, '0').repeat(8).slice(0, 64);
}

function attachments(scanId: number, roles: Array<'REPORT_PDF' | 'BOTTOM_PLATEN' | 'TOP_PLATEN'>): Attachment[] {
  return roles.map(role => ({
    role,
    content_type: role === 'REPORT_PDF' ? 'application/pdf' : 'image/svg+xml',
    size_bytes: role === 'REPORT_PDF' ? 186432 : 248800,
    verified: true,
    sha256: hash(`${scanId}-${role}`),
    url: `/api/v1/scans/${scanId}/files/${role}`,
  }));
}

function departmentById(id: number) {
  const department = departments.find(item => item.id === id);
  return department ? { id: department.id, code: department.code, name: department.name, location: department.location } : null;
}

function deviceById(deviceId: string) {
  return devices.find(item => item.device_id === deviceId);
}

interface ScanSeed {
  id: number;
  client_scan_id: string;
  sample_id: string;
  batch_id: string;
  lot_id: string;
  device_id: string;
  department_id: number;
  processing_status: string;
  quality_verdict: string | null;
  analyzed_at: string;
  completed_at: string | null;
  grain_count: number;
  sample_mass_est_g: number;
  avg_length_mm: number;
  avg_breadth_mm: number;
  grain_shape_ratio: number;
  grain_shape_label: string;
  parameters: QualityParameter[];
  age: ScanDetail['rice_age_result'];
  withFiles: boolean;
}

function buildScan(seed: ScanSeed): ScanDetail {
  const device = deviceById(seed.device_id);
  const files = seed.withFiles ? attachments(seed.id, ['REPORT_PDF', 'BOTTOM_PLATEN', 'TOP_PLATEN']) : [];
  return {
    id: seed.id,
    client_scan_id: seed.client_scan_id,
    sample_id: seed.sample_id,
    batch_id: seed.batch_id,
    lot_id: seed.lot_id,
    device_id: seed.device_id,
    department_id: seed.department_id,
    department_name: departmentById(seed.department_id)?.name ?? null,
    processing_status: seed.processing_status,
    quality_verdict: seed.quality_verdict,
    analyzed_at: seed.analyzed_at,
    completed_at: seed.completed_at,
    grain_count: seed.grain_count,
    avg_length_mm: seed.avg_length_mm,
    avg_breadth_mm: seed.avg_breadth_mm,
    rice_age: seed.age,
    report_available: files.some(file => file.role === 'REPORT_PDF'),
    attachments: files,
    department: departmentById(seed.department_id),
    device: device ? { device_id: device.device_id, friendly_name: device.friendly_name, model: device.model, firmware_version: device.firmware_version } : { device_id: seed.device_id },
    analysis: {
      grain_count: seed.grain_count,
      sample_mass_est_g: seed.sample_mass_est_g,
      avg_length_mm: seed.avg_length_mm,
      avg_breadth_mm: seed.avg_breadth_mm,
      grain_shape_ratio: seed.grain_shape_ratio,
      grain_shape_label: seed.grain_shape_label,
      unresolved_clusters: 0,
      optical_platen_unit: 'Primary platen',
    },
    evaluation: { overall: seed.quality_verdict, ruleset_version: 'sample-v1', certification_status: 'ADVISORY_ONLY' },
    rice_age_result: seed.age,
    quality_parameters: seed.parameters,
    measurements: [],
    advisory_only: true,
  };
}

const ageResult = (category: string, breakdown: string, freshness: string, activeColor: string): ScanDetail['rice_age_result'] => ({
  value: category.replace(' Months', ''),
  unit: 'months',
  category,
  model_version: 'color-guide-v1',
  confidence: 100,
  validation_status: 'DEVICE_REPORTED',
  sample_uniformity: 'Uniform Age',
  age_breakdown: breakdown,
  freshness_rating: freshness,
  testing_station: 'Grain Analyzer Chemical Unit',
  color_reference_guide: colorGuide.map(item => ({ ...item, status: item.detected_color === activeColor ? 'ACTIVE 100%' : '—' })),
});

export const mockScans: ScanDetail[] = [
  buildScan({
    id: 38, client_scan_id: 'SIM-SCAN-0038-FULL', sample_id: 'Sample-0038', batch_id: 'BATCH-2026-001', lot_id: 'LOT-A',
    device_id: 'GA-DEVICE-001', department_id: 1, processing_status: 'Completed', quality_verdict: 'FLAG',
    analyzed_at: '2026-11-20T11:07:52.000Z', completed_at: '2026-11-20T11:09:10.000Z',
    grain_count: 363, sample_mass_est_g: 8.87, avg_length_mm: 5.25, avg_breadth_mm: 2.61, grain_shape_ratio: 2.01, grain_shape_label: 'Short',
    parameters: sampleParameters, withFiles: true,
    age: ageResult('8-10 Months', '100% 8-10 Months', 'Sound Commercial Grain (Medium Storage Age)', 'Yellow Orange'),
  }),
  buildScan({
    id: 52, client_scan_id: 'GA-SCAN-0052', sample_id: 'Sample-0052', batch_id: 'BATCH-2026-004', lot_id: 'LOT-C',
    device_id: 'GA-DEVICE-014', department_id: 2, processing_status: 'Completed', quality_verdict: 'PASS',
    analyzed_at: '2026-11-21T06:42:00.000Z', completed_at: '2026-11-21T06:44:12.000Z',
    grain_count: 774, sample_mass_est_g: 17.26, avg_length_mm: 6.84, avg_breadth_mm: 2.11, grain_shape_ratio: 3.24, grain_shape_label: 'Slender',
    parameters: passingParameters, withFiles: true,
    age: ageResult('3-5 Months', '100% 3-5 Months', 'Fresh Commercial Grain (Short Storage Age)', 'Avocado Green'),
  }),
  buildScan({
    id: 61, client_scan_id: 'GA-SCAN-0061', sample_id: 'Sample-0061', batch_id: 'BATCH-2026-004', lot_id: 'LOT-C',
    device_id: 'GA-DEVICE-014', department_id: 2, processing_status: 'Awaiting Files', quality_verdict: null,
    analyzed_at: '2026-11-21T09:15:00.000Z', completed_at: null,
    grain_count: 410, sample_mass_est_g: 9.4, avg_length_mm: 6.1, avg_breadth_mm: 2.2, grain_shape_ratio: 2.77, grain_shape_label: 'Medium',
    parameters: [], withFiles: false, age: null,
  }),
  buildScan({
    id: 44, client_scan_id: 'GA-SCAN-0044', sample_id: 'Sample-0044', batch_id: 'BATCH-2026-002', lot_id: 'LOT-B',
    device_id: 'GA-DEVICE-002', department_id: 1, processing_status: 'Completed', quality_verdict: 'FLAG',
    analyzed_at: '2026-11-18T08:20:00.000Z', completed_at: '2026-11-18T08:22:40.000Z',
    grain_count: 512, sample_mass_est_g: 11.05, avg_length_mm: 5.48, avg_breadth_mm: 2.44, grain_shape_ratio: 2.25, grain_shape_label: 'Medium',
    parameters: parameters([
      ['HEAD_RICE', 'Head Rice (Whole Kernels >= 75%)', 'Min 75.00%', 61.2, 55.4, 284, 6.76, 'FLAG'],
      ['BIG_BROKEN', 'Big Broken Grains (25% - 75%)', 'Max 15.00%', 22.4, 28.1, 144, 2.48, 'FLAG'],
      ['SMALL_BROKEN', 'Small Broken Grains (< 25% Fragments)', 'Max 1.00%', 1.8, 2.4, 12, 0.2, 'FLAG'],
      ['TOTAL_BROKENS', 'Total Brokens (Big + Small)', 'Max 16.00%', 24.2, 30.5, 156, 2.68, 'FLAG'],
      ['FOREIGN_MATTER', 'Foreign Matter (Inorganic/Organic)', 'Max 0.50%', 0.2, 0.2, 1, 0.02, 'PASS'],
      ['DAMAGED_INSECT_INFESTED', 'Damaged & Insect-Infested Grains', 'Max 2.00%', 0.6, 0.8, 4, 0.07, 'PASS'],
      ['DISCOLOURED_AMBER', 'Discoloured / Amber Grains', 'Max 1.00%', 0.4, 0.5, 3, 0.04, 'PASS'],
      ['CHALKY_GRAINS', 'Chalky Grains (>= 50% Opacity)', 'Max 3.00%', 4.8, 5.6, 29, 0.53, 'FLAG'],
      ['DEHUSKED_UNMILLED_PADDY', 'Dehusked / Unmilled Paddy Grains', 'Max 10.00%', 3.1, 3.4, 17, 0.34, 'PASS'],
    ]),
    withFiles: true,
    age: ageResult('10-11 Months', '100% 10-11 Months', 'Aged Commercial Grain (Longer Storage)', 'Orange'),
  }),
  buildScan({
    id: 29, client_scan_id: 'GA-SCAN-0029', sample_id: 'Sample-0029', batch_id: 'BATCH-2026-001', lot_id: 'LOT-A',
    device_id: 'GA-DEVICE-021', department_id: 3, processing_status: 'Completed', quality_verdict: 'INCONCLUSIVE',
    analyzed_at: '2026-11-12T04:05:00.000Z', completed_at: '2026-11-12T04:08:00.000Z',
    grain_count: 198, sample_mass_est_g: 4.62, avg_length_mm: 5.9, avg_breadth_mm: 2.18, grain_shape_ratio: 2.71, grain_shape_label: 'Medium',
    parameters: passingParameters.map((row, index) => index === 0 ? { ...row, status: 'INCONCLUSIVE', mass_percent: 74.2, count_percent: 71.5 } : row),
    withFiles: true,
    age: ageResult('6-8 Months', '100% 6-8 Months', 'Sound Commercial Grain (Medium Storage Age)', 'Yellow'),
  }),
  buildScan({
    id: 17, client_scan_id: 'GA-SCAN-0017', sample_id: 'Sample-0017', batch_id: 'BATCH-2026-003', lot_id: 'LOT-D',
    device_id: 'GA-DEVICE-021', department_id: 3, processing_status: 'Completed', quality_verdict: 'PASS',
    analyzed_at: '2026-11-08T13:30:00.000Z', completed_at: '2026-11-08T13:32:18.000Z',
    grain_count: 690, sample_mass_est_g: 15.4, avg_length_mm: 7.02, avg_breadth_mm: 2.05, grain_shape_ratio: 3.42, grain_shape_label: 'Slender',
    parameters: passingParameters, withFiles: true,
    age: ageResult('1-2 Months', '100% 1-2 Months', 'Fresh Commercial Grain (Short Storage Age)', 'Green'),
  }),
  buildScan({
    id: 8, client_scan_id: 'GA-SCAN-0008', sample_id: 'Sample-0008', batch_id: 'BATCH-2025-118', lot_id: 'LOT-E',
    device_id: 'GA-DEVICE-002', department_id: 1, processing_status: 'Failed', quality_verdict: 'FLAG',
    analyzed_at: '2026-10-30T02:11:00.000Z', completed_at: null,
    grain_count: 88, sample_mass_est_g: 1.9, avg_length_mm: 4.8, avg_breadth_mm: 2.7, grain_shape_ratio: 1.78, grain_shape_label: 'Short',
    parameters: sampleParameters, withFiles: false, age: null,
  }),
  buildScan({
    id: 71, client_scan_id: 'GA-SCAN-0071', sample_id: 'Sample-0071', batch_id: 'BATCH-2026-006', lot_id: 'LOT-F',
    device_id: 'GA-DEVICE-001', department_id: 1, processing_status: 'Verifying', quality_verdict: 'PASS',
    analyzed_at: '2026-11-22T04:48:00.000Z', completed_at: null,
    grain_count: 540, sample_mass_est_g: 12.1, avg_length_mm: 6.4, avg_breadth_mm: 2.16, grain_shape_ratio: 2.96, grain_shape_label: 'Medium',
    parameters: passingParameters, withFiles: false, age: ageResult('3-5 Months', '100% 3-5 Months', 'Fresh Commercial Grain (Short Storage Age)', 'Avocado Green'),
  }),
].sort((left, right) => right.analyzed_at.localeCompare(left.analyzed_at) || right.id - left.id);

function includes(value: string | null | undefined, query: string) {
  return (value || '').toLowerCase().includes(query.trim().toLowerCase());
}

export function filterScans(params: URLSearchParams): PaginatedScans {
  const page = Math.max(1, Number(params.get('page') || 1));
  const pageSize = Math.max(1, Number(params.get('page_size') || 10));
  const sample = params.get('sample_id') || '';
  const batch = params.get('batch_id') || '';
  const lot = params.get('lot_id') || '';
  const device = params.get('device_id') || '';
  const verdict = (params.get('quality_verdict') || '').toUpperCase();
  const status = params.get('processing_status') || '';
  const from = params.get('date_from') || '';
  const to = params.get('date_to') || '';

  const matched = mockScans.filter(scan => {
    if (sample && !includes(scan.sample_id, sample) && !includes(scan.client_scan_id, sample)) return false;
    if (batch && !includes(scan.batch_id, batch)) return false;
    if (lot && !includes(scan.lot_id, lot)) return false;
    if (device && !includes(scan.device_id, device) && !includes(scan.device?.friendly_name, device)) return false;
    if (verdict && (scan.quality_verdict || '').toUpperCase() !== verdict) return false;
    if (status && scan.processing_status !== status) return false;
    const day = scan.analyzed_at.slice(0, 10);
    if (from && day < from) return false;
    if (to && day > to) return false;
    return true;
  });

  const start = (page - 1) * pageSize;
  const items = matched.slice(start, start + pageSize).map(toListItem);
  return { items, total: matched.length, page, page_size: pageSize, pages: Math.max(1, Math.ceil(matched.length / pageSize)) };
}

export function mockSummary(): DashboardSummary {
  const completed = mockScans.filter(scan => scan.processing_status === 'Completed');
  const latest = completed[0] ?? null;
  return {
    role: mockUser.role,
    department: null,
    counts: {
      total_scans: mockScans.length,
      completed_scans: completed.length,
      flagged_scans: completed.filter(scan => (scan.quality_verdict || '').toUpperCase() === 'FLAG').length,
      devices: devices.length,
    },
    latest_scan: latest,
    recent_scans: completed.slice(0, 6).map(toListItem),
    departments: departments.map(department => ({
      id: department.id,
      code: department.code,
      name: department.name,
      is_active: department.is_active,
      device_count: devices.filter(device => device.department_id === department.id).length,
      completed_scans: completed.filter(scan => scan.department_id === department.id).length,
    })),
  };
}

export function mockScan(id: number) {
  return mockScans.find(scan => scan.id === id) ?? null;
}

const platenPalette = ['#3d5c49', '#6d5332', '#35556a', '#5c4638', '#3f6248', '#6a4e2e'];

export function mockAsset(path: string) {
  const match = path.match(/\/scans\/(\d+)\/files\/([A-Z_]+)/);
  if (!match) throw new Error('Attachment not found');
  const scan = mockScan(Number(match[1]));
  const role = match[2];
  const attachment = scan?.attachments.find(item => item.role === role && item.verified);
  if (!scan || !attachment) throw new Error('Attachment not found');
  if (role === 'REPORT_PDF') return samplePdf(`${scan.sample_id} · ${scan.client_scan_id}`);
  const fill = platenPalette[scan.id % platenPalette.length];
  return platenImage(role === 'BOTTOM_PLATEN' ? 'Bottom platen' : 'Top platen', scan.sample_id, fill, role === 'TOP_PLATEN');
}

function platenImage(title: string, sample: string, fill: string, lighter: boolean) {
  const grains = Array.from({ length: 46 }, (_, index) => {
    const x = 36 + ((index * 137) % 900);
    const y = 36 + ((index * 89) % 430);
    const rx = 18 + (index % 6) * 6;
    const ry = 8 + (index % 4) * 2;
    const tone = lighter ? (index % 2 ? '#f3e2b0' : '#e7c98a') : (index % 2 ? '#f6e7c4' : '#d7b56a');
    return `<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="${tone}" transform="rotate(${(index * 23) % 70} ${x} ${y})"/>`;
  }).join('');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540"><rect width="960" height="540" fill="${fill}"/>${grains}<text x="36" y="508" fill="#f7f4ea" font-family="sans-serif" font-size="22" font-weight="400">${title} · ${sample}</text></svg>`;
  return new Blob([svg], { type: 'image/svg+xml' });
}

function samplePdf(title: string) {
  const safe = title.replace(/[()\\]/g, '');
  const lines = [
    `BT /F1 20 Tf 64 730 Td (Grain Analyzer) Tj ET`,
    `BT /F1 12 Tf 64 690 Td (Sample report) Tj ET`,
    `BT /F1 12 Tf 64 660 Td (${safe}) Tj ET`,
    `BT /F1 11 Tf 64 620 Td (Advisory sample output. Values match the on-screen inspection record.) Tj ET`,
  ];
  const stream = lines.join('\n');
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
    `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
  ];
  let body = '%PDF-1.4\n';
  const offsets = [0];
  objects.forEach((object, index) => {
    offsets.push(body.length);
    const suffix = index === 3 ? 'endobj\n' : 'endobj\n';
    body += `${index + 1} 0 obj ${object} ${suffix}`;
  });
  const xrefAt = body.length;
  let xref = `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (let index = 1; index < offsets.length; index += 1) xref += `${String(offsets[index]).padStart(10, '0')} 00000 n \n`;
  body += `${xref}trailer << /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefAt}\n%%EOF`;
  return new Blob([body], { type: 'application/pdf' });
}
