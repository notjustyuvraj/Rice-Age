import { useEffect, useState, type ReactNode } from 'react';
import { Activity, ArrowRight, ArrowUpRight, Building2, CheckCircle2, ChevronRight, Cpu, FlaskConical, RefreshCw, ScanLine, ShieldCheck, Wheat } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import type { DashboardSummary, ScanDetail, ScanListItem } from '../lib/types';
import StatusBadge from '../components/StatusBadge';
import AssetImage from '../components/AssetImage';

const dateLabel = (value?: string | null) => value ? new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : '—';
const n = (value: unknown, digits = 2) => typeof value === 'number' ? value.toFixed(digits) : '—';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const load = async () => { setLoading(true); setError(''); try { setData(await api.summary()); } catch(e) { setError(e instanceof Error ? e.message : 'Unable to load dashboard'); } finally { setLoading(false); } };
  useEffect(() => { void load(); }, []);
  if (loading) return <div className="page-loading"><div className="loading-orb"><RefreshCw className="animate-spin" size={21}/></div><p>Preparing your quality workspace…</p></div>;
  if (error) return <div className="page-error"><h2>Dashboard couldn't load</h2><p>{error}</p><button className="btn btn-primary" onClick={load}><RefreshCw size={16}/> Try again</button></div>;
  if (!data) return null;
  const isSuper = data.role === 'SUPER_ADMIN';
  return <div className="page-stack">
    <section className="page-heading"><div><div className="eyebrow">{isSuper ? 'CENTRAL OPERATIONS' : 'DEPARTMENT OVERVIEW'}</div><h1>{isSuper ? 'Good to see you.' : `Welcome to ${data.department?.name || 'your workspace'}.`}</h1><p>{isSuper ? 'A clear view of registered departments and completed rice inspections.' : 'A current view of your completed rice inspections and sample evidence.'}</p></div><button className="btn btn-secondary" onClick={load}><RefreshCw size={15}/> Refresh data</button></section>
    <section className="stat-grid">
      <StatCard label="Completed scans" value={data.counts.completed_scans} note={`${data.counts.total_scans} total submissions`} icon={<ScanLine size={19}/>} tone="green"/>
      <StatCard label="Flagged results" value={data.counts.flagged_scans} note="Source-reported quality flags" icon={<Activity size={19}/>} tone="amber"/>
      <StatCard label="Registered devices" value={data.counts.devices} note="Currently assigned devices" icon={<Cpu size={19}/>} tone="blue"/>
      <StatCard label={isSuper ? 'Departments' : 'Completion rate'} value={isSuper ? data.departments.length : `${data.counts.total_scans ? Math.round(data.counts.completed_scans / data.counts.total_scans * 100) : 0}%`} note={isSuper ? 'Registered workspaces' : 'Completed of all submissions'} icon={<Building2 size={19}/>} tone="violet"/>
    </section>
    {isSuper && <section className="panel"><div className="section-heading"><div><span className="eyebrow">ORGANIZATION</span><h2>Department overview</h2><p>Registered departments and their inspection activity.</p></div><span className="soft-count">{data.departments.length} departments</span></div>
      {data.departments.length ? <div className="department-grid">{data.departments.map(dept => <div className="department-card" key={dept.id}><div className="dept-icon"><Building2 size={19}/></div><div className="dept-state">{dept.is_active ? 'ACTIVE' : 'INACTIVE'}</div><h3>{dept.name}</h3><p>{dept.code}</p><div className="dept-stats"><span><strong>{dept.completed_scans}</strong><small>Completed scans</small></span><span><strong>{dept.device_count}</strong><small>Devices</small></span></div></div>)}</div> : <EmptyInline title="No departments registered" text="Create a department through the administration API to begin assigning devices."/>}
    </section>}
    <LatestScan scan={data.latest_scan}/>
    <RecentScans scans={data.recent_scans}/>
  </div>;
}

