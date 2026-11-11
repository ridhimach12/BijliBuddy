import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Award,
  BarChart3,
  CheckCircle2,
  Cpu,
  IndianRupee,
  MapPin,
  ShieldCheck,
  Sparkles,
  Wrench,
  Zap,
} from 'lucide-react';
import { mlApi, publicApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { formatINR } from '../constants/delhi';
import SafetyBanner from '../components/SafetyBanner';

export default function LandingPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  const [categories, setCategories] = useState([]);
  const [sampleText, setSampleText] = useState('Main MCB tripping repeatedly when AC starts in Saket');
  const [triageLoading, setTriageLoading] = useState(false);
  const [triageResult, setTriageResult] = useState(null);
  const [demoLoading, setDemoLoading] = useState('');

  useEffect(() => {
    publicApi
      .categories()
      .then((res) => setCategories(res.categories || []))
      .catch(() => {});
  }, []);

  const handleLiveTriage = async (e) => {
    e.preventDefault();
    if (!sampleText.trim()) return;
    setTriageLoading(true);
    try {
      const res = await mlApi.analyzeIssue({
        description: sampleText,
        locality: 'Saket',
        urgency: 'normal',
        time_of_service: 'morning',
      });
      setTriageResult(res);
    } catch {
      setTriageResult(null);
    } finally {
      setTriageLoading(false);
    }
  };

  const handleQuickDemoLogin = async (email, targetPath) => {
    setDemoLoading(email);
    try {
      await login(email, 'Demo@1234');
      navigate(targetPath);
    } finally {
      setDemoLoading('');
    }
  };

  const goPrimaryCta = () => {
    if (!user) return navigate('/request-service');
    if (user.role === 'customer') return navigate('/request-service');
    if (user.role === 'electrician') return navigate('/electrician/dashboard');
    return navigate('/admin/dashboard');
  };

  return (
    <div className="space-y-20 pb-12">
      {/* Hero Section */}
      <section className="bg-navy text-ivory relative overflow-hidden">
        <div className="absolute inset-0 opacity-15 pointer-events-none bg-[radial-gradient(circle_at_top_right,#FACC15,transparent_45%)]" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-20 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center relative">
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 border border-white/15 text-xs font-semibold text-electric">
              <Sparkles className="w-3.5 h-3.5" />
              Hyperlocal AI Electrician Marketplace • Delhi NCR
            </div>
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-[1.12] text-white">
              Trusted neighbourhood electricians,{' '}
              <span className="text-electric">intelligently matched</span> in minutes.
            </h1>
            <p className="text-base sm:text-lg text-ivory/80 max-w-2xl leading-relaxed">
              Describe your electrical problem in plain words. BijliBuddy classifies the fault, detects safety
              hazards, estimates a transparent INR baseline price range, and ranks verified nearby Delhi
              technicians using explainable AI.
            </p>

            <div className="flex flex-wrap gap-3 pt-1">
              <button
                onClick={goPrimaryCta}
                className="px-6 py-3.5 rounded-xl bg-electric hover:bg-electric-hover text-navy font-extrabold text-sm inline-flex items-center gap-2 shadow-lg transition-all"
              >
                {user?.role === 'electrician'
                  ? 'Open Electrician Workspace'
                  : user?.role === 'admin'
                  ? 'Open Admin Console'
                  : 'Diagnose Issue & Book Electrician'}
                <ArrowRight className="w-4 h-4" />
              </button>
              <Link
                to="/electricians"
                className="px-6 py-3.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-sm border border-white/15 transition-colors"
              >
                Browse Delhi Electricians
              </Link>
            </div>

            {/* Hackathon Demo Role Quick Switcher */}
            <div className="pt-4 border-t border-white/10 space-y-2.5">
              <div className="text-xs font-semibold uppercase tracking-wider text-ivory/65">
                Instant Demo Login (Synthetic Demonstration Accounts)
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleQuickDemoLogin('ananya.sharma@bijlibuddy.demo', '/customer/dashboard')}
                  disabled={!!demoLoading}
                  className="px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-semibold border border-white/15 transition"
                >
                  {demoLoading === 'ananya.sharma@bijlibuddy.demo' ? 'Signing in...' : 'Demo Customer (Saket)'}
                </button>
                <button
                  onClick={() => handleQuickDemoLogin('ramesh.verma@bijlibuddy.demo', '/electrician/dashboard')}
                  disabled={!!demoLoading}
                  className="px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-semibold border border-white/15 transition"
                >
                  {demoLoading === 'ramesh.verma@bijlibuddy.demo' ? 'Signing in...' : 'Demo Electrician (Ramesh)'}
                </button>
                <button
                  onClick={() => handleQuickDemoLogin('admin@bijlibuddy.demo', '/admin/dashboard')}
                  disabled={!!demoLoading}
                  className="px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-semibold border border-white/15 transition"
                >
                  {demoLoading === 'admin@bijlibuddy.demo' ? 'Signing in...' : 'Demo Admin Console'}
                </button>
              </div>
            </div>
          </div>

          {/* Live AI Triage Sandbox Widget */}
          <div className="lg:col-span-5 bg-white text-navy rounded-3xl p-6 shadow-elevated border border-[#E8E4D8] space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-electric/30 text-navy">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="font-bold text-base">Live AI Fault & INR Estimator</h2>
                  <p className="text-xs text-slate-500">TF-IDF Classifier + Random Forest Pricer</p>
                </div>
              </div>
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
                Live API
              </span>
            </div>

            <form onSubmit={handleLiveTriage} className="space-y-3">
              <textarea
                rows={3}
                value={sampleText}
                onChange={(e) => setSampleText(e.target.value)}
                placeholder="e.g., Bedroom switchboard sparking and smelling burnt..."
                className="w-full rounded-xl border border-slate-200 bg-[#FAF9F5] p-3 text-sm focus:outline-none focus:ring-2 focus:ring-navy"
              />
              <div className="flex flex-wrap gap-1.5">
                {[
                  'Ceiling fan humming and running slow',
                  'Switchboard sparking with burning smell',
                  'Inverter not charging battery',
                ].map((preset) => (
                  <button
                    type="button"
                    key={preset}
                    onClick={() => setSampleText(preset)}
                    className="text-[11px] px-2.5 py-1 rounded-full bg-cream hover:bg-electric/40 text-navy font-medium transition"
                  >
                    {preset}
                  </button>
                ))}
              </div>
              <button
                type="submit"
                disabled={triageLoading}
                className="w-full py-2.5 rounded-xl bg-navy hover:bg-navy-light text-white font-bold text-sm transition"
              >
                {triageLoading ? 'Running ML Inference...' : 'Analyze Problem Now'}
              </button>
            </form>

            {triageResult && (
              <div className="space-y-3 pt-2 border-t border-slate-100">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                    <div className="text-[11px] text-slate-500 font-medium">Predicted Category</div>
                    <div className="font-bold text-sm text-navy mt-0.5">
                      {triageResult.classification.predicted_category}
                    </div>
                    <div className="text-[11px] font-semibold text-emerald-700 mt-0.5">
                      {Math.round(triageResult.classification.confidence_score * 100)}% confidence
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                    <div className="text-[11px] text-slate-500 font-medium">ML Price Range (Saket)</div>
                    <div className="font-extrabold text-sm text-navy mt-0.5">
                      {formatINR(triageResult.price_estimate.lower_estimate_inr)} –{' '}
                      {formatINR(triageResult.price_estimate.upper_estimate_inr)}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Base: {formatINR(triageResult.price_estimate.predicted_base_price_inr)}
                    </div>
                  </div>
                </div>

                {triageResult.classification.hazard_assessment?.hazard_detected && (
                  <SafetyBanner hazardAssessment={triageResult.classification.hazard_assessment} />
                )}

                <Link
                  to="/request-service"
                  className="block w-full text-center py-2.5 rounded-xl bg-electric hover:bg-electric-hover text-navy font-bold text-xs transition"
                >
                  Continue to Find Top 5 Electricians →
                </Link>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 5 AI/ML Architecture Pillars */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="max-w-2xl">
          <span className="text-xs font-extrabold uppercase tracking-wider text-navy/60">
            Engineering Architecture
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-navy mt-1">
            Five Transparent AI & Statistical Engines Under the Hood
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[
            {
              icon: Cpu,
              title: '1. TF-IDF + Logistic Regression Triage',
              desc: 'Classifies free-text descriptions across 8 electrical categories with confidence scores and triggers emergency safety warnings for sparks or shock.',
            },
            {
              icon: MapPin,
              title: '2. Explainable Haversine Matching',
              desc: 'Ranks available nearby electricians via exact Haversine distance, skill fit, ETA, rating, acceptance & completion rates. Unavailable workers never outrank available ones.',
            },
            {
              icon: IndianRupee,
              title: '3. Random Forest INR Price Estimator',
              desc: 'Predicts labour baseline ranges across category, complexity, Delhi zone, urgency, and time slot — clearly distinct from the electrician’s final quotation.',
            },
            {
              icon: BarChart3,
              title: '4. Baseline Statistical Demand Forecast',
              desc: 'Aggregates bookings by Delhi locality, weekday, time slot, and category using recency-weighted moving averages & Poisson intervals.',
            },
            {
              icon: Award,
              title: '5. Bayesian Reliability Score',
              desc: 'Scores verified completed jobs, acceptance, cancellation & on-time rates with Bayesian smoothing so new electricians are treated fairly.',
            },
            {
              icon: ShieldCheck,
              title: '6. Admin-Verified Trust & Safety',
              desc: 'Verification badges are granted strictly by Admin credential review. Urgent hazards display non-diagnostic safety steps and 112 / DISCOM helplines.',
            },
          ].map((item, i) => (
            <div key={i} className="bg-white rounded-2xl p-6 border border-[#E8E4D8] shadow-card space-y-3">
              <div className="w-10 h-10 rounded-xl bg-navy text-electric flex items-center justify-center">
                <item.icon className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-navy text-base">{item.title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Supported Electrical Services */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <span className="text-xs font-extrabold uppercase tracking-wider text-navy/60">
              Service Coverage
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-navy mt-1">
              8 Household Electrical Categories
            </h2>
          </div>
          <Link to="/request-service" className="text-sm font-bold text-navy hover:underline inline-flex items-center gap-1">
            Request Any Service <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {categories.map((c) => (
            <div key={c.id} className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card flex flex-col justify-between gap-3">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="p-2 rounded-xl bg-electric/25 text-navy">
                    <Wrench className="w-4 h-4" />
                  </span>
                  <span className="text-xs font-bold text-navy bg-[#FAF9F5] px-2.5 py-1 rounded-full border border-[#E8E4D8]">
                    From {formatINR(c.base_price_inr)}
                  </span>
                </div>
                <h3 className="font-bold text-navy text-base">{c.name}</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{c.description}</p>
              </div>
              <div className="text-[11px] font-semibold text-slate-500 pt-2 border-t border-slate-100 flex justify-between">
                <span>Est. ~{c.estimated_duration_mins} mins</span>
                <span className="capitalize">Risk: {c.safety_level}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Safety Banner on Landing */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SafetyBanner compact />
      </section>
    </div>
  );
}
