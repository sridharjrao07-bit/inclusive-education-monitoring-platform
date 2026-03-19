import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { GraduationCap, Eye, EyeOff, UserPlus, AlertCircle, CheckCircle } from 'lucide-react';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  
  // Basic info
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('teacher');
  const [showPassword, setShowPassword] = useState(false);
  
  // School selection logic
  const [schoolAction, setSchoolAction] = useState('join'); // 'join' or 'new'
  const [schoolCode, setSchoolCode] = useState('');
  
  // New School info
  const [newSchoolName, setNewSchoolName] = useState('');
  const [newSchoolDistrict, setNewSchoolDistrict] = useState('');
  const [newSchoolState, setNewSchoolState] = useState('');
  const [newSchoolType, setNewSchoolType] = useState('Urban');
  
  // UI State
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successInfo, setSuccessInfo] = useState(null); // To show completion modal

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    let payload = {
      username,
      email,
      password,
      role: role === 'admin' ? 'national_admin' : 'teacher',
      state: null,
    };

    if (role === 'teacher') {
      if (schoolAction === 'join') {
        if (!schoolCode) {
          setError('Please provide an existing School Registration Code to join.');
          setLoading(false);
          return;
        }
        payload.school_code = schoolCode;
      } else {
        if (!newSchoolName || !newSchoolDistrict || !newSchoolState) {
          setError('Please fill out all New School details.');
          setLoading(false);
          return;
        }
        payload.new_school = {
          name: newSchoolName,
          district: newSchoolDistrict,
          state: newSchoolState,
          school_type: newSchoolType,
        };
      }
    }

    try {
      const res = await register(payload);
      
      // If a school was just created, show the code so they can write it down
      if (res.createdSchoolCode) {
        setSuccessInfo({ code: res.createdSchoolCode });
      } else {
        navigate('/');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // SUCCESS OVERLAY (When a new school is registered)
  if (successInfo) {
    return (
      <div className="auth-container">
        <div className="auth-card text-center">
          <CheckCircle size={48} className="text-neem-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">School Registered Successfully!</h2>
          <p className="mt-4 text-sm text-slate-500 leading-relaxed max-w-sm mx-auto">
            Your school has been created on the platform. Please save this unique Registration Code. 
            Other teachers and students will need this code to join your school instance.
          </p>
          <div className="bg-slate-50 p-5 my-6 rounded-xl border border-dashed border-slate-300 text-3xl tracking-[4px] font-extrabold text-india-600">
            {successInfo.code}
          </div>
          <button 
            className="btn btn-primary w-full py-3 text-[14px]" 
            onClick={() => navigate('/')}
          >
            Continue to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container py-12">
      <div className="auth-card max-w-[500px]">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center text-white"
               style={{ background: 'linear-gradient(135deg, #1e3a8a, #2b4acb)' }}>
            <GraduationCap size={28} />
          </div>
          <h1 className="text-xl font-bold text-slate-800 tracking-tight">Samagra Shiksha</h1>
          <p className="text-sm text-slate-500 mt-1">Create a New Account</p>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="flex items-center gap-2 px-4 py-3 mb-5 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input className="form-input" type="text" value={username} onChange={e => setUsername(e.target.value)} required />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div className="relative">
              <input
                className="form-input pr-10"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
              <button 
                type="button" 
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 border-none bg-transparent cursor-pointer" 
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Role</label>
            <select className="form-select" value={role} onChange={e => setRole(e.target.value)}>
              <option value="teacher">Teacher (or School Administrator)</option>
              <option value="admin">National Admin</option>
            </select>
          </div>

          {role === 'teacher' && (
            <div className="border-t border-slate-100 mt-5 pt-5">
              <div className="flex gap-6 mb-5">
                <label className="flex items-center gap-2 text-[13px] text-slate-700 cursor-pointer font-medium">
                  <input type="radio" className="w-4 h-4 accent-india-500 cursor-pointer" checked={schoolAction === 'join'} onChange={() => setSchoolAction('join')} />
                  Join Existing School
                </label>
                <label className="flex items-center gap-2 text-[13px] text-slate-700 cursor-pointer font-medium">
                  <input type="radio" className="w-4 h-4 accent-india-500 cursor-pointer" checked={schoolAction === 'new'} onChange={() => setSchoolAction('new')} />
                  Register New School
                </label>
              </div>

              {schoolAction === 'join' ? (
                <div className="form-group">
                  <label className="form-label">School Registration Code</label>
                  <input 
                    className="form-input"
                    type="text" 
                    placeholder="e.g. A1B2C3D4" 
                    value={schoolCode} 
                    onChange={e => setSchoolCode(e.target.value.toUpperCase())} 
                    required={schoolAction === 'join'} 
                  />
                  <p className="text-[11px] text-slate-400 mt-1.5">Ask your school administrator for this unique 8-character code.</p>
                </div>
              ) : (
                <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
                  <h4 className="text-[13px] font-bold text-slate-800 mb-4">New School Details</h4>
                  <div className="form-group">
                    <label className="form-label">School Name</label>
                    <input className="form-input" type="text" value={newSchoolName} onChange={e => setNewSchoolName(e.target.value)} required={schoolAction === 'new'} />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="form-group">
                      <label className="form-label">District</label>
                      <input className="form-input" type="text" value={newSchoolDistrict} onChange={e => setNewSchoolDistrict(e.target.value)} required={schoolAction === 'new'} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">State</label>
                      <input className="form-input" type="text" value={newSchoolState} onChange={e => setNewSchoolState(e.target.value)} required={schoolAction === 'new'} />
                    </div>
                  </div>
                  <div className="form-group mb-0">
                    <label className="form-label">School Type</label>
                    <select className="form-select" value={newSchoolType} onChange={e => setNewSchoolType(e.target.value)}>
                      <option value="Urban">Urban</option>
                      <option value="Rural">Rural</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          )}

          <button type="submit" className="btn btn-primary w-full mt-6 py-3 text-[14px]" disabled={loading || !username || !email || !password}>
            {loading ? <span className="spinner" /> : <><UserPlus size={18} /> Register</>}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{' '}
          <Link to="/login" className="text-india-500 font-medium hover:text-india-600 no-underline">
            Login here
          </Link>
        </div>
      </div>
    </div>
  );
}
