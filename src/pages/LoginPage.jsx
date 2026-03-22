import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { GraduationCap, Eye, EyeOff, LogIn, AlertCircle, KeyRound, School, Search } from 'lucide-react';
import axios from 'axios';

const backendURL = import.meta.env.VITE_API_URL || '';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // School code lookup
  const [showCodeLookup, setShowCodeLookup] = useState(false);
  const [lookupCode, setLookupCode] = useState('');
  const [lookupResult, setLookupResult] = useState(null);
  const [lookupLoading, setLookupLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCodeLookup = async () => {
    if (!lookupCode || lookupCode.length < 4) return;
    setLookupLoading(true);
    setLookupResult(null);
    try {
      const authBase = backendURL ? `${backendURL}/auth` : '/auth';
      const res = await axios.get(`${authBase}/verify-code/${lookupCode}`);
      setLookupResult({ valid: true, ...res.data });
    } catch {
      setLookupResult({ valid: false });
    } finally {
      setLookupLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center text-white"
               style={{ background: 'linear-gradient(135deg, #1e3a8a, #2b4acb)' }}>
            <GraduationCap size={28} />
          </div>
          <h1 className="text-xl font-bold text-slate-800">Samagra Shiksha</h1>
          <p className="text-sm text-slate-500 mt-1">Inclusive Education Monitoring Platform</p>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="flex items-center gap-2 px-4 py-3 mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="username">Username</label>
            <input
              id="username"
              className="form-input"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <div className="relative">
              <input
                id="password"
                className="form-input pr-10"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 bg-transparent border-none cursor-pointer"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full mt-2 py-3"
            disabled={loading || !username || !password}
          >
            {loading ? (
              <span className="spinner" />
            ) : (
              <>
                <LogIn size={18} />
                Sign In
              </>
            )}
          </button>
        </form>

        {/* School Code Lookup */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <button
            type="button"
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-[13px] font-medium transition cursor-pointer border"
            style={{
              background: showCodeLookup ? '#f0f4ff' : '#f8fafc',
              borderColor: showCodeLookup ? '#c7d2fe' : '#e2e8f0',
              color: showCodeLookup ? '#4338ca' : '#475569',
            }}
            onClick={() => setShowCodeLookup(!showCodeLookup)}
          >
            <KeyRound size={15} />
            {showCodeLookup ? 'Hide School Code Lookup' : 'Have a School Code? Look Up Your School'}
          </button>

          {showCodeLookup && (
            <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
              <p className="text-[12px] text-slate-500 mb-3 leading-relaxed">
                Enter your school's unique registration code to see which school it belongs to. 
                If you don't have an account yet, <Link to="/register" className="text-india-500 font-medium no-underline">register here</Link>.
              </p>
              <div className="flex gap-2">
                <input
                  className="form-input flex-1"
                  type="text"
                  placeholder="e.g. A1B2C3D4"
                  value={lookupCode}
                  onChange={e => { setLookupCode(e.target.value.toUpperCase()); setLookupResult(null); }}
                  maxLength={8}
                />
                <button
                  type="button"
                  className="btn btn-primary px-4 py-2 text-[13px] flex items-center gap-1.5 whitespace-nowrap"
                  style={{ minWidth: 'auto' }}
                  onClick={handleCodeLookup}
                  disabled={lookupLoading || lookupCode.length < 4}
                >
                  {lookupLoading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : <Search size={15} />}
                  Verify
                </button>
              </div>
              {lookupResult && lookupResult.valid && (
                <div className="flex items-center gap-2 mt-3 px-3 py-2.5 rounded-lg bg-green-50 border border-green-200 text-green-700 text-[13px]">
                  <School size={16} className="shrink-0" />
                  <span><strong>{lookupResult.school_name}</strong> — {lookupResult.district}, {lookupResult.state}</span>
                </div>
              )}
              {lookupResult && !lookupResult.valid && (
                <div className="flex items-center gap-2 mt-3 px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-red-600 text-[13px]">
                  <AlertCircle size={16} className="shrink-0" />
                  <span>Invalid code. Please check and try again.</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Demo credentials */}
        <div className="mt-5 pt-5 border-t border-slate-100">
          <p className="text-xs font-semibold text-slate-500 mb-2 text-center">Demo Credentials</p>
          <div className="flex flex-wrap gap-2 justify-center">
            <button className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-medium text-slate-600 hover:bg-india-50 hover:text-india-600 transition cursor-pointer"
              onClick={() => { setUsername('admin'); setPassword('admin123'); }}>
              🔑 National Admin
            </button>
            <button className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-medium text-slate-600 hover:bg-india-50 hover:text-india-600 transition cursor-pointer"
              onClick={() => { setUsername('state_mp'); setPassword('state123'); }}>
              🏛️ State Admin
            </button>
            <button className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-medium text-slate-600 hover:bg-india-50 hover:text-india-600 transition cursor-pointer"
              onClick={() => { setUsername('teacher1'); setPassword('teacher123'); }}>
              👩‍🏫 Teacher
            </button>
          </div>
        </div>

        <div className="mt-5 text-center text-sm text-slate-500">
          Don't have an account?{' '}
          <Link to="/register" className="text-india-500 font-medium hover:text-india-600 no-underline">
            Register here
          </Link>
        </div>
      </div>
    </div>
  );
}
