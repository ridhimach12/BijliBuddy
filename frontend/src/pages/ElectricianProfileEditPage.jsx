import React, { useEffect, useState } from 'react';
import { Save, ShieldCheck, Wrench } from 'lucide-react';
import { electricianApi, publicApi } from '../api/client';
import { DAYS_SHORT, SERVICE_CATEGORIES } from '../constants/delhi';
import LocalityMap from '../components/LocalityMap';
import { VerificationBadge } from '../components/StatusBadge';

export default function ElectricianProfileEditPage() {
  const [profile, setProfile] = useState(null);
  const [localities, setLocalities] = useState([]);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    Promise.all([electricianApi.getProfile(), publicApi.localities()]).then(([prof, locRes]) => {
      setProfile(prof);
      setLocalities(locRes.localities || []);
    });
  }, []);

  const toggleSkill = (skill) => {
    setProfile((prev) => {
      const has = prev.skills.includes(skill);
      const next = has ? prev.skills.filter((s) => s !== skill) : [...prev.skills, skill];
      return { ...prev, skills: next.length ? next : [skill] };
    });
  };

  const toggleDay = (dayIdx) => {
    setProfile((prev) => ({
      ...prev,
      availability_slots: prev.availability_slots.map((s) =>
        s.day_of_week === dayIdx ? { ...s, is_active: !s.is_active } : s
      ),
    }));
  };

  const handleLocalityChange = (locName) => {
    const loc = localities.find((l) => l.name === locName);
    setProfile((prev) => ({
      ...prev,
      locality: locName,
      zone: loc?.zone || prev.zone,
      latitude: loc?.latitude || prev.latitude,
      longitude: loc?.longitude || prev.longitude,
    }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMsg('');
    try {
      const updated = await electricianApi.updateProfile({
        full_name: profile.full_name,
        phone: profile.phone,
        bio: profile.bio,
        experience_years: Number(profile.experience_years),
        service_radius_km: Number(profile.service_radius_km),
        locality: profile.locality,
        address: profile.address,
        latitude: profile.latitude,
        longitude: profile.longitude,
        is_available: profile.is_available,
        working_hours_start: profile.working_hours_start,
        working_hours_end: profile.working_hours_end,
        base_visit_fee_inr: Number(profile.base_visit_fee_inr),
        credential_id: profile.credential_id || '',
        skills: profile.skills,
        availability_slots: profile.availability_slots,
      });
      setProfile(updated);
      setMsg('Electrician profile, skills, and weekly availability saved!');
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Update failed.');
    } finally {
      setSaving(false);
    }
  };

  if (!profile) return <div className="max-w-5xl mx-auto p-8 text-sm text-slate-500">Loading...</div>;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-2xl bg-navy text-electric">
            <Wrench className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-navy">Electrician Profile & Availability</h1>
            <p className="text-xs text-slate-600">{profile.email}</p>
          </div>
        </div>
        <VerificationBadge status={profile.verification_status} />
      </div>

      {msg && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-semibold">
          {msg}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6 bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">Full Name</label>
            <input
              type="text"
              required
              value={profile.full_name}
              onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">Phone (+91)</label>
            <input
              type="text"
              required
              value={profile.phone}
              onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">License / Wireman Credential ID</label>
            <input
              type="text"
              value={profile.credential_id || ''}
              onChange={(e) => setProfile({ ...profile, credential_id: e.target.value })}
              placeholder="Changing ID triggers Admin re-review"
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">Experience (yrs)</label>
            <input
              type="number"
              min={0}
              max={55}
              value={profile.experience_years}
              onChange={(e) => setProfile({ ...profile, experience_years: e.target.value })}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">Radius (km)</label>
            <input
              type="number"
              min={1}
              max={35}
              value={profile.service_radius_km}
              onChange={(e) => setProfile({ ...profile, service_radius_km: e.target.value })}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">Visit Fee (INR)</label>
            <input
              type="number"
              min={50}
              max={2000}
              value={profile.base_visit_fee_inr}
              onChange={(e) => setProfile({ ...profile, base_visit_fee_inr: e.target.value })}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">Start Hour</label>
            <input
              type="time"
              value={profile.working_hours_start}
              onChange={(e) => setProfile({ ...profile, working_hours_start: e.target.value })}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">End Hour</label>
            <input
              type="time"
              value={profile.working_hours_end}
              onChange={(e) => setProfile({ ...profile, working_hours_end: e.target.value })}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-bold text-navy">Specializations & Skills</label>
          <div className="flex flex-wrap gap-2">
            {SERVICE_CATEGORIES.map((s) => {
              const active = profile.skills.includes(s);
              return (
                <button
                  type="button"
                  key={s}
                  onClick={() => toggleSkill(s)}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold border transition ${
                    active ? 'bg-navy text-electric border-navy' : 'bg-[#FAF9F5] text-slate-600 border-slate-200'
                  }`}
                >
                  {s}
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-bold text-navy">Weekly Working Days</label>
          <div className="grid grid-cols-7 gap-2">
            {profile.availability_slots?.map((slot) => (
              <button
                type="button"
                key={slot.day_of_week}
                onClick={() => toggleDay(slot.day_of_week)}
                className={`py-2.5 rounded-xl border text-xs font-bold transition ${
                  slot.is_active
                    ? 'bg-emerald-100 border-emerald-300 text-emerald-900'
                    : 'bg-slate-100 border-slate-200 text-slate-500'
                }`}
              >
                {DAYS_SHORT[slot.day_of_week]}
                <div className="text-[10px] font-medium">{slot.is_active ? 'Active' : 'Off'}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Base Delhi Locality</label>
              <select
                value={profile.locality}
                onChange={(e) => handleLocalityChange(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
              >
                {localities.map((l) => (
                  <option key={l.name} value={l.name}>
                    {l.name} ({l.zone})
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Base Address</label>
              <input
                type="text"
                value={profile.address}
                onChange={(e) => setProfile({ ...profile, address: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Bio / Summary</label>
              <textarea
                rows={3}
                value={profile.bio}
                onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="text-xs font-bold text-navy">
              Base Dispatch Pin ({profile.latitude.toFixed(4)}, {profile.longitude.toFixed(4)})
            </div>
            <LocalityMap
              centerLat={profile.latitude}
              centerLon={profile.longitude}
              customerLabel={profile.full_name}
              interactivePicker
              onPickLocation={(lat, lon) => setProfile({ ...profile, latitude: lat, longitude: lon })}
              heightClass="h-60"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="px-6 py-3 rounded-xl bg-navy hover:bg-navy-light text-white font-extrabold text-sm inline-flex items-center gap-2"
        >
          <Save className="w-4 h-4 text-electric" />
          {saving ? 'Saving Profile...' : 'Save Changes'}
        </button>
      </form>
    </div>
  );
}
