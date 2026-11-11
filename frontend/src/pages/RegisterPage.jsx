import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldAlert, UserPlus } from 'lucide-react';
import { publicApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { SERVICE_CATEGORIES } from '../constants/delhi';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [localities, setLocalities] = useState([]);
  const [role, setRole] = useState('customer');
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    password: '',
    locality: 'Saket',
    address: '',
    experience_years: 3,
    service_radius_km: 6,
    credential_id: '',
    bio: '',
    skills: ['General electrical maintenance'],
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    publicApi
      .localities()
      .then((res) => setLocalities(res.localities || []))
      .catch(() => {});
  }, []);

  const toggleSkill = (skill) => {
    setForm((prev) => {
      const exists = prev.skills.includes(skill);
      const next = exists ? prev.skills.filter((s) => s !== skill) : [...prev.skills, skill];
      return { ...prev, skills: next.length ? next : [skill] };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await register({
        ...form,
        role,
        experience_years: Number(form.experience_years),
        service_radius_km: Number(form.service_radius_km),
        credential_id: form.credential_id.trim() || null,
      });
      navigate(user.role === 'electrician' ? '/electrician/dashboard' : '/customer/dashboard');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(', '));
      } else {
        setError(detail || 'Registration failed. Please check your details.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto px-4 py-10">
      <div className="bg-white rounded-3xl p-8 border border-[#E8E4D8] shadow-elevated space-y-6">
        <div className="text-center space-y-1.5">
          <div className="w-11 h-11 rounded-2xl bg-electric text-navy flex items-center justify-center mx-auto">
            <UserPlus className="w-5 h-5" />
          </div>
          <h1 className="text-2xl font-extrabold text-navy">Join BijliBuddy</h1>
          <p className="text-sm text-slate-600">Register as a Delhi Household Customer or Independent Electrician</p>
        </div>

        {/* Role Selector */}
        <div className="grid grid-cols-2 gap-3 p-1.5 rounded-2xl bg-[#FAF9F5] border border-[#E8E4D8]">
          {[
            { id: 'customer', label: 'Household Customer' },
            { id: 'electrician', label: 'Independent Electrician' },
          ].map((opt) => (
            <button
              type="button"
              key={opt.id}
              onClick={() => setRole(opt.id)}
              className={`py-2.5 rounded-xl text-sm font-bold transition ${
                role === opt.id ? 'bg-navy text-electric shadow' : 'text-slate-600 hover:text-navy'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Full Name</label>
              <input
                type="text"
                required
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                placeholder="e.g., Rohit Sharma"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Indian Mobile Number</label>
              <input
                type="text"
                required
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="+919811223344 or 9811223344"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Email Address</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@example.com"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Password (min 6 chars)</label>
              <input
                type="password"
                required
                minLength={6}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Delhi Locality</label>
              <select
                value={form.locality}
                onChange={(e) => setForm({ ...form, locality: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
              >
                {(localities.length ? localities : [{ name: 'Saket', zone: 'South Delhi' }]).map((loc) => (
                  <option key={loc.name} value={loc.name}>
                    {loc.name} ({loc.zone})
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Street / House Address</label>
              <input
                type="text"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                placeholder="Block / Sector / Street"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
              />
            </div>
          </div>

          {role === 'electrician' && (
            <div className="space-y-4 pt-3 border-t border-slate-200">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-navy">Experience (Years)</label>
                  <input
                    type="number"
                    min={0}
                    max={50}
                    value={form.experience_years}
                    onChange={(e) => setForm({ ...form, experience_years: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-navy">Service Radius (km)</label>
                  <input
                    type="number"
                    min={1}
                    max={30}
                    value={form.service_radius_km}
                    onChange={(e) => setForm({ ...form, service_radius_km: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-navy">License / ID Ref</label>
                  <input
                    type="text"
                    value={form.credential_id}
                    onChange={(e) => setForm({ ...form, credential_id: e.target.value })}
                    placeholder="e.g., DL-WIRE-2026-401"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-navy">Electrical Specializations</label>
                <div className="flex flex-wrap gap-2">
                  {SERVICE_CATEGORIES.map((skill) => {
                    const active = form.skills.includes(skill);
                    return (
                      <button
                        type="button"
                        key={skill}
                        onClick={() => toggleSkill(skill)}
                        className={`text-xs px-3 py-1.5 rounded-full font-semibold border transition ${
                          active
                            ? 'bg-navy text-electric border-navy'
                            : 'bg-[#FAF9F5] text-slate-700 border-slate-200 hover:border-navy'
                        }`}
                      >
                        {skill}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
                <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-amber-700" />
                <span>
                  New electricians start with <strong>Pending / Unverified</strong> badge until an Admin reviews and
                  approves your submitted license/credential ID.
                </span>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-electric hover:bg-electric-hover text-navy font-extrabold text-sm transition shadow"
          >
            {loading ? 'Creating Account...' : 'Create BijliBuddy Account'}
          </button>
        </form>

        <div className="text-center text-xs text-slate-600">
          Already registered?{' '}
          <Link to="/login" className="font-bold text-navy underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
