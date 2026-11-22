import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Activity, Bell, ChevronDown, ClipboardList, LayoutDashboard, LogOut, Menu, ShieldCheck, Sprout, X } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  if (!user) return null;
  const roleName = user.role === 'SUPER_ADMIN' ? 'Super administrator' : user.role === 'DEPARTMENT_ADMIN' ? 'Department administrator' : 'Department user';
  const close = () => setMobileOpen(false);
  const nav = <>
    <div className="sidebar-section-label">WORKSPACE</div>
    <NavLink to="/dashboard" onClick={close} className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}><LayoutDashboard size={18}/><span>Dashboard</span></NavLink>
    <NavLink to="/scans" onClick={close} className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}><ClipboardList size={18}/><span>Scan history</span></NavLink>
    <div className="sidebar-section-label mt-8">SYSTEM</div>
    <div className="nav-link disabled" title="Planned for a later release"><Activity size={18}/><span>Quality analytics</span><span className="nav-soon">P4</span></div>
    <div className="nav-link disabled" title="Planned for a later release"><Bell size={18}/><span>Notifications</span><span className="nav-soon">P5</span></div>
  </>;
  return <div className="app-shell">
    {mobileOpen && <button className="mobile-scrim" onClick={close} aria-label="Close menu"/>}
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
      <div className="brand"><div className="brand-mark"><Sprout size={21}/></div><div><div className="brand-name">Grain Analyzer</div><div className="brand-sub">QUALITY INTELLIGENCE</div></div><button className="mobile-close" onClick={close}><X size={18}/></button></div>
      <div className="workspace-pill"><span className="workspace-dot"/><div><strong>{user.role === 'SUPER_ADMIN' ? 'Central workspace' : 'Department workspace'}</strong><small>{user.role === 'SUPER_ADMIN' ? 'All departments' : `Department #${user.department_id ?? '—'}`}</small></div><ChevronDown size={14}/></div>
      <nav className="sidebar-nav">{nav}</nav>
      <div className="sidebar-bottom"><div className="security-note"><ShieldCheck size={17}/><div><strong>Protected workspace</strong><small>Department access is enforced by the server.</small></div></div><div className="sidebar-user"><div className="avatar">{user.full_name.split(' ').map(x=>x[0]).slice(0,2).join('').toUpperCase()}</div><div className="min-w-0 flex-1"><strong className="truncate">{user.full_name}</strong><small>{roleName}</small></div><button className="icon-button subtle" title="Sign out" onClick={() => { logout(); navigate('/login'); }}><LogOut size={17}/></button></div></div>
    </aside>
    <div className="main-column"><header className="topbar"><button className="mobile-menu" onClick={() => setMobileOpen(true)}><Menu size={20}/></button><div className="breadcrumb"><span>Grain Analyzer</span><span className="crumb-slash">/</span><span>Portal</span></div><div className="topbar-right"><span className="secure-chip"><span/> Secure session</span><div className="topbar-avatar">{user.full_name.slice(0,1).toUpperCase()}</div></div></header><main className="main-content"><Outlet/></main><footer className="app-footer"><span>GRAIN ANALYZER · DEPARTMENTAL QUALITY PORTAL</span><span>Prototype / advisory data remains subject to source validation.</span></footer></div>
  </div>;
}
