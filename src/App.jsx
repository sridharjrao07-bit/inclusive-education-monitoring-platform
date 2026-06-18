import { BrowserRouter as Router, Routes, Route, NavLink, useLocation, Navigate } from 'react-router-dom';
import { useState, useEffect, Suspense, lazy } from 'react';
import {
  LayoutDashboard, School, Users, ClipboardList,
  Bot, GraduationCap, ChevronRight, LogOut, Upload, ShieldCheck, MapPin
} from 'lucide-react';
import { AuthProvider, useAuth } from './AuthContext';
import { seedAdmin } from './api';
import NotificationBell from './components/NotificationBell';

// Lazy-loaded pages — each becomes its own JS chunk
const Dashboard        = lazy(() => import('./pages/Dashboard'));
const SchoolsPage      = lazy(() => import('./pages/SchoolsPage'));
const DataEntry        = lazy(() => import('./pages/DataEntry'));
const AIAssistant      = lazy(() => import('./pages/AIAssistant'));
const AttendancePage   = lazy(() => import('./pages/AttendancePage'));
const LoginPage        = lazy(() => import('./pages/LoginPage'));
const RegisterPage     = lazy(() => import('./pages/RegisterPage'));
const AdminPanel       = lazy(() => import('./pages/AdminPanel'));
const StateAdminPanel  = lazy(() => import('./pages/StateAdminPanel'));

function PageLoader() {
  return (
    <div className="page-loader" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', fontSize: '1rem', color: 'var(--text-muted, #888)' }}>
      Loading…
    </div>
  );
}

/* ProtectedRoute — redirects to /login if not authenticated */
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="page-loader">Loading…</div>;
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

/* Role labels for display */
const ROLE_LABELS = {
  national_admin: 'National Admin',
  state_admin: 'State Admin',
  teacher: 'Teacher',
  admin: 'Admin',
};

function AppContent() {
  const location = useLocation();
  const { user, isAuthenticated, isAdmin, isTeacher, isStateAdmin, logout } = useAuth();

  // Seed admin users on first load (idempotent)
  useEffect(() => {
    seedAdmin().catch(() => {});
  }, []);

  const pageMap = {
    '/': { title: 'Dashboard', desc: 'National overview' },
    '/schools': { title: 'Schools', desc: 'Browse & manage' },
    '/data-entry': { title: 'Data Entry', desc: 'Add records' },
    '/ai': { title: 'AI Assistant', desc: 'Ask questions' },
    '/attendance': { title: 'Attendance', desc: 'Student attendance analytics' },
  };

  const current = pageMap[location.pathname] || pageMap['/'];

  // If on login or register page, render only that page (no sidebar)
  if (location.pathname === '/login' || location.pathname === '/register') {
    return (
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </Suspense>
    );
  }

  return (
    <div className="app-layout">
      {/* ── SIDEBAR ── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <GraduationCap size={20} />
          </div>
          <div>
            <h1>Samagra Shiksha</h1>
            <span>Inclusive Monitoring</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <span className="nav-label">Navigation</span>

          <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
            <LayoutDashboard /> Dashboard
          </NavLink>
          <NavLink to="/schools" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <School /> Schools
          </NavLink>

          {/* Data Entry: visible to admins and teachers */}
          {(isAdmin || isStateAdmin || isTeacher) && (
            <NavLink to="/data-entry" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <ClipboardList /> Data Entry
            </NavLink>
          )}

          <span className="nav-label">AI & Insights</span>

          <NavLink to="/ai" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <Bot /> AI Assistant
          </NavLink>

          {/* Admin Panel: national_admin only */}
          {user?.role === 'national_admin' && (
            <>
              <span className="nav-label">Administration</span>
              <NavLink to="/admin-panel" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <ShieldCheck /> Admin Panel
              </NavLink>
            </>
          )}

          {/* State Admin Panel: state_admin only */}
          {user?.role === 'state_admin' && (
            <>
              <span className="nav-label">Administration</span>
              <NavLink to="/state-admin-panel" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <MapPin /> State Panel
              </NavLink>
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          {isAuthenticated && user ? (
            <div className="sidebar-footer-role">
              <div className="sidebar-footer-avatar">
                {user.username.slice(0, 2).toUpperCase()}
              </div>
              <div className="sidebar-footer-info">
                <p>{user.username}</p>
                <span>{ROLE_LABELS[user.role] || user.role}</span>
                {user.state && <span className="state-badge">{user.state}</span>}
              </div>
              <button className="logout-btn" onClick={logout} title="Logout">
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <div className="sidebar-footer-role">
              <div className="sidebar-footer-avatar">?</div>
              <div className="sidebar-footer-info">
                <p>Not logged in</p>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* ── HEADER ── */}
      <header className="header">
        <div className="header-left">
          <div>
            <div className="header-breadcrumb">
              Home <ChevronRight size={12} /> <span>{current.title}</span>
            </div>
            <h2>{current.title}</h2>
          </div>
        </div>
        <div className="header-right" style={{ display: 'flex', alignItems: 'center' }}>
          {isAuthenticated && (
            <>
              <NotificationBell />
              <div className="header-badge">
                {ROLE_LABELS[user?.role] || 'Authenticated'}
                {user?.state ? ` · ${user.state}` : ''}
              </div>
            </>
          )}
        </div>
      </header>

      {/* ── MAIN ── */}
      <main className="main-content">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/schools" element={<ProtectedRoute><SchoolsPage /></ProtectedRoute>} />
            <Route path="/data-entry" element={<ProtectedRoute><DataEntry /></ProtectedRoute>} />
            <Route path="/ai" element={<ProtectedRoute><AIAssistant /></ProtectedRoute>} />
            <Route path="/attendance" element={<ProtectedRoute><AttendancePage /></ProtectedRoute>} />
            <Route path="/admin-panel" element={<ProtectedRoute><AdminPanel /></ProtectedRoute>} />
            <Route path="/state-admin-panel" element={<ProtectedRoute><StateAdminPanel /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}
