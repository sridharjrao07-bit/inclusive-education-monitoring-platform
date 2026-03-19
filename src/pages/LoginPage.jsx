import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { GraduationCap, Eye, EyeOff, LogIn, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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

        {/* Demo credentials */}
        <div className="mt-6 pt-5 border-t border-slate-100">
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
