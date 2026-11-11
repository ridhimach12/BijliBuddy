import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail, Sparkles, Zap } from 'lucide-react';
import { authApi } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [demoAccounts, setDemoAccounts] = useState([]);

  useEffect(() => {
    if (!import.meta.env.DEV) return;
    authApi
      .demoAccounts()
      .then((res) => setDemoAccounts(res.accounts || []))
      .catch(() => {});
  }, []);

  const redirectByRole = (role) => {
    if (role === 'electrician') navigate('/electrician/dashboard');
    else if (role === 'admin') navigate('/admin/dashboard');
    else navigate('/customer/dashboard');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await login(email, password);
      redirectByRole(user.role);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoClick = async (acc) => {
    if (!import.meta.env.DEV || acc.role === 'admin') return;
    setError('');
    setLoading(true);
    try {
      const user = await login(acc.email, acc.password);
      redirectByRole(user.role);
    } catch (err) {
      setError(err.response?.data?.detail || 'Demo login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12 space-y-6">
      <div className="bg-white rounded-3xl p-8 border border-[#E8E4D8] shadow-elevated space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-navy text-electric flex items-center justify-center mx-auto">
            <Zap className="w-6 h-6 fill-electric" />
          </div>
          <h1 className="text-2xl font-extrabold text-navy">Sign in to BijliBuddy</h1>
          <p className="text-sm text-slate-600">Access your household, electrician, or admin console</p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-navy">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm focus:outline-none focus:ring-2 focus:ring-navy"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-navy">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm focus:outline-none focus:ring-2 focus:ring-navy"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-navy hover:bg-navy-light text-white font-bold text-sm transition"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="text-center text-xs text-slate-600">
          New to BijliBuddy?{' '}
          <Link to="/register" className="font-bold text-navy underline">
            Create an account
          </Link>
        </div>
      </div>

      {/* Demo Accounts Quick Switch (development only) */}
      {import.meta.env.DEV && demoAccounts.length > 0 && (
        <div className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-navy/70">
            <Sparkles className="w-4 h-4 text-amber-500" />
            Synthetic Demonstration Accounts
          </div>
          <div className="space-y-2">
            {demoAccounts.map((acc) => (
              <button
                key={acc.email}
                onClick={() => handleDemoClick(acc)}
                disabled={loading}
                className="w-full text-left px-3.5 py-2.5 rounded-xl bg-[#FAF9F5] hover:bg-electric/25 border border-[#E8E4D8] transition flex items-center justify-between"
              >
                <div>
                  <div className="text-xs font-bold text-navy">{acc.label}</div>
                  <div className="text-[11px] text-slate-500">{acc.email}</div>
                </div>
                <span className="text-[11px] font-bold uppercase px-2 py-0.5 rounded bg-navy text-electric">
                  {acc.role}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
