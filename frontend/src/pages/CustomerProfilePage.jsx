import React, { useEffect, useState } from 'react';
import { Save, User } from 'lucide-react';
import { customerApi, publicApi } from '../api/client';
import LocalityMap from '../components/LocalityMap';

export default function CustomerProfilePage() {
  const [profile, setProfile] = useState(null);
  const [localities, setLocalities] = useState([]);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    Promise.all([customerApi.getProfile(), publicApi.localities()]).then(([prof, locRes]) => {
      setProfile(prof);
      setLocalities(locRes.localities || []);
    });
  }, []);

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
      const updated = await customerApi.updateProfile({
        full_name: profile.full_name,
        phone: profile.phone,
        locality: profile.locality,
        address: profile.address,
        latitude: profile.latitude,
        longitude: profile.longitude,
      });
      setProfile(updated);
      setMsg('Customer profile saved successfully.');
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  if (!profile) {
    return <div className="max-w-4xl mx-auto p-8 text-sm text-slate-500">Loading customer profile...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-2xl bg-navy text-electric">
          <User className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-navy">Customer Profile & Default Location</h1>
          <p className="text-xs text-slate-600">{profile.email}</p>
        </div>
      </div>

      {msg && (
        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-semibold">
          {msg}
        </div>
      )}

      <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-2 gap-6 bg-white p-6 rounded-3xl border border-[#E8E4D8] shadow-card">
        <div className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">Full Name</label>
            <input
              type="text"
              required
              value={profile.full_name}
              onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">Indian Mobile Number</label>
            <input
              type="text"
              required
              value={profile.phone}
              onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">Delhi Locality</label>
            <select
              value={profile.locality}
              onChange={(e) => handleLocalityChange(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            >
              {localities.map((l) => (
                <option key={l.name} value={l.name}>
                  {l.name} ({l.zone})
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-bold text-navy">Saved Household Address</label>
            <textarea
              rows={2}
              value={profile.address}
              onChange={(e) => setProfile({ ...profile, address: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="w-full py-3 rounded-xl bg-navy hover:bg-navy-light text-white font-bold text-sm inline-flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Profile'}
          </button>
        </div>

        <div className="space-y-2">
          <div className="text-xs font-bold text-navy">Default Map Pin ({profile.latitude.toFixed(4)}, {profile.longitude.toFixed(4)})</div>
          <LocalityMap
            centerLat={profile.latitude}
            centerLon={profile.longitude}
            customerLabel={profile.full_name}
            interactivePicker
            onPickLocation={(lat, lon) => setProfile((prev) => ({ ...prev, latitude: lat, longitude: lon }))}
            heightClass="h-72"
          />
        </div>
      </form>
    </div>
  );
}
