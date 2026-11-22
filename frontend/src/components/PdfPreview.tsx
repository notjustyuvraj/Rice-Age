import { useEffect, useRef, useState } from 'react';
import { X, Download, LoaderCircle, FileText, AlertCircle, Printer, ExternalLink } from 'lucide-react';
import { api } from '../lib/api';

export default function PdfPreview({ scanId, onClose }: { scanId: number; onClose: () => void }) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState('');
  const frameRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    api.asset(`/api/v1/scans/${scanId}/files/REPORT_PDF`)
      .then(url => {
        objectUrl = url;
        if (active) setSrc(url);
        else URL.revokeObjectURL(url);
      })
      .catch(e => { if (active) setError(e instanceof Error ? e.message : 'Unable to load report'); });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [scanId]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  const download = () => {
    if (!src) return;
    const anchor = document.createElement('a');
    anchor.href = src;
    anchor.download = `rice-age-scan-${scanId}.pdf`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  };

  const print = () => {
    if (!src) return;
    try {
      const frameWindow = frameRef.current?.contentWindow;
      if (frameWindow) {
        frameWindow.focus();
        frameWindow.print();
        return;
      }
    } catch {
      // Browser PDF viewers sometimes block iframe.print(); fall back to a separate tab.
    }
    window.open(src, '_blank', 'noopener,noreferrer');
  };

  const openInTab = () => { if (src) window.open(src, '_blank', 'noopener,noreferrer'); };

  return <div className="modal-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="pdf-modal" role="dialog" aria-modal="true" aria-label="Original device report">
      <header className="pdf-modal-head">
        <div className="flex items-center gap-3"><span className="icon-tile"><FileText size={18}/></span><div><p className="font-semibold text-ink">Original device report</p><p className="text-xs text-muted">Scan #{scanId} · Uploaded PDF · Original bytes preserved</p></div></div>
        <div className="pdf-actions">
          <button className="btn btn-secondary btn-small" onClick={openInTab} disabled={!src}><ExternalLink size={14}/> Open</button>
          <button className="btn btn-secondary btn-small" onClick={print} disabled={!src}><Printer size={14}/> Print</button>
          <button className="btn btn-secondary btn-small" onClick={download} disabled={!src}><Download size={14}/> Download</button>
          <button className="icon-button" onClick={onClose} aria-label="Close"><X size={18}/></button>
        </div>
      </header>
      <div className="pdf-stage">
        {src ? <iframe ref={frameRef} title="Original device report PDF" src={src}/> : error ? <div className="empty-state"><AlertCircle/><p>{error}</p></div> : <div className="empty-state"><LoaderCircle className="animate-spin"/><p>Loading original report…</p></div>}
      </div>
    </section>
  </div>;
}
