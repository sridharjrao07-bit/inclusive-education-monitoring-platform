import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import { Navigate } from 'react-router-dom';
import { adminCreateUser, adminListUsers, adminToggleUserActive, adminDeleteUser } from '../api';
import {
  Shield, UserPlus, Users, CheckCircle, AlertCircle,
  Eye, EyeOff, ToggleLeft, ToggleRight, Lock, Trash2, AlertTriangle, X
} from 'lucide-react';

const ROLE_LABELS = {
  national_admin: 'National Admin',
  state_admin:    'State Admin',
  teacher:        'Teacher',
};

const ROLE_COLORS = {
  national_admin: { bg: 'rgba(239,68,68,0.08)',   color: '#dc2626' },
  state_admin:    { bg: 'rgba(249,115,22,0.08)',   color: '#ea580c' },
  teacher:        { bg: 'rgba(59,130,246,0.08)',   color: '#2563eb' },
};

// ─── Toast ──────────────────────────────────────────────
function Toast({ message, type, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3400); return () => clearTimeout(t); }, [onDone]);
  return (
    <div className={`toast toast-${type}`}>
      {type === 'success' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
      {message}
    </div>
  );
}

// ─── Confirmation Modal ─────────────────────────────────
function ConfirmModal({ title, message, confirmLabel, confirmStyle, onConfirm, onCancel, loading }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9999, backdropFilter: 'blur(3px)',
    }}>
      <div style={{
        background: '#fff', borderRadius: '1rem', padding: '2rem',
        maxWidth: 420, width: '90%', boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
        animation: 'fadeIn 0.15s ease',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <div style={{
            width: 40, height: 40, borderRadius: '50%', flexShrink: 0,
            background: confirmStyle === 'danger' ? 'rgba(239,68,68,0.1)' : 'rgba(249,115,22,0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <AlertTriangle size={20} color={confirmStyle === 'danger' ? '#dc2626' : '#ea580c'} />
          </div>
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#1e293b' }}>{title}</h3>
        </div>
        <p style={{ margin: '0 0 1.5rem', fontSize: '0.875rem', color: '#64748b', lineHeight: 1.6 }}>
          {message}
        </p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={onCancel} disabled={loading}
            style={{ fontSize: '0.85rem' }}>
            <X size={14} /> Cancel
          </button>
          <button
            className="btn"
            onClick={onConfirm}
            disabled={loading}
            style={{
              fontSize: '0.85rem',
              background: confirmStyle === 'danger' ? '#dc2626' : '#ea580c',
              color: '#fff', border: 'none',
              display: 'flex', alignItems: 'center', gap: 6,
            }}
          >
            {loading
              ? <span className="spinner" style={{ width: 14, height: 14 }} />
              : confirmStyle === 'danger' ? <Trash2 size={14} /> : <ToggleLeft size={14} />
            }
            {loading ? 'Working…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Create User Form ───────────────────────────────────
function CreateUserForm({ onCreated, showToast }) {
  const [form, setForm] = useState({ username: '', email: '', password: '', role: 'state_admin', state: '' });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const created = await adminCreateUser({
        username: form.username, email: form.email, password: form.password,
        role: form.role, state: form.role === 'state_admin' ? form.state : null,
      });
      showToast(`User '${created.username}' created successfully!`, 'success');
      setForm({ username: '', email: '', password: '', role: 'state_admin', state: '' });
      onCreated(created);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create user', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Username *</label>
          <input className="form-input" required value={form.username}
            onChange={e => set('username', e.target.value)} id="admin-new-username" placeholder="e.g. state_rajasthan" />
        </div>
        <div className="form-group">
          <label className="form-label">Email *</label>
          <input className="form-input" type="email" required value={form.email}
            onChange={e => set('email', e.target.value)} id="admin-new-email" placeholder="e.g. raj@edu.gov.in" />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Temporary Password *</label>
        <div style={{ position: 'relative' }}>
          <input className="form-input" type={showPw ? 'text' : 'password'} required
            value={form.password} onChange={e => set('password', e.target.value)}
            id="admin-new-password" placeholder="Minimum 8 characters" style={{ paddingRight: '2.5rem' }} />
          <button type="button" onClick={() => setShowPw(p => !p)} style={{
            position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)',
            background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 0,
          }}>
            {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Role *</label>
          <select className="form-select" value={form.role} onChange={e => set('role', e.target.value)} id="admin-new-role">
            <option value="national_admin">National Admin</option>
            <option value="state_admin">State Admin</option>
            <option value="teacher">Teacher</option>
          </select>
        </div>
        {form.role === 'state_admin' && (
          <div className="form-group">
            <label className="form-label">State *</label>
            <input className="form-input" required value={form.state}
              onChange={e => set('state', e.target.value)} id="admin-new-state" placeholder="e.g. Rajasthan" />
          </div>
        )}
      </div>

      <button className="btn btn-primary" type="submit" id="admin-create-user-btn"
        disabled={loading || !form.username || !form.email || !form.password}>
        <UserPlus size={15} />
        {loading ? 'Creating…' : 'Create User'}
      </button>
    </form>
  );
}

// ─── Users Table ───────────────────────────────────────
function UsersTable({ users, setUsers, showToast, currentUserId }) {
  const [actionLoading, setActionLoading] = useState(null);
  const [confirm, setConfirm] = useState(null); // { type: 'disable'|'delete', user }

  const handleToggle = async () => {
    const u = confirm.user;
    setActionLoading(u.id);
    try {
      const res = await adminToggleUserActive(u.id);
      setUsers(prev => prev.map(x => x.id === u.id ? { ...x, is_active: res.is_active } : x));
      showToast(`'${res.username}' ${res.is_active ? 'enabled' : 'disabled'}.`, res.is_active ? 'success' : 'error');
    } catch {
      showToast('Failed to update user status', 'error');
    } finally {
      setActionLoading(null);
      setConfirm(null);
    }
  };

  const handleDelete = async () => {
    const u = confirm.user;
    setActionLoading(u.id);
    try {
      await adminDeleteUser(u.id);
      setUsers(prev => prev.filter(x => x.id !== u.id));
      showToast(`User '${u.username}' permanently deleted.`, 'error');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to delete user', 'error');
    } finally {
      setActionLoading(null);
      setConfirm(null);
    }
  };

  if (!users.length) {
    return (
      <div className="empty-state" style={{ padding: '2rem' }}>
        <Shield size={28} style={{ opacity: 0.3, marginBottom: 8 }} />
        <p>No users found.</p>
      </div>
    );
  }

  return (
    <>
      {confirm && (
        <ConfirmModal
          title={confirm.type === 'delete' ? 'Delete User Permanently' : (confirm.user.is_active ? 'Disable Access' : 'Enable Access')}
          message={
            confirm.type === 'delete'
              ? `This will permanently delete '${confirm.user.username}' (${ROLE_LABELS[confirm.user.role]}). This action cannot be undone.`
              : confirm.user.is_active
                ? `'${confirm.user.username}' will be locked out immediately. Their data is preserved and you can re-enable them later.`
                : `'${confirm.user.username}' will regain access to the platform.`
          }
          confirmLabel={confirm.type === 'delete' ? 'Delete Permanently' : (confirm.user.is_active ? 'Disable Access' : 'Enable Access')}
          confirmStyle={confirm.type === 'delete' || confirm.user.is_active ? 'danger' : 'warning'}
          onConfirm={confirm.type === 'delete' ? handleDelete : handleToggle}
          onCancel={() => setConfirm(null)}
          loading={actionLoading === confirm.user.id}
        />
      )}

      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>State</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => {
              const roleStyle = ROLE_COLORS[u.role] || {};
              const isSelf = u.id === currentUserId;
              return (
                <tr key={u.id}>
                  <td style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{
                      width: 30, height: 30, borderRadius: '50%', flexShrink: 0,
                      background: 'linear-gradient(135deg,#1e3a8a,#2b4acb)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: '#fff', fontSize: '0.65rem', fontWeight: 700,
                    }}>
                      {u.username.slice(0, 2).toUpperCase()}
                    </div>
                    <span className="font-semibold" style={{ fontSize: '0.875rem' }}>
                      {u.username}
                      {isSelf && <span style={{ fontSize: '0.7rem', color: '#94a3b8', marginLeft: 4 }}>(you)</span>}
                    </span>
                  </td>
                  <td style={{ color: '#64748b', fontSize: '0.83rem' }}>{u.email}</td>
                  <td>
                    <span style={{
                      fontSize: '0.72rem', fontWeight: 600, padding: '2px 9px',
                      borderRadius: 20, background: roleStyle.bg, color: roleStyle.color,
                    }}>
                      {ROLE_LABELS[u.role] || u.role}
                    </span>
                  </td>
                  <td style={{ color: '#64748b', fontSize: '0.83rem' }}>{u.state || '—'}</td>
                  <td>
                    <span className={`badge ${u.is_active ? 'badge-success' : 'badge-danger'}`}>
                      {u.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td>
                    {isSelf ? (
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>—</span>
                    ) : (
                      <div style={{ display: 'flex', gap: 6 }}>
                        {/* Enable / Disable */}
                        <button
                          className="btn btn-sm btn-secondary"
                          style={{ fontSize: '0.73rem', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}
                          onClick={() => setConfirm({ type: 'toggle', user: u })}
                          title={u.is_active ? 'Disable access' : 'Enable access'}
                        >
                          {u.is_active
                            ? <><ToggleRight size={13} /> Disable</>
                            : <><ToggleLeft size={13} /> Enable</>
                          }
                        </button>
                        {/* Delete */}
                        <button
                          className="btn btn-sm"
                          style={{
                            fontSize: '0.73rem', padding: '4px 10px',
                            background: 'rgba(239,68,68,0.08)', color: '#dc2626',
                            border: '1px solid rgba(239,68,68,0.2)',
                            display: 'flex', alignItems: 'center', gap: 4,
                          }}
                          onClick={() => setConfirm({ type: 'delete', user: u })}
                          title="Permanently delete user"
                        >
                          <Trash2 size={12} /> Delete
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ─── Main Admin Panel ──────────────────────────────────
export default function AdminPanel() {
  const { user, isAdmin } = useAuth();
  const [users, setUsers]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast]   = useState(null);
  const [tab, setTab]       = useState('users');

  const showToast = (message, type) => setToast({ message, type });

  if (!isAdmin || user?.role !== 'national_admin') return <Navigate to="/" replace />;

  useEffect(() => {
    adminListUsers()
      .then(setUsers)
      .catch(() => showToast('Failed to load users', 'error'))
      .finally(() => setLoading(false));
  }, []);

  const activeCount   = users.filter(u => u.is_active).length;
  const disabledCount = users.filter(u => !u.is_active).length;

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h2>Admin Panel</h2>
          <p>Manage platform users — create, disable, or permanently remove accounts</p>
        </div>
      </div>

      {/* Access notice */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.6rem',
        padding: '0.75rem 1rem', marginBottom: '1.25rem',
        background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)',
        borderRadius: '0.75rem', fontSize: '0.8rem', color: '#dc2626',
      }}>
        <Lock size={14} style={{ flexShrink: 0 }} />
        <span>
          <strong>Restricted area.</strong> Only National Admins can access this panel. All changes are permanent and applied to the live database.
        </span>
      </div>

      {/* KPI summary */}
      {!loading && (
        <div className="kpi-grid" style={{ marginBottom: '1.25rem' }}>
          {[
            { label: 'Total Users',    value: users.length,  color: '#2b4acb', bg: 'rgba(43,74,203,0.08)'  },
            { label: 'Active',         value: activeCount,   color: '#10b981', bg: 'rgba(16,185,129,0.08)' },
            { label: 'Disabled',       value: disabledCount, color: '#ef4444', bg: 'rgba(239,68,68,0.08)'  },
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
            onClick={() => setTab('users')} id="admin-tab-users">
            <Users size={13} style={{ verticalAlign: -2, marginRight: 5 }} />
            All Users {users.length > 0 && `(${users.length})`}
          </button>
          <button className={`tab-btn ${tab === 'create' ? 'active' : ''}`}
            onClick={() => setTab('create')} id="admin-tab-create">
            <UserPlus size={13} style={{ verticalAlign: -2, marginRight: 5 }} />
            Create User
          </button>
        </div>

        {tab === 'users' && (
          loading
            ? <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>Loading users…</div>
            : <UsersTable users={users} setUsers={setUsers} showToast={showToast} currentUserId={user?.id} />
        )}

        {tab === 'create' && (
          <CreateUserForm onCreated={u => { setUsers(prev => [u, ...prev]); setTab('users'); }} showToast={showToast} />
        )}
      </div>

      {toast && <Toast {...toast} onDone={() => setToast(null)} />}
    </div>
  );
}
