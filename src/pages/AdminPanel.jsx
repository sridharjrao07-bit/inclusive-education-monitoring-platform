import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import { Navigate } from 'react-router-dom';
import { adminCreateUser, adminListUsers, adminToggleUserActive } from '../api';
import {
  Shield, UserPlus, Users, CheckCircle, AlertCircle,
  Eye, EyeOff, ToggleLeft, ToggleRight, Lock
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

function Toast({ message, type, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 3400);
    return () => clearTimeout(t);
  }, [onDone]);
  return (
    <div className={`toast toast-${type}`}>
      {type === 'success' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
      {message}
    </div>
  );
}

// ─── Create User Form ───────────────────────────────────
function CreateUserForm({ onCreated, showToast }) {
  const [form, setForm] = useState({
    username: '', email: '', password: '', role: 'state_admin', state: '',
  });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const created = await adminCreateUser({
        username: form.username,
        email:    form.email,
        password: form.password,
        role:     form.role,
        state:    form.role === 'state_admin' ? form.state : null,
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
          <input
            className="form-input"
            required
            value={form.username}
            onChange={e => set('username', e.target.value)}
            id="admin-new-username"
            placeholder="e.g. state_rajasthan"
          />
        </div>
        <div className="form-group">
          <label className="form-label">Email *</label>
          <input
            className="form-input"
            type="email"
            required
            value={form.email}
            onChange={e => set('email', e.target.value)}
            id="admin-new-email"
            placeholder="e.g. raj@edu.gov.in"
          />
        </div>
      </div>

      <div className="form-group" style={{ position: 'relative' }}>
        <label className="form-label">Temporary Password *</label>
        <div style={{ position: 'relative' }}>
          <input
            className="form-input"
            type={showPw ? 'text' : 'password'}
            required
            value={form.password}
            onChange={e => set('password', e.target.value)}
            id="admin-new-password"
            placeholder="Minimum 8 characters"
            style={{ paddingRight: '2.5rem' }}
          />
          <button
            type="button"
            onClick={() => setShowPw(p => !p)}
            style={{
              position: 'absolute', right: '0.75rem', top: '50%',
              transform: 'translateY(-50%)', background: 'none',
              border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 0,
            }}
          >
            {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Role *</label>
          <select
            className="form-select"
            value={form.role}
            onChange={e => set('role', e.target.value)}
            id="admin-new-role"
          >
            <option value="national_admin">National Admin</option>
            <option value="state_admin">State Admin</option>
            <option value="teacher">Teacher</option>
          </select>
        </div>
        {form.role === 'state_admin' && (
          <div className="form-group">
            <label className="form-label">State *</label>
            <input
              className="form-input"
              required
              value={form.state}
              onChange={e => set('state', e.target.value)}
              id="admin-new-state"
              placeholder="e.g. Rajasthan"
            />
          </div>
        )}
      </div>

      <button
        className="btn btn-primary"
        type="submit"
        disabled={loading || !form.username || !form.email || !form.password}
        id="admin-create-user-btn"
      >
        <UserPlus size={15} />
        {loading ? 'Creating…' : 'Create User'}
      </button>
    </form>
  );
}

// ─── Users Table ───────────────────────────────────────
function UsersTable({ users, setUsers, showToast, currentUserId }) {
  const [toggling, setToggling] = useState(null);

  const handleToggle = async (userId) => {
    setToggling(userId);
    try {
      const res = await adminToggleUserActive(userId);
      setUsers(prev =>
        prev.map(u => u.id === userId ? { ...u, is_active: res.is_active } : u)
      );
      showToast(
        `User '${res.username}' ${res.is_active ? 'activated' : 'deactivated'}.`,
        res.is_active ? 'success' : 'error'
      );
    } catch {
      showToast('Failed to toggle user status', 'error');
    } finally {
      setToggling(null);
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
    <div className="overflow-x-auto">
      <table className="data-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>State</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {users.map(u => {
            const roleStyle = ROLE_COLORS[u.role] || {};
            const isSelf = u.id === currentUserId;
            return (
              <tr key={u.id}>
                <td className="font-semibold" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: '50%',
                    background: 'linear-gradient(135deg,#1e3a8a,#2b4acb)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff', fontSize: '0.65rem', fontWeight: 700, flexShrink: 0,
                  }}>
                    {u.username.slice(0, 2).toUpperCase()}
                  </div>
                  {u.username}
                  {isSelf && <span style={{ fontSize: '0.7rem', color: '#94a3b8', marginLeft: 4 }}>(you)</span>}
                </td>
                <td style={{ color: '#64748b', fontSize: '0.85rem' }}>{u.email}</td>
                <td>
                  <span style={{
                    fontSize: '0.72rem', fontWeight: 600, padding: '2px 8px',
                    borderRadius: 20, background: roleStyle.bg, color: roleStyle.color,
                  }}>
                    {ROLE_LABELS[u.role] || u.role}
                  </span>
                </td>
                <td style={{ color: '#64748b', fontSize: '0.85rem' }}>{u.state || '—'}</td>
                <td>
                  <span className={`badge ${u.is_active ? 'badge-success' : 'badge-danger'}`}>
                    {u.is_active ? 'Active' : 'Disabled'}
                  </span>
                </td>
                <td>
                  {isSelf ? (
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>—</span>
                  ) : (
                    <button
                      className="btn btn-sm btn-secondary"
                      style={{ fontSize: '0.75rem', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}
                      onClick={() => handleToggle(u.id)}
                      disabled={toggling === u.id}
                      title={u.is_active ? 'Disable account' : 'Enable account'}
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
  );
}

// ─── Main Admin Panel ──────────────────────────────────
export default function AdminPanel() {
  const { user, isAdmin } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [tab, setTab] = useState('users');

  const showToast = (message, type) => setToast({ message, type });

  // Only national_admin can access this page
  if (!isAdmin || user?.role !== 'national_admin') {
    return <Navigate to="/" replace />;
  }

  useEffect(() => {
    adminListUsers()
      .then(setUsers)
      .catch(() => showToast('Failed to load users', 'error'))
      .finally(() => setLoading(false));
  }, []);

  const handleCreated = (newUser) => {
    setUsers(prev => [newUser, ...prev]);
    setTab('users');
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h2>Admin Panel</h2>
          <p>Manage platform users — create admins, state admins, and monitor accounts</p>
        </div>
      </div>

      {/* Access notice */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.6rem',
        padding: '0.75rem 1rem', marginBottom: '1.25rem',
        background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)',
        borderRadius: '0.75rem', fontSize: '0.8rem', color: '#dc2626'
      }}>
        <Lock size={14} style={{ flexShrink: 0 }} />
        <span>
          <strong>Restricted area.</strong> Only National Admins can access this panel.
          Changes made here are immediately applied to the live database.
        </span>
      </div>

      <div className="card">
        <div className="tab-bar">
          <button
            className={`tab-btn ${tab === 'users' ? 'active' : ''}`}
            onClick={() => setTab('users')}
            id="admin-tab-users"
          >
            <Users size={13} style={{ verticalAlign: -2, marginRight: 5 }} />
            All Users {users.length > 0 && `(${users.length})`}
          </button>
          <button
            className={`tab-btn ${tab === 'create' ? 'active' : ''}`}
            onClick={() => setTab('create')}
            id="admin-tab-create"
          >
            <UserPlus size={13} style={{ verticalAlign: -2, marginRight: 5 }} />
            Create User
          </button>
        </div>

        {tab === 'users' && (
          loading
            ? <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>Loading users…</div>
            : <UsersTable
                users={users}
                setUsers={setUsers}
                showToast={showToast}
                currentUserId={user?.id}
              />
        )}

        {tab === 'create' && (
          <CreateUserForm onCreated={handleCreated} showToast={showToast} />
        )}
      </div>

      {toast && <Toast {...toast} onDone={() => setToast(null)} />}
    </div>
  );
}