function StatCard({label,value,note,icon,tone}:{label:string;value:string|number;note:string;icon:ReactNode;tone:string}) {
  return <div className="stat-card"><div className={`stat-icon ${tone}`}>{icon}</div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-note">{note}</div></div>;
}
function LatestScan({scan}:{scan:ScanDetail|null}) {
  if (!scan) return <section className="panel latest-empty"><div className="empty-illustration"><Wheat size={30}/></div><div><span className="eyebrow">LATEST COMPLETED INSPECTION</span><h2>No completed scan yet</h2><p>When a registered device completes an upload, its result and original report will appear here.</p></div></section>;
  const analysis = scan.analysis || {}; const age = scan.rice_age_result;
  const bottom = scan.attachments.find(a=>a.role==='BOTTOM_PLATEN'); const top = scan.attachments.find(a=>a.role==='TOP_PLATEN');
  return <section className="panel latest-panel">
    <div className="section-heading latest-heading"><div><span className="eyebrow">LATEST COMPLETED INSPECTION</span><h2>Latest rice analysis</h2><p>{scan.sample_id} <span className="dot-sep">·</span> {scan.batch_id || 'No batch'} <span className="dot-sep">·</span> {scan.lot_id || 'No lot'}</p></div><div className="latest-status"><StatusBadge value={scan.quality_verdict}/><span className="advisory-text">{scan.advisory_only ? 'Advisory · source-reported result' : 'Device-reported verdict'}</span></div></div>
    <div className="scan-meta-row"><span><span className="meta-label">SCAN ID</span><strong>{scan.client_scan_id}</strong></span><span><span className="meta-label">DEVICE</span><strong>{scan.device?.friendly_name || scan.device_id}</strong></span><span><span className="meta-label">ANALYZED</span><strong>{dateLabel(scan.analyzed_at)}</strong></span><span><span className="meta-label">PROCESSING</span><StatusBadge value={scan.processing_status}/></span></div>
    <div className="metric-grid">
      <Metric icon={<Wheat size={17}/>} label="Grains detected" value={typeof analysis.grain_count==='number'?analysis.grain_count.toLocaleString('en-IN'):'—'} helper="Device-reported count"/>
      <Metric icon={<FlaskConical size={17}/>} label="Estimated sample mass" value={typeof analysis.sample_mass_est_g==='number'?`${n(analysis.sample_mass_est_g)} g`:'—'} helper="Optical estimate"/>
      <Metric icon={<Activity size={17}/>} label="Average length" value={typeof analysis.avg_length_mm==='number'?`${n(analysis.avg_length_mm)} mm`:'—'} helper="Device-reported"/>
      <Metric icon={<ArrowUpRight size={17}/>} label="Rice age" value={age?.category || (age?.value ? `${age.value} ${age.unit || ''}` : 'Not available')} helper={age?.validation_status || 'No age output supplied'}/>
    </div>
    <div className="evidence-grid"><div className="evidence-panel"><div className="subsection-title"><div><h3>Optical evidence</h3><p>Uploaded inspection image evidence</p></div><span className="soft-count">{scan.client_scan_id.startsWith('SIM-') ? 'Simulation fixtures' : (bottom && top ? '2 captures' : 'Evidence status')}</span></div><div className="image-pair">{bottom ? <AssetImage path={`/api/v1/scans/${scan.id}/files/BOTTOM_PLATEN`} title="Bottom platen · primary"/> : <div className="asset-frame asset-placeholder"><span>Bottom platen unavailable</span></div>}{top ? <AssetImage path={`/api/v1/scans/${scan.id}/files/TOP_PLATEN`} title="Top platen · verification"/> : <div className="asset-frame asset-placeholder"><span>Top platen unavailable</span></div>}</div></div>
      <div className="quality-panel"><div className="subsection-title"><div><h3>Quality measurements</h3><p>Source values retained by measurement basis</p></div><span className="count-pill">{scan.quality_parameters.length} parameters</span></div><QualityTable rows={scan.quality_parameters}/><div className="basis-note"><ShieldCheck size={15}/> Mass-basis and count-basis percentages are shown separately; no combined average is calculated.</div></div></div>
    <div className="latest-footer"><div className="footer-note"><CheckCircle2 size={16}/> Report and attachments verified at scan completion.</div><div className="flex gap-2"><Link className="btn btn-secondary" to={`/scans/${scan.id}`}>View scan details <ChevronRight size={15}/></Link></div></div>
  </section>;
}
function Metric({icon,label,value,helper}:{icon:ReactNode;label:string;value:string;helper:string}) {return <div className="metric-card"><span className="metric-icon">{icon}</span><span className="metric-label">{label}</span><strong>{value}</strong><small>{helper}</small></div>}
export function QualityTable({rows}:{rows:ScanDetail['quality_parameters']}) {
  if (!rows.length) return <EmptyInline title="No quality parameters supplied" text="The connected device did not include a parameter breakdown in this scan."/>;
  return <div className="table-wrap"><table className="quality-table"><thead><tr><th>QUALITY PARAMETER</th><th>PERMISSIBLE LIMIT</th><th>MASS BASIS %</th><th>COUNT BASIS %</th><th>KERNEL COUNT & MASS</th><th>STATUS</th></tr></thead><tbody>{rows.map(row=><tr key={row.code}><td><strong>{row.name || row.code.replaceAll('_',' ')}</strong><small>{row.code}</small></td><td>{row.permissible_limit || '—'}</td><td>{row.mass_percent != null ? `${n(row.mass_percent)}%` : '—'}</td><td>{row.count_percent != null ? `${n(row.count_percent)}%` : '—'}</td><td><strong>{row.kernel_count != null ? `${row.kernel_count.toLocaleString('en-IN')} kernels` : '—'}</strong><small>{row.estimated_mass_g != null ? `${row.estimated_mass_g.toFixed(3)} g` : 'Mass not supplied'}</small></td><td><StatusBadge value={row.status}/></td></tr>)}</tbody></table></div>;
}
function RecentScans({scans}:{scans:ScanListItem[]}) {return <section className="panel"><div className="section-heading"><div><span className="eyebrow">ACTIVITY</span><h2>Recent completed scans</h2><p>Latest records available in your authorized workspace.</p></div><Link className="text-link" to="/scans">View scan history <ArrowRight size={15}/></Link></div>{scans.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>SAMPLE</th><th>BATCH / LOT</th><th>ANALYZED</th><th>GRAINS</th><th>RESULT</th><th/></tr></thead><tbody>{scans.map(scan=><tr key={scan.id}><td><Link className="sample-link" to={`/scans/${scan.id}`}>{scan.sample_id}<small>{scan.client_scan_id}</small></Link></td><td>{scan.batch_id || '—'}<small className="cell-sub">{scan.lot_id || 'No lot'}</small></td><td>{dateLabel(scan.analyzed_at)}</td><td>{scan.grain_count ?? '—'}</td><td><StatusBadge value={scan.quality_verdict}/></td><td><Link className="row-arrow" to={`/scans/${scan.id}`}><ChevronRight size={17}/></Link></td></tr>)}</tbody></table></div> : <EmptyInline title="No completed scans" text="Completed device submissions will be listed here."/>}</section>}
function EmptyInline({title,text}:{title:string;text:string}) {return <div className="empty-inline"><div className="empty-illustration small"><ScanLine size={20}/></div><div><strong>{title}</strong><p>{text}</p></div></div>}
