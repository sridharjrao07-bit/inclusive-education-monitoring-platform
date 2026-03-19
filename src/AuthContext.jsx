import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const backendURL = import.meta.env.VITE_API_URL || '';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('auth_token'));
  const [loading, setLoading] = useState(true);

  // On mount / token change, fetch current user
  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    const authBase = backendURL ? `${backendURL}/auth` : '/auth';
    axios.get(`${authBase}/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => {
        setUser(r.data);
        setLoading(false);
      })
      .catch(() => {
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
        setLoading(false);
      });
  }, [token]);

  const login = async (username, password) => {
    const authBase = backendURL ? `${backendURL}/auth` : '/auth';
    
    // Convert to x-www-form-urlencoded
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    
    const res = await axios.post(`${authBase}/login`, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    });
    const newToken = res.data.access_token;
    localStorage.setItem('auth_token', newToken);
    setToken(newToken);
    // Fetch user profile
    const me = await axios.get(`${authBase}/me`, {
      headers: { Authorization: `Bearer ${newToken}` },
    });
    setUser(me.data);
    return me.data;
  };

  const register = async (userData) => {
    const authBase = backendURL ? `${backendURL}/auth` : '/auth';
    const regRes = await axios.post(`${authBase}/register`, userData);
    
    // Login automatically after registration
    await login(userData.username, userData.password);
    return { 
      user: regRes.data.user, 
      createdSchoolCode: regRes.data.school_code 
    };
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
  };

  const isAuthenticated = !!user && !!token;
  const isAdmin = user?.role === 'national_admin' || user?.role === 'admin';
  const isStateAdmin = user?.role === 'state_admin';
  const isTeacher = user?.role === 'teacher';

  return (
    <AuthContext.Provider value={{
      user, token, loading, login, logout, register,
      isAuthenticated, isAdmin, isStateAdmin, isTeacher,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
