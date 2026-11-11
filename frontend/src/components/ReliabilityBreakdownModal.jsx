import React from 'react';
import { Award, ShieldCheck, X } from 'lucide-react';

export default function ReliabilityBreakdownModal({ reliability, electricianName, onClose }) {
  if (!reliability) return null;

  return (
    <div className="fixed inset-0 z-50 bg-navy/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-elevated border border-[#E8E4D8] space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-navy/70">
              <Award className="w-4 h-4 text-amber-500" /> Explainable Reliability Engine
            </div>
            <h3 className="text-xl font-bold text-navy mt-1">{electricianName}</h3>
            <p className="text-xs text-slate-600">{reliability.confidence_tier}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center justify-between bg-[#FAF9F5] border border-[#E8E4D8] rounded-xl p-4">
          <div>
            <div className="text-xs font-medium text-slate-500">Overall Score</div>
            <div className="text-3xl font-extrabold text-navy">
              {reliability.reliability_score}
              <span className="text-sm font-semibold text-slate-500"> / 100</span>
            </div>
          </div>
          <div className="text-right text-xs text-slate-600 space-y-1">
            <div>Completed Jobs: <strong>{reliability.verified_completed_jobs}</strong></div>
            <div>Smoothed Rating: <strong>{reliability.smoothed_rating} ★</strong> ({reliability.review_count} reviews)</div>
            <div>
              Admin Verified:{' '}
              <strong className={reliability.is_admin_verified ? 'text-emerald-700' : 'text-amber-700'}>
                {reliability.is_admin_verified ? 'Yes' : 'Not yet'}
              </strong>
            </div>
          </div>
        </div>

        <div className="space-y-2.5">
          {reliability.breakdown?.map((item, idx) => (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-navy">{item.factor} ({item.weight_pct}%)</span>
                <span className="font-bold text-navy">
                  {item.points_earned} / {item.weight_pct} pts
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full bg-electric rounded-full"
                  style={{ width: `${Math.round((item.points_earned / item.weight_pct) * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-start gap-2 text-xs bg-sky-50 border border-sky-200 text-sky-900 rounded-xl p-3">
          <ShieldCheck className="w-4 h-4 shrink-0 mt-0.5 text-sky-700" />
          <p>{reliability.fairness_note}</p>
        </div>
      </div>
    </div>
  );
}
