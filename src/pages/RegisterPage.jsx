import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { GraduationCap, Eye, EyeOff, UserPlus, AlertCircle, CheckCircle, Search, School } from 'lucide-react';
import axios from 'axios';

const backendURL = import.meta.env.VITE_API_URL || '';

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
  const [verifiedSchool, setVerifiedSchool] = useState(null); // result from verify-code
  const [verifyingCode, setVerifyingCode] = useState(false);
  
  // New School info
  const [newSchoolName, setNewSchoolName] = useState('');
  const [newSchoolDistrict, setNewSchoolDistrict] = useState('');
  const [newSchoolState, setNewSchoolState] = useState('');
  const [newSchoolType, setNewSchoolType] = useState('Urban');
  const [generatedSchoolCode, setGeneratedSchoolCode] = useState('');

  // Generate an 8-character random code
  const generateRandomCode = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    return Array.from({ length: 8 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  };

  // UI State
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successInfo, setSuccessInfo] = useState(null);

  // Verify a school code against the backend
  const handleVerifyCode = async () => {
    if (!schoolCode || schoolCode.length < 4) return;
    setVerifyingCode(true);
    setVerifiedSchool(null);
    setError('');
    try {
      const authBase = backendURL ? `${backendURL}/auth` : '/auth';
      const res = await axios.get(`${authBase}/verify-code/${schoolCode}`);
      setVerifiedSchool(res.data);
    } catch {
      setVerifiedSchool(null);
      setError('Invalid school code. Please check and try again.');
    } finally {
      setVerifyingCode(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    let payload = {
      username,
      email,
      password,
      role: role === 'admin' ? 'national_admin' : role,
      state: null,
    };

    if (role === 'student') {
      // Students must always join an existing school
      if (!schoolCode) {
        setError('Please provide your School Registration Code to join.');
        setLoading(false);
        return;
      }
      payload.school_code = schoolCode;
    }

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
          registration_code: generatedSchoolCode || generateRandomCode(),
        };
      }
    }

    try {
      const res = await register(payload);
      
      if (res.createdSchoolCode) {
        setSuccessInfo({ code: res.createdSchoolCode, role });
      } else {
        navigate('/');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // SUCCESS OVERLAY
  if (successInfo) {
    return (
      <div className="auth-container">
        <div className="auth-card text-center">
          <CheckCircle size={48} className="text-neem-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">
            {successInfo.role === 'teacher' && schoolAction === 'new'
              ? 'School Registered Successfully!'
              : 'Registration Successful!'}
          </h2>
          <p className="mt-4 text-sm text-slate-500 leading-relaxed max-w-sm mx-auto">
            {successInfo.role === 'teacher' && schoolAction === 'new'
              ? 'Your school has been created. Share this unique code with teachers and students who need to join your school.'
              : 'You have successfully joined the school. Save this code for reference — share it with others who need to join.'}
          </p>
          <div className="bg-slate-50 p-5 my-6 rounded-xl border border-dashed border-slate-300">
            <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-2 font-semibold">Your School Code</p>
            <div className="text-3xl tracking-[4px] font-extrabold text-india-600">
              {successInfo.code}
            </div>
          </div>
          <p className="text-[12px] text-slate-400 mb-4">
            ⚠️ Please save this code. Teachers and students will use it to join this school.
          </p>
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

  // Code input with verify button (shared between student and teacher-join flows)
  const renderCodeInput = () => (
    <div className="form-group">
      <label className="form-label">School Registration Code</label>
      <div className="flex gap-2">
        <input 
          className="form-input flex-1"
          type="text" 
          placeholder="e.g. A1B2C3D4" 
          value={schoolCode} 
          onChange={e => {
            setSchoolCode(e.target.value.toUpperCase());
            setVerifiedSchool(null);
          }}
          maxLength={8}
        />
        <button
          type="button"
          className="btn btn-primary px-4 py-2 text-[13px] flex items-center gap-1.5 whitespace-nowrap"
          style={{ minWidth: 'auto' }}
          onClick={handleVerifyCode}
          disabled={verifyingCode || schoolCode.length < 4}
        >
          {verifyingCode ? <span className="spinner" style={{ width: 16, height: 16 }} /> : <Search size={15} />}
          Verify
        </button>
      </div>
      {verifiedSchool && (
        <div className="flex items-center gap-2 mt-2.5 px-3 py-2.5 rounded-lg bg-green-50 border border-green-200 text-green-700 text-[13px]">
          <School size={16} className="shrink-0" />
          <span><strong>{verifiedSchool.school_name}</strong> — {verifiedSchool.district}, {verifiedSchool.state}</span>
        </div>
      )}
      {!verifiedSchool && (
        <p className="text-[11px] text-slate-400 mt-1.5">Enter the code and click Verify to confirm the school.</p>
      )}
    </div>
  );

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
            <select className="form-select" value={role} onChange={e => { setRole(e.target.value); setVerifiedSchool(null); setSchoolCode(''); }}>
              <option value="student">Student</option>
              <option value="teacher">Teacher (or School Administrator)</option>
              <option value="admin">National Admin</option>
            </select>
          </div>

          {/* STUDENT — always join by code */}
          {role === 'student' && (
            <div className="border-t border-slate-100 mt-5 pt-5">
              <div className="flex items-center gap-2 mb-4">
                <School size={16} className="text-india-500" />
                <span className="text-[13px] font-bold text-slate-700">Join Your School</span>
              </div>
              <p className="text-[12px] text-slate-500 mb-4 leading-relaxed">
                Enter the unique School Registration Code provided by your teacher or school administrator.
              </p>
              {renderCodeInput()}
            </div>
          )}

          {/* TEACHER — join or register new */}
          {role === 'teacher' && (
            <div className="border-t border-slate-100 mt-5 pt-5">
              <div className="flex gap-6 mb-5">
                <label className="flex items-center gap-2 text-[13px] text-slate-700 cursor-pointer font-medium">
                  <input type="radio" className="w-4 h-4 accent-india-500 cursor-pointer" checked={schoolAction === 'join'} onChange={() => { setSchoolAction('join'); setVerifiedSchool(null); }} />
                  Join Existing School
                </label>
                <label className="flex items-center gap-2 text-[13px] text-slate-700 cursor-pointer font-medium">
                  <input type="radio" className="w-4 h-4 accent-india-500 cursor-pointer" checked={schoolAction === 'new'} onChange={() => { setSchoolAction('new'); setVerifiedSchool(null); if (!generatedSchoolCode) setGeneratedSchoolCode(generateRandomCode()); }} />
                  Register New School
                </label>
              </div>

              {schoolAction === 'join' ? (
                renderCodeInput()
              ) : (
                <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="text-[13px] font-bold text-slate-800">New School Details</h4>
                    <div className="bg-indigo-50 border border-indigo-100 rounded-md px-3 py-2 text-right">
                      <p className="text-[10px] text-indigo-500 uppercase font-bold tracking-wider mb-0.5">Registration Code</p>
                      <p className="text-sm font-black text-indigo-700 tracking-widest">{generatedSchoolCode}</p>
                    </div>
                  </div>
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
