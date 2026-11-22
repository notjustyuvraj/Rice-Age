import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import AppLayout from './components/AppLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ScansPage from './pages/ScansPage';
import ScanDetailPage from './pages/ScanDetailPage';

function ProtectedLayout() {
  const { user, loading } = useAuth();
  if (loading) return <div className="app-loading"><div className="loading-orb"/><span>Loading Rice Age…</span></div>;
  if (!user) return <Navigate to="/login" replace/>;
  return <AppLayout/>;
}
function LoginRoute() { const { user, loading } = useAuth(); if (loading) return null; return user ? <Navigate to="/dashboard" replace/> : <LoginPage/>; }
function AppRoutes() {
  return <Routes>
    <Route path="/login" element={<LoginRoute/>}/>
    <Route element={<ProtectedLayout/>}>
      <Route path="/" element={<Navigate to="/dashboard" replace/>}/>
      <Route path="/dashboard" element={<DashboardPage/>}/>
      <Route path="/scans" element={<ScansPage/>}/>
      <Route path="/scans/:id" element={<ScanDetailPage/>}/>
    </Route>
    <Route path="*" element={<Navigate to="/dashboard" replace/>}/>
  </Routes>;
}
export default function App() { return <AuthProvider><AppRoutes/></AuthProvider>; }
