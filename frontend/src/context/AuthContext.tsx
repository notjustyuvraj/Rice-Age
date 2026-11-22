import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api, getToken, setToken } from '../lib/api';
import type { User } from '../lib/types';

interface AuthValue { user: User | null; loading: boolean; login: (email: string, password: string) => Promise<void>; logout: () => void; }
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    const restore = async () => {
      if (!getToken()) { if (active) setLoading(false); return; }
      try { const me = await api.me(); if (active) setUser(me); }
      catch { setToken(null); if (active) setUser(null); }
      finally { if (active) setLoading(false); }
    };
    const onUnauthorized = () => setUser(null);
    window.addEventListener('rice-age:unauthorized', onUnauthorized);
    void restore();
    return () => { active = false; window.removeEventListener('rice-age:unauthorized', onUnauthorized); };
  }, []);
  const value = useMemo<AuthValue>(() => ({
    user, loading,
    login: async (email, password) => {
      const result = await api.login(email, password);
      setToken(result.access_token);
      const me = await api.me();
      setUser(me);
    },
    logout: () => { setToken(null); setUser(null); },
  }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('useAuth must be used within AuthProvider'); return value; }
