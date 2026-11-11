import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Search, Star, Wrench } from 'lucide-react';
import { publicApi } from '../api/client';
import { SERVICE_CATEGORIES, formatINR } from '../constants/delhi';
import LocalityMap from '../components/LocalityMap';
import { VerificationBadge } from '../components/StatusBadge';

export default function ElectriciansDirectoryPage() {
  const [electricians, setElectricians] = useState([]);
  const [localities, setLocalities] = useState([]);
  const [filters, setFilters] = useState({
    locality: '',
    category: '',
    verified_only: false,
    available_only: false,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    publicApi.localities().then((res) => setLocalities(res.localities || []));
  }, []);

  useEffect(() => {
    setLoading(true);
    publicApi
      .electricians({
        locality: filters.locality || undefined,
        category: filters.category || undefined,
        verified_only: filters.verified_only,
        available_only: filters.available_only,
      })
      .then((res) => setElectricians(res.electricians || []))
      .finally(() => setLoading(false));
  }, [filters]);

  const mapCenter = (() => {
    const found = localities.find((l) => l.name === filters.locality);
    return found ? [found.latitude, found.longitude] : [28.6139, 77.209];
  })();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="text-xs font-extrabold uppercase tracking-wider text-navy/60">Delhi Network</span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-navy mt-1">
            Electrician Directory ({electricians.length})
          </h1>
          <p className="text-sm text-slate-600">
            Explore independent Delhi technicians, verification status, skills, and reliability scores.
          </p>
        </div>
        <Link
          to="/request-service"
          className="px-5 py-2.5 rounded-xl bg-electric hover:bg-electric-hover text-navy font-extrabold text-sm shadow"
        >
          Run AI Matching Instead →
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl p-4 border border-[#E8E4D8] shadow-card grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 items-center">
        <select
          value={filters.locality}
          onChange={(e) => setFilters({ ...filters, locality: e.target.value })}
          className="px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm font-medium"
        >
          <option value="">All Delhi Localities</option>
          {localities.map((l) => (
            <option key={l.name} value={l.name}>
              {l.name} ({l.zone})
            </option>
          ))}
        </select>

        <select
          value={filters.category}
          onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          className="px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm font-medium"
        >
          <option value="">All Electrical Skills</option>
          {SERVICE_CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <label className="flex items-center gap-2 text-xs font-bold text-navy px-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.verified_only}
            onChange={(e) => setFilters({ ...filters, verified_only: e.target.checked })}
          />
          Admin-Verified Credentials Only
        </label>

        <label className="flex items-center gap-2 text-xs font-bold text-navy px-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.available_only}
            onChange={(e) => setFilters({ ...filters, available_only: e.target.checked })}
          />
          Available Now Only
        </label>
      </div>

      {/* Map */}
      <LocalityMap
        centerLat={mapCenter[0]}
        centerLon={mapCenter[1]}
        customerLabel={filters.locality || 'New Delhi Center'}
        electricians={electricians}
        heightClass="h-72"
      />

      {/* Cards Grid */}
      {loading ? (
        <div className="text-sm text-slate-500">Loading electricians...</div>
      ) : electricians.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-[#E8E4D8] text-center text-sm text-slate-600">
          No electricians match the selected filters.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {electricians.map((e) => (
            <Link
              key={e.id}
              to={`/electricians/${e.id}`}
              className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card hover:border-navy transition flex flex-col justify-between gap-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-extrabold text-navy text-base">{e.full_name}</h3>
                    <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                      <MapPin className="w-3.5 h-3.5" /> {e.locality} ({e.zone}) • {e.experience_years} yrs exp
                    </p>
                  </div>
                  <span
                    className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                      e.is_available ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {e.is_available ? 'Available' : 'Unavailable'}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <VerificationBadge status={e.verification_status} />
                  <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-navy text-electric">
                    Reliability {e.reliability_score}/100
                  </span>
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {e.skills.map((sk) => (
                    <span key={sk} className="text-[11px] px-2 py-0.5 rounded-md bg-[#FAF9F5] border border-[#E8E4D8] text-navy">
                      {sk}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="inline-flex items-center gap-1 font-semibold text-navy">
                  <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                  {e.average_rating ? `${e.average_rating} (${e.review_count})` : `New (${e.smoothed_rating}★ prior)`}
                </span>
                <span className="font-bold text-navy">Visit Fee: {formatINR(e.base_visit_fee_inr)}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
