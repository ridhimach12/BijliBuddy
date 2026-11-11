import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Award, Calendar, Clock, MapPin, Phone, Star } from 'lucide-react';
import { publicApi } from '../api/client';
import { DAYS_SHORT, formatINR } from '../constants/delhi';
import { VerificationBadge } from '../components/StatusBadge';
import LocalityMap from '../components/LocalityMap';

export default function ElectricianPublicProfilePage() {
  const { id } = useParams();
  const [elec, setElec] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    publicApi
      .electricianDetail(id)
      .then((res) => setElec(res))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="max-w-5xl mx-auto p-8 text-sm text-slate-500">Loading profile...</div>;
  if (!elec) return <div className="max-w-5xl mx-auto p-8 text-sm text-rose-600">Electrician not found.</div>;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#E8E4D8] shadow-card flex flex-col md:flex-row justify-between gap-6">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-navy">{elec.full_name}</h1>
            <VerificationBadge status={elec.verification_status} />
            <span
              className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                elec.is_available ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'
              }`}
            >
              {elec.is_available ? 'Available Now' : 'Currently Unavailable'}
            </span>
          </div>
          <p className="text-sm text-slate-600 max-w-2xl">{elec.bio}</p>
          <div className="flex flex-wrap gap-4 text-xs font-medium text-slate-700">
            <span className="inline-flex items-center gap-1">
              <MapPin className="w-4 h-4 text-navy" /> {elec.locality} ({elec.zone}) • {elec.service_radius_km} km radius
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock className="w-4 h-4 text-navy" /> {elec.working_hours_start} – {elec.working_hours_end}
            </span>
            <span className="inline-flex items-center gap-1">
              <Phone className="w-4 h-4 text-navy" /> {elec.phone}
            </span>
            {elec.is_verified && elec.credential_id && (
              <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-900 font-bold">
                Verified ID: {elec.credential_id}
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {elec.skills?.map((s) => (
              <span key={s} className="text-xs px-3 py-1 rounded-full bg-navy text-electric font-semibold">
                {s}
              </span>
            ))}
          </div>
        </div>

        <div className="bg-[#FAF9F5] border border-[#E8E4D8] rounded-2xl p-5 min-w-[210px] space-y-2 text-center self-start">
          <div className="text-xs font-bold uppercase text-slate-500">Reliability Score</div>
          <div className="text-4xl font-extrabold text-navy">{elec.reliability?.reliability_score}</div>
          <div className="text-[11px] font-semibold text-slate-600">{elec.reliability?.confidence_tier}</div>
          <div className="pt-2 border-t border-[#E8E4D8] text-xs space-y-1">
            <div>Experience: <strong>{elec.experience_years} years</strong></div>
            <div>Visit Fee: <strong>{formatINR(elec.base_visit_fee_inr)}</strong></div>
            <div>Completed Jobs: <strong>{elec.stats?.completed || 0}</strong></div>
          </div>
          <Link
            to="/request-service"
            className="block w-full mt-3 py-2 rounded-xl bg-electric hover:bg-electric-hover text-navy font-extrabold text-xs"
          >
            Request Service
          </Link>
        </div>
      </div>

      {/* Reliability Explainability & Weekly Schedule */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-3">
          <h2 className="font-extrabold text-navy text-base inline-flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-500" /> Reliability Score Breakdown
          </h2>
          <p className="text-xs text-slate-600">{elec.reliability?.fairness_note}</p>
          <div className="space-y-2.5 pt-1">
            {elec.reliability?.breakdown?.map((b, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span>{b.factor}</span>
                  <span>{b.points_earned} / {b.weight_pct}</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-navy rounded-full"
                    style={{ width: `${Math.round((b.points_earned / b.weight_pct) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-3">
            <h2 className="font-extrabold text-navy text-base inline-flex items-center gap-2">
              <Calendar className="w-5 h-5" /> Weekly Working Schedule
            </h2>
            <div className="grid grid-cols-7 gap-1.5 text-center">
              {elec.availability_slots?.map((slot) => (
                <div
                  key={slot.day_of_week}
                  className={`p-2 rounded-xl border text-[11px] ${
                    slot.is_active
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                      : 'bg-slate-100 border-slate-200 text-slate-400'
                  }`}
                >
                  <div className="font-bold">{DAYS_SHORT[slot.day_of_week]}</div>
                  <div>{slot.is_active ? slot.start_time : 'Off'}</div>
                </div>
              ))}
            </div>
          </div>

          <LocalityMap
            centerLat={elec.latitude}
            centerLon={elec.longitude}
            customerLabel={`${elec.full_name} (${elec.locality})`}
            heightClass="h-48"
          />
        </div>
      </div>

      {/* Customer Reviews */}
      <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
        <h2 className="font-extrabold text-navy text-lg">
          Customer Reviews ({elec.reviews?.length || 0})
        </h2>
        {elec.reviews?.length === 0 ? (
          <p className="text-sm text-slate-500">No reviews yet — new electricians receive fair Bayesian prior scoring.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {elec.reviews.map((r) => (
              <div key={r.id} className="p-4 rounded-2xl bg-[#FAF9F5] border border-[#E8E4D8] space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-navy">{r.customer_name}</span>
                  <span className="inline-flex items-center gap-1 font-bold text-amber-600">
                    <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" /> {r.rating}/5
                  </span>
                </div>
                <p className="text-xs text-slate-700">{r.comment}</p>
                <div className="text-[11px] text-slate-500">
                  {r.was_on_time ? 'On-time completion' : 'Delayed'} • {new Date(r.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
