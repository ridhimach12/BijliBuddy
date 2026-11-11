import React from 'react';
import { AlertTriangle, PhoneCall, ShieldAlert } from 'lucide-react';

export default function SafetyBanner({ hazardAssessment, compact = false }) {
  const severity = hazardAssessment?.severity || 'none';
  const isCritical = severity === 'critical';
  const isElevated = severity === 'elevated';

  if (!hazardAssessment && !compact) return null;

  const containerStyle = isCritical
    ? 'bg-rose-50 border-rose-400 text-rose-950'
    : isElevated
    ? 'bg-amber-50 border-amber-400 text-amber-950'
    : 'bg-navy/5 border-navy/15 text-navy';

  const Icon = isCritical ? AlertTriangle : ShieldAlert;

  return (
    <div className={`rounded-2xl border-2 p-4 ${containerStyle}`}>
      <div className="flex items-start gap-3">
        <div
          className={`p-2 rounded-xl shrink-0 ${
            isCritical ? 'bg-rose-600 text-white' : isElevated ? 'bg-amber-500 text-white' : 'bg-navy text-electric'
          }`}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="font-bold text-sm sm:text-base">
              {isCritical
                ? 'IMMEDIATE ELECTRICAL HAZARD WARNING'
                : isElevated
                ? 'Elevated Electrical Safety Caution'
                : 'Electrical Safety Guardrails'}
            </h4>
            <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-white/80 border border-current/20">
              <PhoneCall className="w-3.5 h-3.5" /> Emergency: 112 • Fire: 101
            </span>
          </div>

          {hazardAssessment?.reasons?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {hazardAssessment.reasons.map((reason, idx) => (
                <span key={idx} className="text-xs font-medium px-2 py-0.5 rounded-md bg-white/80 border border-current/15">
                  {reason}
                </span>
              ))}
            </div>
          )}

          <ul className="text-xs sm:text-sm space-y-1 list-disc list-inside leading-relaxed">
            {(hazardAssessment?.safety_instructions || [
              'Stay away from exposed wires, sparks, burning smells, or wet switchboards.',
              'Never attempt live electrical repairs yourself. Wait for a qualified electrician or contact 112 / BSES (19123 / 19122) / Tata Power DDL (19124) in emergencies.',
            ]).map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>

          <p className="text-[11px] opacity-80 pt-1 border-t border-current/15">
            Delhi DISCOM Helplines: BSES Rajdhani <strong>19123</strong> • BSES Yamuna <strong>19122</strong> • Tata Power DDL{' '}
            <strong>19124</strong>. AI classification assists routing only and never replaces on-site safety inspection.
          </p>
        </div>
      </div>
    </div>
  );
}
