import React, { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('bijlibuddy_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('bijlibuddy_token');
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then((me) => {
        setUser(me);
        localStorage.setItem('bijlibuddy_user', JSON.stringify(me));
      })
      .catch(() => {
        localStorage.removeItem('bijlibuddy_token');
        localStorage.removeItem('bijlibuddy_user');
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const persistSession = (tokenResponse) => {
    localStorage.setItem('bijlibuddy_token', tokenResponse.access_token);
    localStorage.setItem('bijlibuddy_user', JSON.stringify(tokenResponse.user));
    setUser(tokenResponse.user);
    return tokenResponse.user;
  };

  const login = async (email, password) => {
    const res = await authApi.login({ email, password });
    return persistSession(res);
  };

  const register = async (payload) => {
    const res = await authApi.register(payload);
    return persistSession(res);
  };

  const logout = () => {
    localStorage.removeItem('bijlibuddy_token');
    localStorage.removeItem('bijlibuddy_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
