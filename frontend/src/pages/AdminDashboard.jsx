import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Award,
  BarChart3,
  CheckCircle2,
  Cpu,
  IndianRupee,
  ShieldCheck,
  TrendingUp,
  Users,
  XCircle,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  ComposedChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { adminApi, mlApi } from '../api/client';
import { formatINR } from '../constants/delhi';
import { VerificationBadge } from '../components/StatusBadge';

const CHART_COLORS = ['#0F1E36', '#EAB308', '#0284C7', '#10B981', '#F97316', '#6366F1', '#EC4899', '#64748B'];

export default function AdminDashboard() {
  const [overview, setOverview] = useState(null);
  const [demand, setDemand] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [electricians, setElectricians] = useState([]);
  const [mlMetrics, setMlMetrics] = useState(null);
  const [tab, setTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState('');

  const loadAll = () => {
    Promise.all([
      adminApi.overview(),
      adminApi.demandAnalytics(7),
      adminApi.leaderboard(),
      adminApi.listElectricians(),
      mlApi.modelMetrics(),
    ])
      .then(([ov, dem, lb, elecs, metrics]) => {
        setOverview(ov);
        setDemand(dem);
        setLeaderboard(lb.leaderboard || []);
        setElectricians(elecs.electricians || []);
        setMlMetrics(metrics);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleVerifyDecision = async (id, decision) => {
    setActionMsg('');
    try {
      await adminApi.verifyElectrician(id, {
        decision,
        verification_notes:
          decision === 'verified'
            ? 'Identity & wireman credential approved by Admin.'
            : 'Credential verification declined by Admin.',
      });
      setActionMsg(`Electrician #${id} updated to '${decision}'.`);
      loadAll();
    } catch (err) {
      setActionMsg(err.response?.data?.detail || 'Verification update failed.');
    }
  };

  if (loading) {
    return <div className="max-w-7xl mx-auto p-8 text-sm text-slate-500">Loading Admin Console...</div>;
  }

  const kpis = overview?.kpis || {};

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="bg-navy text-ivory rounded-3xl p-6 sm:p-8 flex flex-wrap items-center justify-between gap-4 shadow-elevated">
        <div>
          <span className="text-xs font-extrabold uppercase tracking-wider text-electric">
            Admin Operations & Intelligence
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-1">
            BijliBuddy Platform Analytics & Governance
          </h1>
          <p className="text-xs sm:text-sm text-ivory/75 mt-1">
            Live marketplace metrics, Delhi demand forecasting, Bayesian leaderboard, and credential approvals.
          </p>
        </div>
        <button
          onClick={loadAll}
          className="px-4 py-2.5 rounded-xl bg-electric hover:bg-electric-hover text-navy font-extrabold text-xs"
        >
          Refresh Live Metrics
        </button>
      </div>

      {actionMsg && (
        <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-semibold">
          {actionMsg}
        </div>
      )}

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[
          { label: 'Total Customers', value: kpis.total_customers, sub: 'Registered households', icon: Users },
          {
            label: 'Electricians',
            value: kpis.registered_electricians,
            sub: `${kpis.verified_electricians} verified • ${kpis.pending_verifications} pending`,
            icon: ShieldCheck,
          },
          { label: 'Total Bookings', value: kpis.total_bookings, sub: `${kpis.active_bookings} active now`, icon: BarChart3 },
          { label: 'Completed Jobs', value: kpis.completed_bookings, sub: 'Verified completions', icon: CheckCircle2 },
          {
            label: 'Cancellations',
            value: `${kpis.cancelled_bookings} (${kpis.cancellation_rate_pct}%)`,
            sub: `${kpis.rejected_bookings} declined by worker`,
            icon: AlertTriangle,
          },
          {
            label: 'Revenue Estimate',
            value: formatINR(kpis.realized_revenue_inr),
            sub: `+ ${formatINR(kpis.estimated_pipeline_revenue_inr)} pipeline`,
            icon: IndianRupee,
          },
        ].map((card, i) => (
          <div key={i} className="bg-white rounded-2xl p-4 border border-[#E8E4D8] shadow-card space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
              <span>{card.label}</span>
              <card.icon className="w-4 h-4 text-navy" />
            </div>
            <div className="text-xl font-extrabold text-navy">{card.value}</div>
            <div className="text-[11px] text-slate-500">{card.sub}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-[#E8E4D8] pb-3">
        {[
          { id: 'overview', label: 'Trends & Distribution' },
          { id: 'forecast', label: 'Demand Forecast (Module 4)' },
          { id: 'leaderboard', label: 'Electrician Leaderboard (Module 5)' },
          { id: 'verification', label: `Verification Queue (${kpis.pending_verifications || 0} Pending)` },
          { id: 'models', label: 'ML Model Diagnostics' },
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

      {/* Tab 1: Overview & Trends */}
      {tab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
            <h2 className="font-extrabold text-navy text-base">Daily Booking Trends</h2>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={overview?.booking_trends || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8E4D8" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="bookings" name="Total Bookings" stroke="#0F1E36" fill="#0F1E36" fillOpacity={0.18} />
                  <Area type="monotone" dataKey="completed" name="Completed" stroke="#EAB308" fill="#FACC15" fillOpacity={0.35} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
            <h2 className="font-extrabold text-navy text-base">Delhi Geographic Demand Distribution</h2>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={overview?.geographic_distribution || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8E4D8" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="locality" width={115} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="bookings" fill="#0F1E36" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
            <h2 className="font-extrabold text-navy text-base">Service Category Distribution</h2>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={overview?.category_distribution || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8E4D8" />
                  <XAxis dataKey="category" tick={{ fontSize: 10 }} interval={0} angle={-18} textAnchor="end" height={60} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="bookings" radius={[6, 6, 0, 0]}>
                    {(overview?.category_distribution || []).map((_, index) => (
                      <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
            <h2 className="font-extrabold text-navy text-base">Booking Outcome Breakdown</h2>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={overview?.status_breakdown || []}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={95}
                    label={({ status, count }) => `${status}: ${count}`}
                  >
                    {(overview?.status_breakdown || []).map((_, index) => (
                      <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Demand Analytics & Statistical Forecasting */}
      {tab === 'forecast' && demand && (
        <div className="space-y-6">
          <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4 text-xs text-amber-950 space-y-1.5">
            <div className="font-extrabold text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4" /> {demand.model_info?.model_type}
            </div>
            <div>
              Analyzed <strong>{demand.total_analyzed_bookings}</strong> bookings across{' '}
              <strong>{demand.model_info?.observed_days}</strong> days. Baseline daily rate:{' '}
              <strong>{demand.model_info?.baseline_daily_rate}</strong> bookings/day • Expected next 7 days total:{' '}
              <strong>{demand.model_info?.expected_next_7_days_total}</strong> bookings.
            </div>
            <ul className="list-disc list-inside text-[11px] space-y-0.5 pt-1">
              {demand.model_info?.limitations?.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
              <h3 className="font-extrabold text-navy text-base">7-Day Statistical Demand Forecast (with 90% Bounds)</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={demand.forecast_next_days || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E8E4D8" />
                    <XAxis dataKey="day_name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Area type="monotone" dataKey="upper_bound" name="Upper Bound (90%)" stroke="#94A3B8" fill="#E2E8F0" fillOpacity={0.5} />
                    <Bar dataKey="expected_bookings" name="Expected Bookings" fill="#0F1E36" radius={[6, 6, 0, 0]} />
                    <Line type="monotone" dataKey="lower_bound" name="Lower Bound" stroke="#EAB308" strokeWidth={2} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
              <h3 className="font-extrabold text-navy text-base">Demand by Time Slot</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={demand.by_time_slot || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E8E4D8" />
                    <XAxis dataKey="time_slot" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="bookings" fill="#EAB308" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
              <h3 className="font-extrabold text-navy text-base">Demand by Day of Week</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={demand.by_day_of_week || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E8E4D8" />
                    <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="bookings" fill="#0284C7" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4">
              <h3 className="font-extrabold text-navy text-base">Expected Next 7 Days by Top Localities</h3>
              <div className="space-y-2.5">
                {demand.forecast_by_locality?.map((item) => (
                  <div key={item.locality} className="flex items-center justify-between text-xs p-2.5 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                    <span className="font-bold text-navy">{item.locality}</span>
                    <span className="font-extrabold text-navy">{item.expected_next_7_days} expected bookings</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Electrician Leaderboard */}
      {tab === 'leaderboard' && (
        <div className="bg-white rounded-3xl border border-[#E8E4D8] shadow-card overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm">
            <thead className="bg-[#FAF9F5] border-b border-[#E8E4D8]">
              <tr>
                <th className="py-3 px-4 font-bold">Rank</th>
                <th className="py-3 px-4 font-bold">Electrician</th>
                <th className="py-3 px-4 font-bold">Locality</th>
                <th className="py-3 px-4 font-bold">Verification</th>
                <th className="py-3 px-4 font-bold">Reliability</th>
                <th className="py-3 px-4 font-bold">Completed</th>
                <th className="py-3 px-4 font-bold">Accept Rate</th>
                <th className="py-3 px-4 font-bold">Rating</th>
                <th className="py-3 px-4 font-bold">Earnings</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {leaderboard.map((row, idx) => (
                <tr key={row.electrician_id} className="hover:bg-[#FAF9F5]/70">
                  <td className="py-3 px-4 font-extrabold text-navy">#{idx + 1}</td>
                  <td className="py-3 px-4">
                    <div className="font-bold text-navy">{row.full_name}</div>
                    <div className="text-[11px] text-slate-500">{row.confidence_tier}</div>
                  </td>
                  <td className="py-3 px-4">{row.locality}</td>
                  <td className="py-3 px-4">
                    <VerificationBadge status={row.verification_status} />
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-extrabold text-navy px-2.5 py-0.5 rounded-full bg-electric/40">
                      {row.reliability_score}/100
                    </span>
                  </td>
                  <td className="py-3 px-4 font-semibold">{row.completed_jobs}</td>
                  <td className="py-3 px-4">{row.acceptance_rate_pct}%</td>
                  <td className="py-3 px-4">
                    {row.average_rating ? `${row.average_rating}★ (${row.review_count})` : `Prior ${row.smoothed_rating}★`}
                  </td>
                  <td className="py-3 px-4 font-bold text-navy">{formatINR(row.total_earnings_inr)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 4: Credential Verification Queue */}
      {tab === 'verification' && (
        <div className="space-y-4">
          <div className="bg-sky-50 border border-sky-200 rounded-2xl p-4 text-xs text-sky-950">
            <strong>Safety & Trust Rule:</strong> Electricians are NEVER labeled Verified automatically. An Admin must
            review and approve a valid credential ID below.
          </div>

          <div className="bg-white rounded-3xl border border-[#E8E4D8] shadow-card overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-[#FAF9F5] border-b border-[#E8E4D8]">
                <tr>
                  <th className="py-3 px-4 font-bold">Electrician</th>
                  <th className="py-3 px-4 font-bold">Locality & Exp</th>
                  <th className="py-3 px-4 font-bold">Submitted Credential ID</th>
                  <th className="py-3 px-4 font-bold">Status</th>
                  <th className="py-3 px-4 font-bold text-right">Admin Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {electricians.map((e) => (
                  <tr key={e.id}>
                    <td className="py-3 px-4">
                      <div className="font-bold text-navy">{e.full_name}</div>
                      <div className="text-[11px] text-slate-500">{e.email} • {e.phone}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div>{e.locality}</div>
                      <div className="text-[11px] text-slate-500">{e.experience_years} yrs</div>
                    </td>
                    <td className="py-3 px-4 font-mono text-xs">
                      {e.credential_id || <span className="text-slate-400 italic">Not submitted</span>}
                    </td>
                    <td className="py-3 px-4">
                      <VerificationBadge status={e.verification_status} />
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleVerifyDecision(e.id, 'verified')}
                        disabled={!e.credential_id}
                        className="px-3 py-1.5 rounded-lg bg-emerald-600 disabled:bg-slate-200 disabled:text-slate-400 text-white text-xs font-bold hover:bg-emerald-700"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleVerifyDecision(e.id, 'rejected')}
                        className="px-3 py-1.5 rounded-lg bg-rose-50 text-rose-800 border border-rose-200 text-xs font-bold hover:bg-rose-100"
                      >
                        Reject
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 5: ML Model Diagnostics */}
      {tab === 'models' && mlMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-3">
            <div className="flex items-center gap-2 text-navy font-extrabold text-base">
              <Cpu className="w-5 h-5" /> Module 1: {mlMetrics.issue_classifier?.model_type}
            </div>
            <p className="text-xs text-amber-900 bg-amber-50 p-2.5 rounded-xl border border-amber-200">
              {mlMetrics.issue_classifier?.dataset_notice}
            </p>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                <div className="text-slate-500">Held-Out Test Accuracy</div>
                <div className="text-xl font-extrabold text-navy">
                  {Math.round((mlMetrics.issue_classifier?.test_accuracy || 0) * 100)}%
                </div>
              </div>
              <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                <div className="text-slate-500">Macro F1-Score</div>
                <div className="text-xl font-extrabold text-navy">
                  {mlMetrics.issue_classifier?.test_macro_f1}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                <div className="text-slate-500">Train / Test Samples</div>
                <div className="font-bold text-navy">
                  {mlMetrics.issue_classifier?.train_samples} / {mlMetrics.issue_classifier?.test_samples}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                <div className="text-slate-500">Split Strategy</div>
                <div className="font-bold text-navy">Template-grouped holdout</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-3">
            <div className="flex items-center gap-2 text-navy font-extrabold text-base">
              <IndianRupee className="w-5 h-5" /> Module 3: {mlMetrics.price_estimator?.model_type}
            </div>
            <p className="text-xs text-amber-900 bg-amber-50 p-2.5 rounded-xl border border-amber-200">
              {mlMetrics.price_estimator?.dataset_notice}
            </p>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                <div className="text-slate-500">Test MAE</div>
                <div className="text-xl font-extrabold text-navy">
                  ₹{mlMetrics.price_estimator?.test_mae_inr}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                <div className="text-slate-500">Test R² Score</div>
                <div className="text-xl font-extrabold text-navy">
                  {mlMetrics.price_estimator?.test_r2_score}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                <div className="text-slate-500">Test RMSE</div>
                <div className="font-bold text-navy">₹{mlMetrics.price_estimator?.test_rmse_inr}</div>
              </div>
              <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                <div className="text-slate-500">Train / Test Samples</div>
                <div className="font-bold text-navy">
                  {mlMetrics.price_estimator?.train_samples} / {mlMetrics.price_estimator?.test_samples}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
