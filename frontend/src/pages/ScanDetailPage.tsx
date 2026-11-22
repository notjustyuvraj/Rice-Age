import { useEffect, useState, type ReactNode } from 'react';
import { ArrowLeft, CalendarClock, FileCheck2, FileText, Layers3, MapPin, ShieldCheck, Wheat, Ruler, FlaskConical } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import type { ScanDetail } from '../lib/types';
import StatusBadge from '../components/StatusBadge';
import AssetImage from '../components/AssetImage';
import PdfPreview from '../components/PdfPreview';
import { QualityTable } from './DashboardPage';

const dateLabel = (value?: string | null) => value ? new Intl.DateTimeFormat('en-IN', { dateStyle: 'full', timeStyle: 'short' }).format(new Date(value)) : '—';
const display = (value: unknown, suffix = '') => typeof value === 'number' && Number.isFinite(value) ? `${value.toLocaleString('en-IN', { maximumFractionDigits: 3 })}${suffix}` : (typeof value === 'string' && value.trim() ? `${value}${suffix}` : '—');

export default function ScanDetailPage() {
  const { id } = useParams();
  const [scan, setScan] = useState<ScanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pdfOpen, setPdfOpen] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    api.scan(Number(id))
      .then(value => { if (active) setScan(value); })
      .catch(e => { if (active) setError(e instanceof Error ? e.message : 'Unable to load scan'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id]);

  if (loading) return <div className="page-loading"><div className="loading-orb"><Layers3 className="animate-pulse" size={21}/></div><p>Loading scan record…</p></div>;
  if (error || !scan) return <div className="page-error"><h2>Scan unavailable</h2><p>{error || 'The requested scan could not be found in your workspace.'}</p><Link className="btn btn-secondary" to="/scans"><ArrowLeft size={16}/> Back to history</Link></div>;

  const analysis = scan.analysis || {};
  const age = scan.rice_age_result;
  const bottom = scan.attachments.find(attachment => attachment.role === 'BOTTOM_PLATEN');
  const top = scan.attachments.find(attachment => attachment.role === 'TOP_PLATEN');
  const report = scan.attachments.find(attachment => attachment.role === 'REPORT_PDF');
  const colorGuide = age?.color_reference_guide || [];
  const ageValue = age?.category || (age?.value ? `${age.value} ${age.unit || ''}`.trim() : 'Not available');

  return <div className="page-stack">
    <div className="back-row"><Link to="/scans" className="back-link"><ArrowLeft size={16}/> Back to scan history</Link><div className="flex gap-2"><StatusBadge value={scan.processing_status}/><StatusBadge value={scan.quality_verdict}/></div></div>

    <section className="detail-hero panel">
      <div>
        <div className="eyebrow">SCAN RECORD · #{scan.id}</div>
        <h1>{scan.sample_id}</h1>
        <p>{scan.client_scan_id} <span className="dot-sep">·</span> {scan.batch_id || 'No batch'} <span className="dot-sep">·</span> {scan.lot_id || 'No lot'}</p>
        <div className="detail-subline"><span><CalendarClock size={15}/>{dateLabel(scan.analyzed_at)}</span><span><MapPin size={15}/>{scan.department?.name || `Department #${scan.department_id}`}</span></div>
      </div>
      <div className="report-action-block">
        <div className="report-file"><FileCheck2 size={20}/><div><strong>{report ? 'Original report available' : 'No report attached'}</strong><small>{report ? `${(report.size_bytes / 1024 / 1024).toFixed(2)} MB · verified upload` : 'The device did not submit a PDF'}</small></div></div>
        <button className="btn btn-primary" disabled={!report || !report.verified} onClick={() => setPdfOpen(true)}><FileText size={16}/> Preview original PDF</button>
      </div>
    </section>

    {scan.advisory_only && <div className="advisory-banner"><ShieldCheck size={17}/><div><strong>Advisory / prototype output</strong><span>This record preserves device-reported values. It is not presented by the portal as statutory certification.</span></div></div>}

    <section className="stat-grid detail-metrics">
      <Metric label="Total grains" value={display(analysis.grain_count)} helper="Device-reported count" icon={<Wheat size={18}/>}/>
      <Metric label="Estimated sample mass" value={display(analysis.sample_mass_est_g, ' g')} helper="Optical estimate" icon={<Layers3 size={18}/>}/>
      <Metric label="Average dimensions" value={`${display(analysis.avg_length_mm)} × ${display(analysis.avg_breadth_mm)} mm`} helper="Length × breadth" icon={<Ruler size={18}/>}/>
      <Metric label="Biochemical age" value={ageValue} helper={age?.validation_status || 'No age output supplied'} icon={<CalendarClock size={18}/>}/>
    </section>

    <section className="panel">
      <div className="section-heading"><div><span className="eyebrow">SAMPLE CHARACTERISTICS</span><h2>Grain profile</h2><p>Device-supplied sample measurements and optical inspection metadata.</p></div></div>
      <div className="detail-fact-grid">
        <Fact label="Grain shape ratio (L/B)" value={display(analysis.grain_shape_ratio)}/>
        <Fact label="Grain shape" value={display(analysis.grain_shape_label)}/>
        <Fact label="Unresolved clusters" value={display(analysis.unresolved_clusters)}/>
        <Fact label="Optical platen unit" value={display(analysis.optical_platen_unit || analysis.platen_unit)}/>
        <Fact label="Analysis timestamp" value={dateLabel(scan.analyzed_at)}/>
        <Fact label="Completion timestamp" value={dateLabel(scan.completed_at)}/>
      </div>
    </section>

    <section className="panel">
      <div className="section-heading"><div><span className="eyebrow">VISUAL EVIDENCE</span><h2>Optical platen captures</h2><p>Select an image to enlarge it. Simulator runs can contain generated placeholders.</p></div><span className="soft-count">{[bottom, top].filter(Boolean).length} of 2 available</span></div>
      <div className="detail-image-grid">{bottom ? <AssetImage path={`/api/v1/scans/${scan.id}/files/BOTTOM_PLATEN`} title="Bottom platen · primary"/> : <div className="asset-frame asset-placeholder">Bottom platen unavailable</div>}{top ? <AssetImage path={`/api/v1/scans/${scan.id}/files/TOP_PLATEN`} title="Top platen · verification"/> : <div className="asset-frame asset-placeholder">Top platen unavailable</div>}</div>
    </section>

    <section className="panel">
      <div className="section-heading"><div><span className="eyebrow">SOURCE EVALUATION</span><h2>Quality parameter breakdown</h2><p>Original device values, permissible limits and individual statuses.</p></div><StatusBadge value={scan.quality_verdict}/></div>
      <QualityTable rows={scan.quality_parameters}/>
      <div className="basis-note mt-4"><ShieldCheck size={15}/> Mass-basis and count-basis percentages are independent source measures. The portal does not combine them or recalculate the source verdict.</div>
    </section>

    <section className="panel">
      <div className="section-heading"><div><span className="eyebrow">BIOCHEMICAL RICE AGE</span><h2>Age & milling freshness evaluation</h2><p>Only values supplied by the device are displayed.</p></div><span className="soft-count">{age?.validation_status || 'Age unavailable'}</span></div>
      {age ? <>
        <div className="detail-fact-grid age-fact-grid">
          <Fact label="Age breakdown" value={display(age.age_breakdown || age.category || age.value)}/>
          <Fact label="Sample uniformity" value={display(age.sample_uniformity)}/>
          <Fact label="Freshness rating" value={display(age.freshness_rating)}/>
          <Fact label="Testing station" value={display(age.testing_station)}/>
          <Fact label="Declared unit" value={display(age.unit)}/>
          <Fact label="Model / method version" value={display(age.model_version)}/>
          <Fact label="Confidence" value={age.confidence != null ? `${display(age.confidence)}%` : 'Not supplied'}/>
        </div>
        {colorGuide.length > 0 && <div className="color-guide-wrap"><h3>Color reference guide · estimated age ranges</h3><div className="table-wrap"><table className="quality-table"><thead><tr><th>DETECTED COLOR</th><th>ESTIMATED AGE</th><th>STATUS</th></tr></thead><tbody>{colorGuide.map((item, index) => <tr key={`${item.detected_color}-${index}`}><td><span className="color-swatch" style={{backgroundColor: item.color_hex || '#b4b9ae'}}/>{item.detected_color}</td><td>{item.estimated_age}</td><td>{item.status || '—'}</td></tr>)}</tbody></table></div></div>}
      </> : <div className="empty-inline"><div className="empty-illustration small"><FlaskConical size={20}/></div><div><strong>Age result not available</strong><p>The device did not supply an age estimate for this scan. The portal does not infer age from images.</p></div></div>}
    </section>

    <section className="detail-two-col">
      <div className="panel"><div className="section-heading"><div><span className="eyebrow">DEVICE</span><h2>Inspection source</h2></div></div><dl className="detail-list"><DetailRow label="Device ID" value={scan.device_id}/><DetailRow label="Friendly name" value={scan.device?.friendly_name || '—'}/><DetailRow label="Model" value={scan.device?.model || '—'}/><DetailRow label="Firmware" value={scan.device?.firmware_version || '—'}/><DetailRow label="Ruleset version" value={String(scan.evaluation.ruleset_version || '—')}/></dl></div>
      <div className="panel"><div className="section-heading"><div><span className="eyebrow">ATTACHMENTS</span><h2>Verified files</h2></div></div><div className="attachment-list">{scan.attachments.length ? scan.attachments.map(attachment => <div className="attachment-row" key={attachment.role}><span className="attachment-icon">{attachment.content_type === 'application/pdf' ? <FileText size={17}/> : <Layers3 size={17}/>}</span><div className="min-w-0 flex-1"><strong>{attachment.role.replaceAll('_', ' ')}</strong><small>{(attachment.size_bytes / 1024).toFixed(1)} KB · SHA-256 {attachment.sha256.slice(0, 12)}…</small></div><StatusBadge value={attachment.verified ? 'VERIFIED' : 'UNVERIFIED'}/></div>) : <p className="muted-copy">No verified attachments are available.</p>}</div></div>
    </section>

    {pdfOpen && <PdfPreview scanId={scan.id} onClose={() => setPdfOpen(false)}/>}
  </div>;
}

function Metric({label, value, helper, icon}: {label: string; value: string; helper: string; icon: ReactNode}) {
  return <div className="stat-card"><div className="stat-icon green">{icon}</div><div className="stat-label">{label}</div><div className="stat-value text-value">{value}</div><div className="stat-note">{helper}</div></div>;
}
function Fact({label, value}: {label: string; value: string}) {
  return <div className="detail-fact"><span>{label}</span><strong>{value}</strong></div>;
}
function DetailRow({label, value}: {label: string; value: string}) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}
