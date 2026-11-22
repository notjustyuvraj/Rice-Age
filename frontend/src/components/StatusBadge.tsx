import { CheckCircle2, AlertTriangle, XCircle, Clock3 } from 'lucide-react';

export default function StatusBadge({ value }: { value?: string | null }) {
  const normalized = (value || 'UNKNOWN').toUpperCase();
  const good = ['PASS', 'COMPLETED', 'ACTIVE', 'VERIFIED'].includes(normalized);
  const bad = ['FLAG', 'FAILED', 'SUSPENDED', 'REJECTED'].includes(normalized);
  const pending = ['RECEIVED', 'AWAITING FILES', 'VERIFYING', 'PENDING_ENROLLMENT', 'INCONCLUSIVE'].includes(normalized);
  const cls = good ? 'status-good' : bad ? 'status-bad' : pending ? 'status-pending' : 'status-neutral';
  const Icon = good ? CheckCircle2 : bad ? XCircle : pending ? Clock3 : AlertTriangle;
  return <span className={`status-badge ${cls}`}><Icon size={13}/>{value || 'Not available'}</span>;
}
