import { FormEvent, useState } from 'react';
import { ArrowRight, Eye, EyeOff, LockKeyhole, ShieldCheck, Sprout } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth(); const navigate = useNavigate();
  const [email, setEmail] = useState(''); const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  async function submit(e: FormEvent) { e.preventDefault(); setBusy(true); setError(''); try { await login(email.trim(), password); navigate('/dashboard', { replace: true }); } catch (err) { setError(err instanceof Error ? err.message : 'Unable to sign in'); } finally { setBusy(false); } }
  return <div className="login-page">
    <div className="login-aside"><div className="login-brand"><div className="brand-mark"><Sprout size={22}/></div><div><div className="brand-name text-white">rice<span>age</span></div><div className="brand-sub text-white/55">QUALITY INTELLIGENCE</div></div></div>
      <div className="login-message"><span className="eyebrow text-emerald-200">FIELD DATA · MADE CLEAR</span><h1>Better visibility<br/>from every <em>grain.</em></h1><p>A secure workspace for rice quality scans, sample evidence and departmental reporting.</p><div className="login-feature"><span><ShieldCheck size={17}/></span><div><strong>Department-scoped access</strong><small>Every scan and attachment is protected by your assigned access.</small></div></div><div className="login-feature"><span><ScanLineIcon/></span><div><strong>Connected inspection records</strong><small>Review completed device submissions and their original evidence.</small></div></div></div>
      <div className="login-aside-foot">RICE AGE PORTAL <span>·</span> INTERNAL WORKSPACE</div>
    </div>
    <div className="login-panel"><div className="login-form-wrap"><div className="login-mobile-brand"><div className="brand-mark"><Sprout size={20}/></div><span className="brand-name">rice<span>age</span></span></div><div className="login-heading"><span className="eyebrow">WELCOME BACK</span><h2>Sign in to your workspace</h2><p>Use the account created by your system administrator.</p></div>
      <form onSubmit={submit} className="login-form"><label>Email address<input autoComplete="username" type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="name@department.gov.in"/></label><label>Password<div className="password-wrap"><input autoComplete="current-password" type={showPassword?'text':'password'} required value={password} onChange={e=>setPassword(e.target.value)} placeholder="Enter your password"/><button type="button" onClick={()=>setShowPassword(v=>!v)} aria-label={showPassword?'Hide password':'Show password'}>{showPassword?<EyeOff size={17}/>:<Eye size={17}/>}</button></div></label>
        {error && <div className="form-error"><LockKeyhole size={16}/>{error}</div>}
        <button className="btn btn-primary w-full login-submit" type="submit" disabled={busy}>{busy?'Signing in…':'Sign in securely'}<ArrowRight size={17}/></button>
      </form><div className="login-help"><ShieldCheck size={16}/><span>Access is invitation-only. Contact your administrator if you need an account.</span></div></div><div className="login-panel-foot">© Rice Age · Internal project portal <span>Version P3</span></div></div>
  </div>;
}
function ScanLineIcon(){return <span className="inline-icon">▤</span>}
