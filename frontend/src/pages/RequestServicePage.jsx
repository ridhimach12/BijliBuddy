import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  Clock,
  Cpu,
  ImagePlus,
  IndianRupee,
  Info,
  List,
  Map as MapIcon,
  MapPin,
  Sparkles,
  Star,
} from 'lucide-react';
import { customerApi, mlApi, publicApi, resolveAssetUrl } from '../api/client';
import { useAuth } from '../context/AuthContext';
import {
  COMPLEXITY_OPTIONS,
  SERVICE_CATEGORIES,
  TIME_OF_SERVICE_OPTIONS,
  URGENCY_OPTIONS,
  formatINR,
} from '../constants/delhi';
import LocalityMap from '../components/LocalityMap';
import SafetyBanner from '../components/SafetyBanner';
import { VerificationBadge } from '../components/StatusBadge';
import ReliabilityBreakdownModal from '../components/ReliabilityBreakdownModal';

export default function RequestServicePage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [localities, setLocalities] = useState([]);
  const [form, setForm] = useState({
    description: '',
    selected_category: '',
    urgency: 'normal',
    repair_complexity: '',
    time_of_service: 'morning',
    locality: 'Saket',
    zone: 'South Delhi',
    address: 'B-42, Press Enclave Road, Saket',
    latitude: 28.5245,
    longitude: 77.2066,
    image_path: null,
  });

  const [imageUploading, setImageUploading] = useState(false);
  const [imageDisclaimer, setImageDisclaimer] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  // Results state
  const [analysisPayload, setAnalysisPayload] = useState(null); // { service_request?, classification, price_estimate, matching }
  const [viewMode, setViewMode] = useState('split'); // 'split' | 'list' | 'map'
  const [selectedElec, setSelectedElec] = useState(null);
  const [bookingNotes, setBookingNotes] = useState('');
  const [scheduledSlot, setScheduledSlot] = useState('Within 1 Hour (Priority)');
  const [bookingLoading, setBookingLoading] = useState(false);
  const [modalReliability, setModalReliability] = useState(null);

  useEffect(() => {
    publicApi.localities().then((res) => {
      setLocalities(res.localities || []);
    });
    if (user?.role === 'customer') {
      customerApi
        .getProfile()
        .then((prof) => {
          setForm((prev) => ({
            ...prev,
            locality: prof.locality || prev.locality,
            zone: prof.zone || prev.zone,
            address: prof.address || prev.address,
            latitude: prof.latitude || prev.latitude,
            longitude: prof.longitude || prev.longitude,
          }));
        })
        .catch(() => {});
    }
  }, [user]);

  const handleLocalityChange = (locName) => {
    const loc = localities.find((l) => l.name === locName);
    if (!loc) return;
    setForm((prev) => ({
      ...prev,
      locality: loc.name,
      zone: loc.zone,
      latitude: loc.latitude,
      longitude: loc.longitude,
    }));
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!user || user.role !== 'customer') {
      setError('Please sign in as a customer to upload reference photos.');
      return;
    }
    setImageUploading(true);
    setError('');
    try {
      const res = await customerApi.uploadImage(file);
      setForm((prev) => ({ ...prev, image_path: res.image_path }));
      setImageDisclaimer(res.disclaimer);
    } catch (err) {
      setError(err.response?.data?.detail || 'Image upload failed.');
    } finally {
      setImageUploading(false);
    }
  };

  const handleAnalyzeAndMatch = async (e) => {
    e.preventDefault();
    setError('');
    if (form.description.trim().length < 5) {
      setError('Please describe your electrical issue in at least a few words.');
      return;
    }
    setAnalyzing(true);
    try {
      if (user?.role === 'customer') {
        const res = await customerApi.createServiceRequest({
          description: form.description,
          selected_category: form.selected_category || null,
          urgency: form.urgency,
          repair_complexity: form.repair_complexity || null,
          time_of_service: form.time_of_service,
          address: form.address,
          locality: form.locality,
          latitude: form.latitude,
          longitude: form.longitude,
          image_path: form.image_path,
        });
        setAnalysisPayload(res);
        setSelectedElec(res.matching?.recommendations?.[0] || null);
      } else {
        // Guest preview runs ML endpoints without persisting customer ServiceRequest
        const triage = await mlApi.analyzeIssue({
          description: form.description,
          urgency: form.urgency,
          locality: form.locality,
          zone: form.zone,
          time_of_service: form.time_of_service,
          repair_complexity: form.repair_complexity || null,
        });
        const activeCategory = form.selected_category || triage.classification.predicted_category;
        const priceEstimate =
          form.selected_category || form.repair_complexity
            ? await mlApi.estimatePrice({
                service_category: activeCategory,
                repair_complexity: form.repair_complexity || triage.classification.suggested_complexity,
                location_zone: form.zone,
                urgency: form.urgency,
                time_of_service: form.time_of_service,
                estimated_duration: triage.classification.estimated_duration_mins,
              })
            : triage.price_estimate;
        const matching = await mlApi.matchElectricians({
          service_category: activeCategory,
          latitude: form.latitude,
          longitude: form.longitude,
          urgency: form.urgency,
          top_k: 5,
        });
        setAnalysisPayload({
          service_request: null,
          classification: triage.classification,
          price_estimate: priceEstimate,
          matching,
        });
        setSelectedElec(matching?.recommendations?.[0] || null);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to run AI diagnostics and electrician matching.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleConfirmBooking = async () => {
    if (!user || user.role !== 'customer') {
      navigate('/login');
      return;
    }
    if (!analysisPayload?.service_request?.id || !selectedElec) {
      setError('Please analyze your issue and select an available electrician first.');
      return;
    }
    setBookingLoading(true);
    setError('');
    try {
      const slotMeta = TIME_OF_SERVICE_OPTIONS.find((t) => t.value === form.time_of_service);
      const res = await customerApi.createBooking({
        service_request_id: analysisPayload.service_request.id,
        electrician_id: selectedElec.electrician_id,
        scheduled_slot: scheduledSlot,
        time_slot_bucket: slotMeta?.slotBucket || 'Morning (6AM-12PM)',
        customer_notes: bookingNotes || null,
      });
      navigate(`/bookings/${res.booking.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Booking request failed.');
    } finally {
      setBookingLoading(false);
    }
  };

  const openReliabilityDetails = async (elec) => {
    try {
      const detail = await publicApi.electricianDetail(elec.electrician_id);
      setModalReliability({ name: elec.full_name, reliability: detail.reliability });
    } catch {}
  };

  const recs = analysisPayload?.matching?.recommendations || [];
  const clf = analysisPayload?.classification;
  const price = analysisPayload?.price_estimate;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="space-y-1">
        <span className="text-xs font-extrabold uppercase tracking-wider text-navy/60">
          AI Issue Diagnostics & Hyperlocal Matching
        </span>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-navy">Request an Electrical Service</h1>
        <p className="text-sm text-slate-600">
          Describe the fault, verify your Delhi locality on the map, review AI price ranges, and book a matched
          technician.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-300 text-rose-900 text-sm font-medium">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Service Request Form */}
        <form
          onSubmit={handleAnalyzeAndMatch}
          className="lg:col-span-5 bg-white rounded-3xl p-6 border border-[#E8E4D8] shadow-card space-y-4"
        >
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-navy">1. Describe Your Electrical Problem *</label>
            <textarea
              rows={3}
              required
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="e.g., Main MCB trips repeatedly whenever geyser turns on, or bedroom switchboard sparking..."
              className="w-full p-3 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm focus:outline-none focus:ring-2 focus:ring-navy"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Service Category (Optional Override)</label>
              <select
                value={form.selected_category}
                onChange={(e) => setForm({ ...form, selected_category: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-xs font-medium"
              >
                <option value="">Auto-detect via AI Classifier</option>
                {SERVICE_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Urgency Level</label>
              <select
                value={form.urgency}
                onChange={(e) => setForm({ ...form, urgency: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-xs font-medium"
              >
                {URGENCY_OPTIONS.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Repair Complexity</label>
              <select
                value={form.repair_complexity}
                onChange={(e) => setForm({ ...form, repair_complexity: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-xs font-medium"
              >
                <option value="">Auto-infer from issue</option>
                {COMPLEXITY_OPTIONS.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-navy">Preferred Time Window</label>
              <select
                value={form.time_of_service}
                onChange={(e) => setForm({ ...form, time_of_service: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-xs font-medium"
              >
                {TIME_OF_SERVICE_OPTIONS.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1.5 pt-2 border-t border-slate-100">
            <label className="text-xs font-bold text-navy">2. Delhi Locality & Service Address</label>
            <select
              value={form.locality}
              onChange={(e) => handleLocalityChange(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm font-medium"
            >
              {localities.map((l) => (
                <option key={l.name} value={l.name}>
                  {l.name} — {l.zone}
                </option>
              ))}
            </select>
            <input
              type="text"
              required
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              placeholder="House/Flat No, Floor, Landmark"
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-[#FAF9F5] text-sm"
            />
          </div>

          {/* Interactive Location Picker Map */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-[11px] text-slate-500 font-medium">
              <span>Service Pin ({form.latitude.toFixed(4)}, {form.longitude.toFixed(4)})</span>
              <span>Click map to adjust pin</span>
            </div>
            <LocalityMap
              centerLat={form.latitude}
              centerLon={form.longitude}
              customerLabel={`${form.locality} Service Pin`}
              interactivePicker
              onPickLocation={(lat, lon) => setForm((prev) => ({ ...prev, latitude: lat, longitude: lon }))}
              heightClass="h-48"
            />
          </div>

          {/* Optional Image Upload */}
          <div className="space-y-1.5 pt-2 border-t border-slate-100">
            <label className="text-xs font-bold text-navy flex items-center gap-1.5">
              <ImagePlus className="w-4 h-4" /> Optional Reference Photo (For Electrician Only)
            </label>
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.webp"
              onChange={handleImageUpload}
              disabled={imageUploading}
              className="block w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-cream file:text-navy hover:file:bg-electric/40"
            />
            {form.image_path && (
              <div className="flex items-center gap-3 p-2 rounded-xl bg-[#FAF9F5] border border-[#E8E4D8]">
                <img
                  src={resolveAssetUrl(form.image_path)}
                  alt="Uploaded reference"
                  className="w-12 h-12 rounded-lg object-cover border"
                />
                <div className="text-[11px] text-slate-600">
                  {imageDisclaimer || 'Reference photo attached for your electrician. AI does NOT diagnose live hazards from images.'}
                </div>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={analyzing}
            className="w-full py-3.5 rounded-xl bg-navy hover:bg-navy-light text-white font-extrabold text-sm inline-flex items-center justify-center gap-2 shadow transition"
          >
            <Sparkles className="w-4 h-4 text-electric" />
            {analyzing ? 'Classifying, Estimating & Matching...' : 'Analyze Issue & Find Nearby Electricians'}
          </button>
        </form>

        {/* Right Panel: AI Classification + Price Estimate + Map/List Recommendations */}
        <div className="lg:col-span-7 space-y-6">
          {!analysisPayload ? (
            <div className="bg-white rounded-3xl p-10 border border-[#E8E4D8] shadow-card text-center space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-electric/30 text-navy flex items-center justify-center mx-auto">
                <Cpu className="w-7 h-7" />
              </div>
              <h2 className="text-xl font-extrabold text-navy">Ready for AI Issue Triage & Matching</h2>
              <p className="text-sm text-slate-600 max-w-md mx-auto">
                Enter your electrical issue on the left to run our TF-IDF Classifier, Random Forest INR Estimator,
                safety hazard check, and Haversine matching engine.
              </p>
              <SafetyBanner compact />
            </div>
          ) : (
            <>
              {/* Hazard Warning Banner */}
              <SafetyBanner hazardAssessment={clf?.hazard_assessment} />

              {/* AI Classification & Price Range Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold uppercase tracking-wider text-navy/60">
                      AI Issue Classification
                    </span>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      {Math.round((clf?.confidence_score || 0) * 100)}% Confidence
                    </span>
                  </div>
                  <div className="text-lg font-extrabold text-navy">{clf?.predicted_category}</div>
                  <div className="text-xs text-slate-600">
                    Suggested Service: <strong>{clf?.suggested_service_type}</strong>
                  </div>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {clf?.top_alternatives?.map((alt) => (
                      <span
                        key={alt.category}
                        className="text-[11px] px-2 py-0.5 rounded bg-[#FAF9F5] border border-[#E8E4D8] text-slate-600"
                      >
                        {alt.category}: {Math.round(alt.probability * 100)}%
                      </span>
                    ))}
                  </div>
                  <p className="text-[10px] text-slate-400">{clf?.dataset_notice}</p>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-[#E8E4D8] shadow-card space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold uppercase tracking-wider text-navy/60">
                      ML Price Estimate (INR)
                    </span>
                    <IndianRupee className="w-4 h-4 text-navy" />
                  </div>
                  <div className="text-2xl font-extrabold text-navy">
                    {formatINR(price?.lower_estimate_inr)} – {formatINR(price?.upper_estimate_inr)}
                  </div>
                  <div className="text-xs text-slate-700">
                    Predicted Baseline: <strong>{formatINR(price?.predicted_base_price_inr)}</strong> ({form.zone})
                  </div>
                  <div className="flex items-start gap-1.5 text-[11px] text-amber-900 bg-amber-50 border border-amber-200 rounded-xl p-2">
                    <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    <span>{price?.disclaimer}</span>
                  </div>
                </div>
              </div>

              {/* View Mode Switcher & Map */}
              <div className="bg-white rounded-3xl p-5 border border-[#E8E4D8] shadow-card space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-extrabold text-navy">
                      Top {recs.length} Matched Electricians Nearby
                    </h2>
                    <p className="text-xs text-slate-500">
                      Ranked by availability, Haversine distance, skills, rating, acceptance & completion rate
                    </p>
                  </div>
                  <div className="flex items-center gap-1 bg-[#FAF9F5] p-1 rounded-xl border border-[#E8E4D8]">
                    {[
                      { id: 'split', label: 'Map + List' },
                      { id: 'map', label: 'Map Only', icon: MapIcon },
                      { id: 'list', label: 'List Only', icon: List },
                    ].map((m) => (
                      <button
                        type="button"
                        key={m.id}
                        onClick={() => setViewMode(m.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                          viewMode === m.id ? 'bg-navy text-electric' : 'text-slate-600 hover:text-navy'
                        }`}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                </div>

                {(viewMode === 'split' || viewMode === 'map') && (
                  <LocalityMap
                    centerLat={form.latitude}
                    centerLon={form.longitude}
                    customerLabel={`Your Location (${form.locality})`}
                    electricians={recs}
                    selectedElectricianId={selectedElec?.electrician_id}
                    onSelectElectrician={(elec) => setSelectedElec(elec)}
                    heightClass="h-72"
                  />
                )}

                {(viewMode === 'split' || viewMode === 'list') && (
                  <div className="space-y-3">
                    {recs.map((elec, idx) => {
                      const isSelected = selectedElec?.electrician_id === elec.electrician_id;
                      return (
                        <div
                          key={elec.electrician_id}
                          onClick={() => setSelectedElec(elec)}
                          className={`rounded-2xl p-4 border-2 transition cursor-pointer space-y-3 ${
                            isSelected
                              ? 'border-navy bg-[#FAF9F5]'
                              : 'border-[#E8E4D8] bg-white hover:border-navy/40'
                          }`}
                        >
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div className="space-y-1">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="text-xs font-extrabold px-2 py-0.5 rounded-md bg-navy text-electric">
                                  #{idx + 1} • {elec.match_score}% Match
                                </span>
                                <Link
                                  to={`/electricians/${elec.electrician_id}`}
                                  onClick={(ev) => ev.stopPropagation()}
                                  className="font-extrabold text-navy text-base hover:underline"
                                >
                                  {elec.full_name}
                                </Link>
                                <VerificationBadge status={elec.verification_status} />
                              </div>
                              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
                                <span className="inline-flex items-center gap-1">
                                  <MapPin className="w-3.5 h-3.5 text-navy" />
                                  {elec.locality} ({elec.distance_km} km)
                                </span>
                                <span className="inline-flex items-center gap-1">
                                  <Clock className="w-3.5 h-3.5 text-navy" />
                                  ETA ~{elec.estimated_arrival_mins} mins
                                </span>
                                <span className="inline-flex items-center gap-1 font-semibold text-navy">
                                  <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                                  {elec.rating ? `${elec.rating} (${elec.review_count})` : `New (${elec.smoothed_rating}★ prior)`}
                                </span>
                              </div>
                            </div>

                            <div className="text-right space-y-1">
                              <span
                                className={`inline-block text-xs font-bold px-2.5 py-1 rounded-full ${
                                  elec.is_available
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : 'bg-slate-200 text-slate-700'
                                }`}
                              >
                                {elec.availability_label}
                              </span>
                              <div className="text-xs font-bold text-navy">
                                Visit Fee: {formatINR(elec.base_visit_fee_inr)}
                              </div>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] bg-white rounded-xl p-2.5 border border-[#E8E4D8]">
                            <div>
                              <span className="text-slate-500">Skills Match:</span>{' '}
                              <strong className="text-navy">{elec.skills_match_pct}%</strong>
                            </div>
                            <div>
                              <span className="text-slate-500">Acceptance:</span>{' '}
                              <strong className="text-navy">{elec.acceptance_rate}%</strong>
                            </div>
                            <div>
                              <span className="text-slate-500">Completion:</span>{' '}
                              <strong className="text-navy">{elec.completion_rate}%</strong>
                            </div>
                            <div>
                              <button
                                type="button"
                                onClick={(ev) => {
                                  ev.stopPropagation();
                                  openReliabilityDetails(elec);
                                }}
                                className="text-navy font-bold underline"
                              >
                                Reliability: {elec.reliability_score}/100
                              </button>
                            </div>
                          </div>

                          <ul className="text-xs text-slate-600 space-y-1 list-disc list-inside">
                            {elec.explanation_reasons?.map((r, rIdx) => (
                              <li key={rIdx}>{r}</li>
                            ))}
                          </ul>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Booking Request Action Box */}
                {selectedElec && (
                  <div className="bg-navy text-ivory rounded-2xl p-5 space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <div className="text-xs uppercase font-bold text-electric">Selected Electrician</div>
                        <div className="text-lg font-extrabold text-white">
                          {selectedElec.full_name} — {selectedElec.locality} ({selectedElec.distance_km} km)
                        </div>
                      </div>
                      <div className="text-xs text-ivory/80">
                        AI Baseline Est: <strong>{formatINR(price?.predicted_base_price_inr)}</strong> (final quote set on acceptance)
                      </div>
                    </div>

                    {!user || user.role !== 'customer' ? (
                      <div className="flex flex-wrap items-center justify-between gap-3 bg-white/10 rounded-xl p-3 text-xs">
                        <span>Sign in with a Customer account to send a real booking request.</span>
                        <Link
                          to="/login"
                          className="px-4 py-2 rounded-lg bg-electric text-navy font-extrabold"
                        >
                          Sign In to Book
                        </Link>
                      </div>
                    ) : !selectedElec.is_available ? (
                      <div className="p-3 rounded-xl bg-amber-500/20 border border-amber-400 text-xs text-amber-100">
                        This electrician is currently unavailable. Please choose an available candidate above.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div>
                            <label className="text-xs font-semibold text-ivory/80 block mb-1">Preferred Arrival Slot</label>
                            <input
                              type="text"
                              value={scheduledSlot}
                              onChange={(e) => setScheduledSlot(e.target.value)}
                              className="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-sm text-white placeholder-white/50"
                            />
                          </div>
                          <div>
                            <label className="text-xs font-semibold text-ivory/80 block mb-1">Gate / Access Notes</label>
                            <input
                              type="text"
                              value={bookingNotes}
                              onChange={(e) => setBookingNotes(e.target.value)}
                              placeholder="e.g., Intercom code, landmark..."
                              className="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-sm text-white placeholder-white/50"
                            />
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={handleConfirmBooking}
                          disabled={bookingLoading}
                          className="w-full py-3 rounded-xl bg-electric hover:bg-electric-hover text-navy font-extrabold text-sm inline-flex items-center justify-center gap-2 transition"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                          {bookingLoading ? 'Sending Booking Request...' : `Confirm Booking Request with ${selectedElec.full_name}`}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {modalReliability && (
        <ReliabilityBreakdownModal
          electricianName={modalReliability.name}
          reliability={modalReliability.reliability}
          onClose={() => setModalReliability(null)}
        />
      )}
    </div>
  );
}
