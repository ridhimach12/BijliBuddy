import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  CheckCircle2,
  Clock,
  CreditCard,
  MapPin,
  Phone,
  RefreshCw,
  Star,
  XCircle,
} from 'lucide-react';
import { bookingApi, customerApi, resolveAssetUrl } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { formatINR } from '../constants/delhi';
import { BookingStatusBadge, VerificationBadge } from '../components/StatusBadge';
import LocalityMap from '../components/LocalityMap';
import SafetyBanner from '../components/SafetyBanner';

const STEPS = ['pending', 'accepted', 'in_progress', 'completed'];

export default function BookingStatusPage() {
  const { id } = useParams();
  const { user } = useAuth();

  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  // Customer Review State
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [wasOnTime, setWasOnTime] = useState(true);
  const [submittingReview, setSubmittingReview] = useState(false);

  // Sandbox Payment State
  const [payMethod, setPayMethod] = useState('sandbox_upi');
  const [paying, setPaying] = useState(false);

  const loadBooking = () => {
    bookingApi
      .getDetail(id)
      .then((res) => {
        setBooking(res.booking);
        setError('');
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Could not load booking details.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadBooking();
    const timer = setInterval(loadBooking, 6000);
    return () => clearInterval(timer);
  }, [id]);

  const handleCancel = async () => {
    try {
      const res = await bookingApi.cancel(id, 'Cancelled via booking status page');
      setBooking(res.booking);
      setActionMsg('Booking cancelled.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Cancel failed.');
    }
  };

  const handleSandboxPay = async () => {
    setPaying(true);
    try {
      const res = await bookingApi.sandboxPay(id, payMethod);
      setBooking(res.booking);
      setActionMsg(res.notice);
    } catch (err) {
      setError(err.response?.data?.detail || 'Sandbox payment failed.');
    } finally {
      setPaying(false);
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    setSubmittingReview(true);
    try {
      await customerApi.submitReview(id, { rating, comment, was_on_time: wasOnTime });
      setActionMsg('Thank you! Your review has been saved and updated the electrician’s reliability score.');
      loadBooking();
    } catch (err) {
      setError(err.response?.data?.detail || 'Review submission failed.');
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading) {
    return <div className="max-w-5xl mx-auto p-8 text-sm text-slate-500">Loading booking status...</div>;
  }

  if (!booking) {
    return (
      <div className="max-w-3xl mx-auto p-8 bg-white rounded-2xl border border-[#E8E4D8] mt-8 text-center space-y-3">
        <p className="text-rose-700 font-semibold">{error || 'Booking not found.'}</p>
        <Link to="/" className="text-sm font-bold text-navy underline">
          Back Home
        </Link>
      </div>
    );
  }

  const sr = booking.service_request;
  const elec = booking.electrician;
  const currentStepIdx = STEPS.indexOf(booking.status);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-extrabold uppercase tracking-wider text-slate-500">
              Booking #{booking.id}
            </span>
            <BookingStatusBadge status={booking.status} />
          </div>
          <h1 className="text-2xl font-extrabold text-navy">{sr?.selected_category}</h1>
          <p className="text-xs text-slate-600">
            {sr?.address} • {sr?.locality} ({sr?.zone})
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadBooking}
            className="px-3.5 py-2 rounded-xl border border-slate-200 hover:bg-[#FAF9F5] text-xs font-bold text-navy inline-flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Live Polling (6s)
          </button>
          {['pending', 'accepted'].includes(booking.status) && (
            <button
              onClick={handleCancel}
              className="px-3.5 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 text-xs font-bold inline-flex items-center gap-1"
            >
              <XCircle className="w-3.5 h-3.5" /> Cancel Booking
            </button>
          )}
        </div>
      </div>

      {actionMsg && (
        <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-semibold">
          {actionMsg}
        </div>
      )}
      {error && (
        <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 text-xs font-semibold">
          {error}
        </div>
      )}

      {/* Timeline Stepper */}
      {currentStepIdx >= 0 && (
        <div className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card">
          <div className="grid grid-cols-4 gap-2">
            {[
              { key: 'pending', label: 'Requested' },
              { key: 'accepted', label: 'Accepted & Quoted' },
              { key: 'in_progress', label: 'Work Started' },
              { key: 'completed', label: 'Completed' },
            ].map((step, i) => {
              const done = i <= currentStepIdx;
              return (
                <div key={step.key} className="text-center space-y-1.5">
                  <div
                    className={`h-2 rounded-full ${
                      done ? 'bg-navy' : 'bg-slate-200'
                    }`}
                  />
                  <div className={`text-xs font-bold ${done ? 'text-navy' : 'text-slate-400'}`}>
                    {step.label}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Hazard Banner if flagged */}
      {sr?.hazard_detected && (
        <SafetyBanner
          hazardAssessment={{
            severity: 'critical',
            reasons: ['Hazard indicators detected in original service description'],
            safety_instructions: sr.hazard_warnings,
          }}
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Details & Transparent Pricing Comparison */}
        <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
          <h2 className="font-extrabold text-navy text-lg">Job & Pricing Summary</h2>
          <p className="text-sm text-slate-700 bg-[#FAF9F5] p-3.5 rounded-xl border border-[#E8E4D8]">
            {sr?.description}
          </p>

          {sr?.image_path && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
              <img
                src={resolveAssetUrl(sr.image_path)}
                alt="Customer reference"
                className="w-16 h-16 rounded-xl object-cover border"
              />
              <div className="text-xs text-slate-600">
                Reference photo shared by customer (not AI-diagnosed).
              </div>
            </div>
          )}

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
              <div className="text-[11px] text-slate-500">AI Baseline Est.</div>
              <div className="font-extrabold text-navy text-base">
                {formatINR(booking.ai_estimate_snapshot_inr)}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
              <div className="text-[11px] text-slate-500">Electrician Quote</div>
              <div className="font-extrabold text-navy text-base">
                {booking.electrician_quote_inr ? formatINR(booking.electrician_quote_inr) : 'Pending'}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-electric/25 border border-electric">
              <div className="text-[11px] text-navy/80 font-semibold">Final Bill</div>
              <div className="font-extrabold text-navy text-base">
                {booking.final_amount_inr ? formatINR(booking.final_amount_inr) : 'On Completion'}
              </div>
            </div>
          </div>

          {booking.electrician_notes && (
            <div className="text-xs bg-sky-50 border border-sky-200 text-sky-950 p-3 rounded-xl">
              <strong>Electrician Note:</strong> {booking.electrician_notes}
            </div>
          )}

          <div className="pt-3 border-t border-slate-100 space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-500">Assigned Electrician</div>
                <Link
                  to={`/electricians/${elec?.id}`}
                  className="font-extrabold text-navy text-base hover:underline"
                >
                  {elec?.full_name}
                </Link>
              </div>
              <VerificationBadge status={elec?.verification_status} />
            </div>
            <div className="flex flex-wrap gap-4 text-xs text-slate-600">
              <span className="inline-flex items-center gap-1">
                <Phone className="w-3.5 h-3.5 text-navy" /> {elec?.phone}
              </span>
              <span className="inline-flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-navy" /> {elec?.locality}
              </span>
              <span className="inline-flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-navy" /> ETA ~{booking.estimated_arrival_mins} mins
              </span>
            </div>
          </div>
        </div>

        {/* Map */}
        <div className="space-y-4">
          <LocalityMap
            centerLat={sr?.latitude || 28.5677}
            centerLon={sr?.longitude || 77.21}
            customerLabel={`Customer (${sr?.locality})`}
            electricians={
              elec
                ? [
                    {
                      ...elec,
                      electrician_id: elec.id,
                      estimated_arrival_mins: booking.estimated_arrival_mins,
                      match_score: booking.match_score,
                    },
                  ]
                : []
            }
            selectedElectricianId={elec?.id}
            heightClass="h-80"
          />
          {booking.match_explanation?.reasons && (
            <div className="bg-white rounded-2xl p-4 border border-[#E8E4D8] text-xs space-y-1">
              <div className="font-bold text-navy">Why {elec?.full_name} Was Matched ({booking.match_score}% Score):</div>
              <ul className="list-disc list-inside text-slate-600 space-y-0.5">
                {booking.match_explanation.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Post-Completion Sandbox Payment & Customer Rating */}
      {booking.status === 'completed' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sandbox Payment */}
          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-extrabold text-navy text-base inline-flex items-center gap-2">
                <CreditCard className="w-5 h-5" /> Sandbox Payment (Demo Only)
              </h3>
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900">
                Demonstration Only
              </span>
            </div>

            {booking.payment?.status === 'demo_paid' ? (
              <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs space-y-1">
                <div className="font-bold flex items-center gap-1.5 text-sm">
                  <CheckCircle2 className="w-4 h-4" /> Sandbox Payment Recorded
                </div>
                <div>Amount: <strong>{formatINR(booking.payment.amount_inr)}</strong></div>
                <div>Method: <strong>{booking.payment.payment_method}</strong></div>
                <div>Ref: <strong>{booking.payment.transaction_ref}</strong></div>
              </div>
            ) : user?.role === 'customer' ? (
              <div className="space-y-3">
                <p className="text-xs text-slate-600">
                  Simulate settling <strong>{formatINR(booking.final_amount_inr || booking.electrician_quote_inr)}</strong>{' '}
                  using our sandbox ledger (no real money moves).
                </p>
                <select
                  value={payMethod}
                  onChange={(e) => setPayMethod(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
                >
                  <option value="sandbox_upi">Sandbox UPI (Demo)</option>
                  <option value="sandbox_card">Sandbox Card (Demo)</option>
                  <option value="cash_on_completion">Cash on Completion (Demo)</option>
                </select>
                <button
                  onClick={handleSandboxPay}
                  disabled={paying}
                  className="w-full py-2.5 rounded-xl bg-navy text-white font-bold text-sm hover:bg-navy-light"
                >
                  {paying ? 'Recording...' : 'Confirm Sandbox Payment'}
                </button>
              </div>
            ) : (
              <div className="text-xs text-slate-500">Awaiting customer sandbox payment confirmation.</div>
            )}
          </div>

          {/* Review & Rating */}
          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
            <h3 className="font-extrabold text-navy text-base inline-flex items-center gap-2">
              <Star className="w-5 h-5 text-amber-400 fill-amber-400" /> Customer Rating & Review
            </h3>

            {booking.review ? (
              <div className="p-4 rounded-2xl bg-[#FAF9F5] border border-[#E8E4D8] space-y-1.5">
                <div className="font-extrabold text-navy text-sm">
                  Rated {booking.review.rating} / 5 ★ •{' '}
                  {booking.review.was_on_time ? 'Arrived On Time' : 'Delayed'}
                </div>
                <p className="text-xs text-slate-700">{booking.review.comment || 'No written comment.'}</p>
              </div>
            ) : user?.role === 'customer' ? (
              <form onSubmit={handleSubmitReview} className="space-y-3">
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      type="button"
                      key={star}
                      onClick={() => setRating(star)}
                      className={`p-2 rounded-xl border ${
                        rating >= star ? 'bg-electric/30 border-amber-400 text-amber-600' : 'border-slate-200 text-slate-400'
                      }`}
                    >
                      <Star className={`w-5 h-5 ${rating >= star ? 'fill-amber-400' : ''}`} />
                    </button>
                  ))}
                  <span className="text-xs font-bold text-navy ml-2">{rating} / 5</span>
                </div>

                <label className="flex items-center gap-2 text-xs font-semibold text-navy">
                  <input
                    type="checkbox"
                    checked={wasOnTime}
                    onChange={(e) => setWasOnTime(e.target.checked)}
                    className="rounded"
                  />
                  Electrician arrived and completed job on time
                </label>

                <textarea
                  rows={2}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Share feedback on safety, quality, and pricing transparency..."
                  className="w-full p-3 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
                />

                <button
                  type="submit"
                  disabled={submittingReview}
                  className="w-full py-2.5 rounded-xl bg-electric hover:bg-electric-hover text-navy font-extrabold text-sm"
                >
                  {submittingReview ? 'Submitting...' : 'Submit Rating & Review'}
                </button>
              </form>
            ) : (
              <div className="text-xs text-slate-500">Customer has not submitted a review yet.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
