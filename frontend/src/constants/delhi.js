export const SERVICE_CATEGORIES = [
  'Wiring',
  'Switchboard',
  'Fan installation/repair',
  'Lighting',
  'MCB/circuit breaker',
  'Inverter',
  'Electrical appliance connection',
  'General electrical maintenance',
];

export const URGENCY_OPTIONS = [
  { value: 'normal', label: 'Normal', desc: 'Flexible same-day or scheduled slot' },
  { value: 'urgent', label: 'Urgent', desc: 'Priority dispatch within ~30-45 mins' },
  { value: 'emergency', label: 'Emergency / Hazard', desc: 'Immediate safety priority (sparks, tripped main)' },
];

export const TIME_OF_SERVICE_OPTIONS = [
  { value: 'morning', label: 'Morning (6AM–12PM)', slotBucket: 'Morning (6AM-12PM)' },
  { value: 'afternoon', label: 'Afternoon (12PM–5PM)', slotBucket: 'Afternoon (12PM-5PM)' },
  { value: 'evening', label: 'Evening (5PM–9PM)', slotBucket: 'Evening (5PM-9PM)' },
  { value: 'night', label: 'Night (9PM–6AM)', slotBucket: 'Night (9PM-6AM)' },
];

export const COMPLEXITY_OPTIONS = [
  { value: 'low', label: 'Low (Minor fix / single component)' },
  { value: 'medium', label: 'Medium (Standard fault / installation)' },
  { value: 'high', label: 'High (Rewiring / main DB / multi-point)' },
];

export const BOOKING_STATUS_META = {
  pending: { label: 'Pending Acceptance', color: 'bg-amber-100 text-amber-900 border-amber-300' },
  accepted: { label: 'Accepted — En Route', color: 'bg-sky-100 text-sky-900 border-sky-300' },
  in_progress: { label: 'Work In Progress', color: 'bg-indigo-100 text-indigo-900 border-indigo-300' },
  completed: { label: 'Completed', color: 'bg-emerald-100 text-emerald-900 border-emerald-300' },
  rejected: { label: 'Declined', color: 'bg-rose-100 text-rose-900 border-rose-300' },
  cancelled: { label: 'Cancelled', color: 'bg-slate-200 text-slate-800 border-slate-300' },
};

export const VERIFICATION_META = {
  verified: { label: 'Admin Verified', color: 'bg-emerald-100 text-emerald-900 border-emerald-300' },
  pending: { label: 'Verification Pending', color: 'bg-amber-100 text-amber-900 border-amber-300' },
  unverified: { label: 'Unverified', color: 'bg-slate-200 text-slate-700 border-slate-300' },
  rejected: { label: 'Verification Rejected', color: 'bg-rose-100 text-rose-900 border-rose-300' },
};

export function formatINR(amount) {
  if (amount === null || amount === undefined || Number.isNaN(Number(amount))) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number(amount));
}

export const DAYS_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
