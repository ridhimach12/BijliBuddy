import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Calendar, Clock, MapPin, PlusCircle, Star, Wrench } from 'lucide-react';
import { customerApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { BookingStatusBadge, VerificationBadge } from '../components/StatusBadge';
import { formatINR } from '../constants/delhi';
import SafetyBanner from '../components/SafetyBanner';

export default function CustomerDashboard() {
  const { user } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadBookings = () => {
    customerApi
      .listBookings()
      .then((res) => setBookings(res.bookings || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadBookings();
    const timer = setInterval(loadBookings, 12000);
    return () => clearInterval(timer);
  }, []);

  const activeBookings = bookings.filter((b) => ['pending', 'accepted', 'in_progress'].includes(b.status));
  const previousBookings = bookings.filter((b) => !['pending', 'accepted', 'in_progress'].includes(b.status));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header */}
      <div className="bg-navy text-ivory rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-elevated">
        <div className="space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-electric">Household Dashboard</span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Namaste, {user?.full_name}</h1>
          <p className="text-sm text-ivory/75">
            Default Delhi area: <strong>{user?.locality || 'Saket'}</strong> ({user?.zone || 'South Delhi'}). Track active
            bookings or run AI diagnostics for a new electrical issue.
          </p>
        </div>
        <Link
          to="/request-service"
          className="px-5 py-3.5 rounded-xl bg-electric hover:bg-electric-hover text-navy font-extrabold text-sm inline-flex items-center justify-center gap-2 shrink-0 transition shadow"
        >
          <PlusCircle className="w-5 h-5" />
          New Service Request
        </Link>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Active Bookings', value: activeBookings.length, icon: Clock },
          { label: 'Completed Jobs', value: bookings.filter((b) => b.status === 'completed').length, icon: Wrench },
          { label: 'Total Requests', value: bookings.length, icon: Calendar },
          {
            label: 'Reviews Submitted',
            value: bookings.filter((b) => !!b.review).length,
            icon: Star,
          },
        ].map((stat, idx) => (
          <div key={idx} className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-slate-500">{stat.label}</div>
              <div className="text-2xl font-extrabold text-navy mt-1">{stat.value}</div>
            </div>
            <div className="p-2.5 rounded-xl bg-electric/25 text-navy">
              <stat.icon className="w-5 h-5" />
            </div>
          </div>
        ))}
      </div>

      {/* Active Bookings */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-extrabold text-navy">Active Bookings (Auto-Updating)</h2>
          <span className="text-xs text-slate-500">Live polling every 12s</span>
        </div>

        {loading ? (
          <div className="bg-white rounded-2xl p-6 border border-[#E8E4D8] text-sm text-slate-500">
            Loading bookings...
          </div>
        ) : activeBookings.length === 0 ? (
          <div className="bg-white rounded-2xl p-8 border border-[#E8E4D8] text-center space-y-3">
            <p className="text-sm text-slate-600">No active bookings right now.</p>
            <Link
              to="/request-service"
              className="inline-flex items-center gap-1.5 text-sm font-bold text-navy underline"
            >
              Describe an electrical issue to get matched <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activeBookings.map((b) => (
              <Link
                key={b.id}
                to={`/bookings/${b.id}`}
                className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card hover:border-navy transition space-y-3 block"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="text-xs font-bold text-slate-500">Booking #{b.id}</div>
                    <h3 className="font-bold text-navy text-base">{b.service_request?.selected_category}</h3>
                  </div>
                  <BookingStatusBadge status={b.status} />
                </div>
                <p className="text-xs text-slate-600 line-clamp-2">{b.service_request?.description}</p>
                <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-navy">{b.electrician?.full_name}</span>
                    <VerificationBadge status={b.electrician?.verification_status} showUnverified={false} />
                  </div>
                  <span className="font-semibold text-slate-600 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" /> ETA ~{b.estimated_arrival_mins} mins
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs bg-[#FAF9F5] rounded-xl px-3 py-2">
                  <span>AI Baseline: {formatINR(b.ai_estimate_snapshot_inr)}</span>
                  <span className="font-bold text-navy">
                    Quote: {b.electrician_quote_inr ? formatINR(b.electrician_quote_inr) : 'Awaiting electrician'}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Previous Bookings */}
      <section className="space-y-4">
        <h2 className="text-xl font-extrabold text-navy">Previous Bookings</h2>
        {previousBookings.length === 0 ? (
          <div className="bg-white rounded-2xl p-6 border border-[#E8E4D8] text-sm text-slate-500">
            No past bookings found.
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-[#E8E4D8] shadow-card overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-[#FAF9F5] border-b border-[#E8E4D8] text-slate-600">
                <tr>
                  <th className="py-3 px-4 font-bold">Booking</th>
                  <th className="py-3 px-4 font-bold">Category & Issue</th>
                  <th className="py-3 px-4 font-bold">Electrician</th>
                  <th className="py-3 px-4 font-bold">Amount</th>
                  <th className="py-3 px-4 font-bold">Status</th>
                  <th className="py-3 px-4 font-bold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {previousBookings.map((b) => (
                  <tr key={b.id} className="hover:bg-[#FAF9F5]/70">
                    <td className="py-3 px-4 font-bold text-navy">#{b.id}</td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-navy">{b.service_request?.selected_category}</div>
                      <div className="text-xs text-slate-500 max-w-xs truncate">{b.service_request?.description}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-navy">{b.electrician?.full_name}</div>
                      <div className="text-[11px] text-slate-500">{b.electrician?.locality}</div>
                    </td>
                    <td className="py-3 px-4 font-bold text-navy">
                      {formatINR(b.final_amount_inr || b.electrician_quote_inr || b.ai_estimate_snapshot_inr)}
                    </td>
                    <td className="py-3 px-4">
                      <BookingStatusBadge status={b.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/bookings/${b.id}`}
                        className="px-3 py-1.5 rounded-lg bg-navy text-white text-xs font-semibold hover:bg-navy-light"
                      >
                        {b.status === 'completed' && !b.review ? 'Rate & View' : 'View'}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <SafetyBanner compact />
    </div>
  );
}
