import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Award,
  CheckCircle2,
  Clock,
  IndianRupee,
  PlayCircle,
  Power,
  Settings,
  Star,
  XCircle,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { electricianApi } from '../api/client';
import { formatINR } from '../constants/delhi';
import { BookingStatusBadge, VerificationBadge } from '../components/StatusBadge';
import ReliabilityBreakdownModal from '../components/ReliabilityBreakdownModal';

export default function ElectricianDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('incoming');
  const [quotes, setQuotes] = useState({});
  const [notes, setNotes] = useState({});
  const [actionMsg, setActionMsg] = useState('');
  const [showReliabilityModal, setShowReliabilityModal] = useState(false);

  const loadDashboard = () => {
    electricianApi
      .getDashboard()
      .then((res) => setData(res))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDashboard();
    const timer = setInterval(loadDashboard, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleToggleAvailability = async () => {
    if (!data?.profile) return;
    const next = !data.profile.is_available;
    await electricianApi.updateProfile({ is_available: next });
    setActionMsg(`Availability updated to: ${next ? 'Available Now' : 'Unavailable'}`);
    loadDashboard();
  };

  const handleRespond = async (bookingId, action, defaultEstimate) => {
    try {
      const q = quotes[bookingId] !== undefined ? Number(quotes[bookingId]) : Number(defaultEstimate);
      await electricianApi.respondBooking(bookingId, {
        action,
        electrician_quote_inr: action === 'accept' ? q : undefined,
        electrician_notes: notes[bookingId] || undefined,
      });
      setActionMsg(`Booking #${bookingId} ${action === 'accept' ? 'accepted' : 'declined'}.`);
      loadDashboard();
    } catch (err) {
      setActionMsg(err.response?.data?.detail || 'Action failed.');
    }
  };

  const handleStart = async (bookingId) => {
    await electricianApi.startBooking(bookingId);
    setActionMsg(`Job #${bookingId} marked In Progress.`);
    loadDashboard();
  };

  const handleComplete = async (bookingId, defaultAmount) => {
    const finalAmt = quotes[bookingId] !== undefined ? Number(quotes[bookingId]) : Number(defaultAmount);
    await electricianApi.completeBooking(bookingId, {
      final_amount_inr: finalAmt,
      on_time_completed: true,
      electrician_notes: notes[bookingId] || 'Completed safely and tested.',
    });
    setActionMsg(`Job #${bookingId} completed! Earnings updated.`);
    loadDashboard();
  };

  if (loading) {
    return <div className="max-w-7xl mx-auto p-8 text-sm text-slate-500">Loading electrician workspace...</div>;
  }

  const prof = data?.profile;
  const counts = data?.counts || {};
  const earnings = data?.earnings || {};

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Banner */}
      <div className="bg-navy text-ivory rounded-3xl p-6 sm:p-8 flex flex-col lg:flex-row lg:items-center justify-between gap-6 shadow-elevated">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-xs font-extrabold uppercase tracking-wider text-electric">
              Electrician Workspace
            </span>
            <VerificationBadge status={prof?.verification_status} />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">{prof?.full_name}</h1>
          <p className="text-xs sm:text-sm text-ivory/80">
            {prof?.locality} ({prof?.zone}) • Radius: {prof?.service_radius_km} km • Hours:{' '}
            {prof?.working_hours_start}–{prof?.working_hours_end}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleToggleAvailability}
            className={`px-5 py-3 rounded-xl font-extrabold text-sm inline-flex items-center gap-2 transition shadow ${
              prof?.is_available
                ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
                : 'bg-slate-600 hover:bg-slate-500 text-white'
            }`}
          >
            <Power className="w-4 h-4" />
            {prof?.is_available ? 'Status: Available Now' : 'Status: Unavailable'}
          </button>

          <Link
            to="/electrician/profile"
            className="px-4 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-sm inline-flex items-center gap-2 border border-white/15"
          >
            <Settings className="w-4 h-4" /> Edit Profile & Hours
          </Link>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-semibold">
          {actionMsg}
        </div>
      )}

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card">
          <div className="text-xs font-semibold text-slate-500">Incoming Requests</div>
          <div className="text-2xl font-extrabold text-navy mt-1">{counts.incoming_requests || 0}</div>
        </div>
        <div className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card">
          <div className="text-xs font-semibold text-slate-500">Active Jobs</div>
          <div className="text-2xl font-extrabold text-navy mt-1">{counts.active_jobs || 0}</div>
        </div>
        <div className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card">
          <div className="text-xs font-semibold text-slate-500">Completed Jobs</div>
          <div className="text-2xl font-extrabold text-navy mt-1">{counts.completed_jobs || 0}</div>
        </div>
        <div className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card">
          <div className="text-xs font-semibold text-slate-500">Total Earnings</div>
          <div className="text-2xl font-extrabold text-navy mt-1">
            {formatINR(earnings.total_earnings_inr)}
          </div>
        </div>
        <button
          onClick={() => setShowReliabilityModal(true)}
          className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card text-left hover:border-navy transition col-span-2 lg:col-span-1"
        >
          <div className="text-xs font-semibold text-slate-500 flex items-center justify-between">
            <span>Reliability Score</span>
            <Award className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-extrabold text-navy mt-1">
            {data?.reliability?.reliability_score} <span className="text-xs font-semibold">/ 100</span>
          </div>
          <div className="text-[11px] text-navy underline mt-0.5">View Breakdown</div>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-[#E8E4D8] pb-3">
        {[
          { id: 'incoming', label: `Incoming (${data?.incoming_requests?.length || 0})` },
          { id: 'active', label: `Active Jobs (${data?.active_jobs?.length || 0})` },
          { id: 'earnings', label: 'Earnings & Analytics' },
          { id: 'reviews', label: `Reviews (${data?.reviews?.length || 0})` },
          { id: 'history', label: `Job History (${data?.job_history?.length || 0})` },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition ${
              tab === t.id ? 'bg-navy text-electric' : 'bg-white text-slate-600 border border-[#E8E4D8] hover:text-navy'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Incoming Requests */}
      {tab === 'incoming' && (
        <div className="space-y-4">
          {data?.incoming_requests?.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 border border-[#E8E4D8] text-center text-sm text-slate-500">
              No pending incoming requests right now (auto-polling every 10s).
            </div>
          ) : (
            data.incoming_requests.map((b) => (
              <div key={b.id} className="bg-white rounded-2xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-extrabold text-slate-500">Request #{b.id}</span>
                      <span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-amber-100 text-amber-900">
                        {b.service_request?.urgency}
                      </span>
                    </div>
                    <h3 className="text-lg font-extrabold text-navy mt-1">
                      {b.service_request?.selected_category}
                    </h3>
                    <p className="text-sm text-slate-700 mt-1">{b.service_request?.description}</p>
                    <div className="text-xs text-slate-500 mt-2">
                      Customer: <strong>{b.customer?.full_name}</strong> ({b.customer?.phone}) •{' '}
                      {b.service_request?.address}, {b.service_request?.locality} • ETA ~{b.estimated_arrival_mins} mins
                    </div>
                  </div>
                  <div className="bg-[#FAF9F5] border border-[#E8E4D8] rounded-xl p-3 text-right">
                    <div className="text-[11px] text-slate-500">AI Baseline Estimate</div>
                    <div className="font-extrabold text-navy text-lg">
                      {formatINR(b.ai_estimate_snapshot_inr)}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-100">
                  <div>
                    <label className="text-[11px] font-bold text-navy block mb-1">Your Quotation (INR)</label>
                    <input
                      type="number"
                      defaultValue={b.ai_estimate_snapshot_inr}
                      onChange={(e) => setQuotes({ ...quotes, [b.id]: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm font-bold"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="text-[11px] font-bold text-navy block mb-1">Note for Customer</label>
                    <input
                      type="text"
                      placeholder="e.g., Will arrive in 25 mins with spare 32A MCB..."
                      onChange={(e) => setNotes({ ...notes, [b.id]: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
                    />
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => handleRespond(b.id, 'accept', b.ai_estimate_snapshot_inr)}
                    className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs inline-flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-4 h-4" /> Accept & Send Quote
                  </button>
                  <button
                    onClick={() => handleRespond(b.id, 'reject', b.ai_estimate_snapshot_inr)}
                    className="px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 font-bold text-xs inline-flex items-center gap-1.5"
                  >
                    <XCircle className="w-4 h-4" /> Decline
                  </button>
                  <Link
                    to={`/bookings/${b.id}`}
                    className="px-4 py-2.5 rounded-xl border border-slate-200 text-navy font-bold text-xs ml-auto"
                  >
                    Open Full Details
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Active Jobs */}
      {tab === 'active' && (
        <div className="space-y-4">
          {data?.active_jobs?.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 border border-[#E8E4D8] text-center text-sm text-slate-500">
              No active accepted or in-progress jobs.
            </div>
          ) : (
            data.active_jobs.map((b) => (
              <div key={b.id} className="bg-white rounded-2xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-extrabold text-slate-500">Job #{b.id}</span>
                      <BookingStatusBadge status={b.status} />
                    </div>
                    <h3 className="text-lg font-extrabold text-navy mt-1">{b.service_request?.selected_category}</h3>
                    <p className="text-sm text-slate-700">{b.service_request?.description}</p>
                    <div className="text-xs text-slate-500 mt-1">
                      {b.customer?.full_name} ({b.customer?.phone}) • {b.service_request?.address},{' '}
                      {b.service_request?.locality}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[11px] text-slate-500">Agreed Quotation</div>
                    <div className="text-xl font-extrabold text-navy">
                      {formatINR(b.electrician_quote_inr || b.ai_estimate_snapshot_inr)}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-100">
                  <div>
                    <label className="text-[11px] font-bold text-navy block mb-1">Final Bill Amount (INR)</label>
                    <input
                      type="number"
                      defaultValue={b.electrician_quote_inr || b.ai_estimate_snapshot_inr}
                      onChange={(e) => setQuotes({ ...quotes, [b.id]: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm font-bold"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="text-[11px] font-bold text-navy block mb-1">Completion Work Notes</label>
                    <input
                      type="text"
                      placeholder="Summary of repair performed..."
                      onChange={(e) => setNotes({ ...notes, [b.id]: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
                    />
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  {b.status === 'accepted' && (
                    <button
                      onClick={() => handleStart(b.id)}
                      className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs inline-flex items-center gap-1.5"
                    >
                      <PlayCircle className="w-4 h-4" /> Mark Arrived & Start Work
                    </button>
                  )}
                  <button
                    onClick={() => handleComplete(b.id, b.electrician_quote_inr || b.ai_estimate_snapshot_inr)}
                    className="px-5 py-2.5 rounded-xl bg-navy hover:bg-navy-light text-electric font-bold text-xs inline-flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-4 h-4" /> Mark Job Completed
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Earnings & Analytics */}
      {tab === 'earnings' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
            <h3 className="font-extrabold text-navy text-base inline-flex items-center gap-2">
              <IndianRupee className="w-5 h-5" /> Earnings by Service Category (INR)
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={earnings.by_category || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8E4D8" />
                  <XAxis dataKey="category" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(val) => formatINR(val)} />
                  <Bar dataKey="earnings_inr" fill="#0F1E36" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
            <h3 className="font-extrabold text-navy text-base">Daily Completed Earnings Trend</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={earnings.by_date || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8E4D8" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(val) => formatINR(val)} />
                  <Bar dataKey="earnings_inr" fill="#EAB308" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Reviews */}
      {tab === 'reviews' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data?.reviews?.length === 0 ? (
            <div className="bg-white rounded-2xl p-6 border border-[#E8E4D8] text-sm text-slate-500">
              No reviews yet.
            </div>
          ) : (
            data.reviews.map((r) => (
              <div key={r.id} className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-bold text-navy">{r.customer_name} (Job #{r.booking_id})</span>
                  <span className="inline-flex items-center gap-1 font-bold text-amber-600">
                    <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" /> {r.rating}/5
                  </span>
                </div>
                <p className="text-xs text-slate-700">{r.comment}</p>
              </div>
            ))
          )}
        </div>
      )}

      {/* History */}
      {tab === 'history' && (
        <div className="bg-white rounded-2xl border border-[#E8E4D8] shadow-card overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm">
            <thead className="bg-[#FAF9F5] border-b border-[#E8E4D8]">
              <tr>
                <th className="py-3 px-4 font-bold">Job</th>
                <th className="py-3 px-4 font-bold">Category</th>
                <th className="py-3 px-4 font-bold">Locality</th>
                <th className="py-3 px-4 font-bold">Amount</th>
                <th className="py-3 px-4 font-bold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data?.job_history?.map((b) => (
                <tr key={b.id}>
                  <td className="py-3 px-4 font-bold text-navy">#{b.id}</td>
                  <td className="py-3 px-4">{b.service_request?.selected_category}</td>
                  <td className="py-3 px-4">{b.service_request?.locality}</td>
                  <td className="py-3 px-4 font-bold">
                    {formatINR(b.final_amount_inr || b.electrician_quote_inr || b.ai_estimate_snapshot_inr)}
                  </td>
                  <td className="py-3 px-4">
                    <BookingStatusBadge status={b.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showReliabilityModal && (
        <ReliabilityBreakdownModal
          electricianName={prof?.full_name}
          reliability={data?.reliability}
          onClose={() => setShowReliabilityModal(false)}
        />
      )}
    </div>
  );
}
