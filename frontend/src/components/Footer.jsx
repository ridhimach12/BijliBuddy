import React from 'react';
import { PhoneCall, Zap } from 'lucide-react';
import { resolveBackendOrigin } from '../api/client';

export default function Footer() {
  const docsUrl = `${resolveBackendOrigin() || 'http://localhost:8000'}/docs`;

  return (
    <footer className="bg-navy text-ivory/85 border-t border-white/10 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 grid grid-cols-1 md:grid-cols-3 gap-8 text-sm">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-electric text-navy flex items-center justify-center">
              <Zap className="w-4 h-4 fill-navy" />
            </div>
            <span className="font-extrabold text-white text-base">BIJLIBUDDY</span>
          </div>
          <p className="text-xs text-ivory/70 leading-relaxed">
            Hyperlocal AI-powered electrician marketplace connecting Delhi households with independent local
            technicians through transparent INR estimates and explainable matching.
          </p>
        </div>

        <div className="space-y-2">
          <h4 className="font-bold text-white text-xs uppercase tracking-wider">Electrical Safety & Emergency</h4>
          <p className="text-xs text-ivory/75 flex items-center gap-1.5">
            <PhoneCall className="w-3.5 h-3.5 text-electric" />
            National Emergency: <strong>112</strong> • Fire: <strong>101</strong>
          </p>
          <p className="text-xs text-ivory/70">
            BSES Rajdhani: 19123 • BSES Yamuna: 19122 • Tata Power DDL: 19124
          </p>
          <p className="text-[11px] text-amber-200/80">
            Never attempt live wiring repairs yourself. Verification badges are strictly Admin-approved.
          </p>
        </div>

        <div className="space-y-2">
          <h4 className="font-bold text-white text-xs uppercase tracking-wider">Engineering Transparency</h4>
          <p className="text-xs text-ivory/70">
            Starter ML datasets (issue classifier & pricing regressor), demo accounts, and payment records are
            explicitly labeled synthetic demonstration data.
          </p>
          <a
            href={docsUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-block text-xs font-semibold text-electric hover:underline"
          >
            Open FastAPI Swagger API Docs →
          </a>
        </div>
      </div>
    </footer>
  );
}
