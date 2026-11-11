import React from 'react';
import { ShieldAlert, ShieldCheck, Clock, ShieldOff } from 'lucide-react';
import { BOOKING_STATUS_META, VERIFICATION_META } from '../constants/delhi';

export function BookingStatusBadge({ status }) {
  const meta = BOOKING_STATUS_META[status] || {
    label: status,
    color: 'bg-slate-100 text-slate-800 border-slate-300',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${meta.color}`}>
      {meta.label}
    </span>
  );
}

export function VerificationBadge({ status, showUnverified = true }) {
  if (!showUnverified && status !== 'verified') return null;
  const meta = VERIFICATION_META[status] || VERIFICATION_META.unverified;

  const Icon =
    status === 'verified'
      ? ShieldCheck
      : status === 'pending'
      ? Clock
      : status === 'rejected'
      ? ShieldOff
      : ShieldAlert;

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${meta.color}`}>
      <Icon className="w-3.5 h-3.5" />
      {meta.label}
    </span>
  );
}
