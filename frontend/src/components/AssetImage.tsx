import { useEffect, useState } from 'react';
import { ImageOff, LoaderCircle, X, ZoomIn } from 'lucide-react';
import { api } from '../lib/api';

export default function AssetImage({ path, title }: { path: string; title: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const [zoomed, setZoomed] = useState(false);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    setSrc(null);
    setError(false);
    api.asset(path)
      .then(url => {
        objectUrl = url;
        if (active) setSrc(url);
        else URL.revokeObjectURL(url);
      })
      .catch(() => { if (active) setError(true); });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [path]);

  useEffect(() => {
    if (!zoomed) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setZoomed(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [zoomed]);

  return <>
    <div className="asset-frame">
      {src ? <button type="button" className="asset-image-trigger" onClick={() => setZoomed(true)} aria-label={`Enlarge ${title}`}>
        <img src={src} alt={title}/><span className="asset-zoom-hint"><ZoomIn size={14}/> Enlarge</span>
      </button> : error ? <div className="asset-fallback"><ImageOff size={20}/><span>Image unavailable</span></div> : <div className="asset-fallback"><LoaderCircle className="animate-spin" size={20}/><span>Loading {title.toLowerCase()}…</span></div>}
      <span className="asset-label">{title}</span>
    </div>
    {zoomed && src && <div className="image-lightbox" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setZoomed(false); }}>
      <section className="image-lightbox-content" role="dialog" aria-modal="true" aria-label={title}>
        <header><strong>{title}</strong><button type="button" className="icon-button" onClick={() => setZoomed(false)} aria-label="Close enlarged image"><X size={19}/></button></header>
        <img src={src} alt={title}/>
      </section>
    </div>}
  </>;
}
