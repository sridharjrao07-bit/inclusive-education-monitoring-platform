import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import { Navigate } from 'react-router-dom';
import { stateAdminCreateTeacher, stateAdminListUsers, stateAdminToggleUserActive, fetchSchools } from '../api';
import {
  MapPin, UserPlus, Users, CheckCircle, AlertCircle,
  Eye, EyeOff, ToggleLeft, ToggleRight, Lock, Search
} from 'lucide-react';

const ROLE_LABELS = { teacher: 'Teacher', state_admin: 'State Admin', national_admin: 'National Admin' };
const ROLE_COLORS = {
  teacher:        { bg: 'rgba(59,130,246,0.08)',  color: '#2563eb' },
  state_admin:    { bg: 'rgba(249,115,22,0.08)',  color: '#ea580c' },
  national_admin: { bg: 'rgba(239,68,68,0.08)',   color: '#dc2626' },
};

function Toast({ message, type, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3400); return () => clearTimeout(t); }, [onDone]);
  return (
    <div className={`toast toast-${type}`}>
      {type === 'success' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
      {message}
    </div>
  );
}

// ─── Create Teacher Form ────────────────────────────────
function CreateTeacherForm({ onCreated, showToast, currentState }) {
  const [form, setForm] = useState({ username: '', email: '', password: '', school_code: '' });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifiedSchool, setVerifiedSchool] = useState(null);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const verifyCode = async () => {
    if (!form.school_code || form.school_code.length < 4) return;
    setVerifying(true);
    setVerifiedSchool(null);
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || ''}/auth/verify-code/${form.school_code.toUpperCase()}`
      );
      if (!res.ok) throw new Error('Invalid code');
      const data = await res.json();
      if (data.state !== currentState) {
        showToast(`This school is in ${data.state}, not ${currentState}`, 'error');
        setVerifiedSchool(null);
      } else {
        setVerifiedSchool(data);
      }
    } catch {
      showToast('Invalid school code', 'error');
    } finally {
      setVerifying(false);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const created = await stateAdminCreateTeacher({
        username: form.username,
        email: form.email,
        password: form.password,
        school_code: form.school_code || null,
      });
      showToast(`Teacher '${created.username}' created successfully!`, 'success');
      setForm({ username: '', email: '', password: '', school_code: '' });
      setVerifiedSchool(null);
      onCreated(created);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create teacher', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit}>
      {/* State badge */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '4px 12px', borderRadius: 20, marginBottom: 16,
        background: 'rgba(249,115,22,0.08)', border: '1px solid rgba(249,115,22,0.2)',
        fontSize: '0.78rem', color: '#ea580c', fontWeight: 600,
      }}>
        <MapPin size={12} /> Creating teachers for: {currentState}
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Username *</label>
          <input className="form-input" required value={form.username}
            onChange={e => set('username', e.target.value)} id="sa-username"
            placeholder="e.g. teacher_jaipur" />
        </div>
        <div className="form-group">
          <label className="form-label">Email *</label>
          <input className="form-input" type="email" required value={form.email}
            onChange={e => set('email', e.target.value)} id="sa-email"
            placeholder="e.g. teacher@school.in" />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Temporary Password *</label>
        <div style={{ position: 'relative' }}>
          <input className="form-input" type={showPw ? 'text' : 'password'} required
            value={form.password} onChange={e => set('password', e.target.value)}
            id="sa-password" placeholder="Minimum 8 characters"
            style={{ paddingRight: '2.5rem' }} />
          <button type="button" onClick={() => setShowPw(p => !p)} style={{
            position: 'absolute', right: '0.75rem', top: '50%',
            transform: 'translateY(-50%)', background: 'none', border: 'none',
            cursor: 'pointer', color: '#94a3b8', padding: 0,
          }}>
            {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
      </div>

      {/* Optional school code */}
      <div className="form-group">
        <label className="form-label">School Registration Code <span style={{ fontWeight: 400, color: '#94a3b8' }}>(optional — links teacher to a school)</span></label>
        <div style={{ display: 'flex', gap: 8 }}>
          <input className="form-input flex-1" type="text"
            placeholder="e.g. A1B2C3D4" value={form.school_code}
            onChange={e => { set('school_code', e.target.value.toUpperCase()); setVerifiedSchool(null); }}
            maxLength={8} id="sa-school-code" />
          <button type="button" className="btn btn-primary"
            style={{ minWidth: 'auto', padding: '0 1rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 4 }}
            onClick={verifyCode} disabled={verifying || form.school_code.length < 4}>
            {verifying ? <span className="spinner" style={{ width: 14, height: 14 }} /> : <Search size={13} />}
            Verify
          </button>
        </div>
        {verifiedSchool && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 6, marginTop: 8,
            padding: '6px 12px', borderRadius: 8, background: 'rgba(16,185,129,0.07)',
            border: '1px solid rgba(16,185,129,0.2)', color: '#059669', fontSize: '0.8rem'
          }}>
            <CheckCircle size={13} />
            <span><strong>{verifiedSchool.school_name}</strong> — {verifiedSchool.district}, {verifiedSchool.state}</span>
          </div>
        )}
        <p className="text-[11px] text-slate-400 mt-1.5">
          The school must be registered in {currentState}. Leave blank to create the teacher without a school assignment.
        </p>
      </div>

      <button className="btn btn-primary" type="submit" id="sa-create-btn"
        disabled={loading || !form.username || !form.email || !form.password}>
        <UserPlus size={14} />
        {loading ? 'Creating…' : 'Create Teacher Account'}
      </button>
    </form>
  );
}

// ─── Users Table ────────────────────────────────────────
function UsersTable({ users, setUsers, showToast, currentUserId }) {
  const [toggling, setToggling] = useState(null);
  const [search, setSearch] = useState('');

  const filtered = users.filter(u =>
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  const handleToggle = async (userId) => {
    setToggling(userId);
    try {
      const res = await stateAdminToggleUserActive(userId);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: res.is_active } : u));
      showToast(
        `User '${res.username}' ${res.is_active ? 'activated' : 'deactivated'}.`,
        res.is_active ? 'success' : 'error'
      );
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to toggle user status', 'error');
    } finally {
      setToggling(null);
    }
  };

  return (
    <>
      {/* Search */}
      <div style={{ padding: '1rem 1rem 0', marginBottom: '0.75rem' }}>
        <div style={{ position: 'relative', maxWidth: 320 }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
          <input className="form-input" placeholder="Search users…" value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ paddingLeft: '2rem', fontSize: '0.83rem' }} />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state" style={{ padding: '2rem' }}>
          <Users size={28} style={{ opacity: 0.3, marginBottom: 8 }} />
          <p>{search ? 'No matching users.' : 'No users in your state yet.'}</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>School ID</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(u => {
                const roleStyle = ROLE_COLORS[u.role] || {};
                const isSelf = u.id === currentUserId;
                const isAdmin = u.role === 'national_admin' || u.role === 'state_admin';
                return (
                  <tr key={u.id}>
                    <td className="font-semibold" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: '50%',
                        background: isAdmin
                          ? 'linear-gradient(135deg,#ea580c,#f97316)'
                          : 'linear-gradient(135deg,#1e3a8a,#2b4acb)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#fff', fontSize: '0.65rem', fontWeight: 700, flexShrink: 0,
                      }}>
                        {u.username.slice(0, 2).toUpperCase()}
                      </div>
                      {u.username}
                      {isSelf && <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>(you)</span>}
                    </td>
                    <td style={{ color: '#64748b', fontSize: '0.83rem' }}>{u.email}</td>
                    <td>
                      <span style={{
                        fontSize: '0.72rem', fontWeight: 600, padding: '2px 8px',
                        borderRadius: 20, background: roleStyle.bg, color: roleStyle.color,
                      }}>
                        {ROLE_LABELS[u.role] || u.role}
                      </span>
                    </td>
                    <td style={{ color: '#64748b', fontSize: '0.83rem' }}>
                      {u.school_id ? `#${u.school_id}` : '—'}
                    </td>
                    <td>
                      <span className={`badge ${u.is_active ? 'badge-success' : 'badge-danger'}`}>
                        {u.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td>
                      {isSelf || isAdmin ? (
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>—</span>
                      ) : (
                        <button
                          className="btn btn-sm btn-secondary"
                          style={{ fontSize: '0.75rem', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}
                          onClick={() => handleToggle(u.id)}
                          disabled={toggling === u.id}
                        >
                          {toggling === u.id
                            ? <span className="spinner" style={{ width: 12, height: 12 }} />
                            : u.is_active
                              ? <><ToggleRight size={13} /> Disable</>
                              : <><ToggleLeft size={13} /> Enable</>
                          }
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

// ─── Main State Admin Panel ─────────────────────────────
export default function StateAdminPanel() {
  const { user, isStateAdmin } = useAuth();
  const [users, setUsers]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast]     = useState(null);
  const [tab, setTab]         = useState('users');

  const showToast = (message, type) => setToast({ message, type });

  // Only state_admin (or national_admin) can access
  if (!isStateAdmin && user?.role !== 'national_admin') {
    return <Navigate to="/" replace />;
  }

  useEffect(() => {
    stateAdminListUsers()
      .then(setUsers)
      .catch(() => showToast('Failed to load users', 'error'))
      .finally(() => setLoading(false));
  }, []);

  const handleCreated = (newUser) => {
    setUsers(prev => [newUser, ...prev]);
    setTab('users');
  };

  const teacherCount  = users.filter(u => u.role === 'teacher').length;
  const activeCount   = users.filter(u => u.is_active).length;
  const disabledCount = users.filter(u => !u.is_active).length;

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h2>State Admin Panel</h2>
          <p>Manage teachers and users in <strong>{user?.state}</strong></p>
        </div>
      </div>

      {/* Access notice */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.6rem',
        padding: '0.75rem 1rem', marginBottom: '1.25rem',
        background: 'rgba(249,115,22,0.06)', border: '1px solid rgba(249,115,22,0.2)',
        borderRadius: '0.75rem', fontSize: '0.8rem', color: '#c2410c'
      }}>
        <Lock size={14} style={{ flexShrink: 0 }} />
        <span>
          <strong>State-scoped access.</strong> You can only view and manage users associated with schools in <strong>{user?.state}</strong>. You cannot create or manage admin-level accounts.
        </span>
      </div>

      {/* Summary KPIs */}
      {!loading && (
        <div className="kpi-grid" style={{ marginBottom: '1.25rem' }}>
          {[
            { label: 'Total Users', value: users.length, color: '#2b4acb', bg: 'rgba(43,74,203,0.08)' },
            { label: 'Teachers',    value: teacherCount,  color: '#138808', bg: 'rgba(19,136,8,0.08)' },
            { label: 'Active',      value: activeCount,   color: '#10b981', bg: 'rgba(16,185,129,0.08)' },
            { label: 'Disabled',    value: disabledCount, color: '#ef4444', bg: 'rgba(239,68,68,0.08)' },
          ].map(k => (
            <div key={k.label} className="kpi-card" style={{ '--kpi-color': k.color, '--kpi-bg': k.bg }}>
              <div className="kpi-content">
                <div className="kpi-label">{k.label}</div>
                <div className="kpi-value">{k.value}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <div className="tab-bar">
          <button className={`tab-btn ${tab === 'users' ? 'active' : ''}`}
            onClick={() => setTab('users')} id="sa-tab-users">
            <Users size={13} style={{ verticalAlign: -2, marginRight: 5 }} />
            Users in {user?.state} {users.length > 0 && `(${users.length})`}
          </button>
          <button className={`tab-btn ${tab === 'create' ? 'active' : ''}`}
            onClick={() => setTab('create')} id="sa-tab-create">
            <UserPlus size={13} style={{ verticalAlign: -2, marginRight: 5 }} />
            Add Teacher
          </button>
        </div>

        {tab === 'users' && (
          loading
            ? <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>Loading users…</div>
            : <UsersTable users={users} setUsers={setUsers} showToast={showToast} currentUserId={user?.id} />
        )}

        {tab === 'create' && (
          <CreateTeacherForm
            onCreated={handleCreated}
            showToast={showToast}
            currentState={user?.state}
          />
        )}
      </div>

      {toast && <Toast {...toast} onDone={() => setToast(null)} />}
    </div>
  );
}
