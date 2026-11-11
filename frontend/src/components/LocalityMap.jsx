import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

function createPinIcon({ bg, border, textColor, label }) {
  return L.divIcon({
    className: 'bijlibuddy-map-pin',
    html: `<div style="
      display:flex;align-items:center;justify-content:center;
      min-width:30px;height:30px;padding:0 7px;
      border-radius:9999px;background:${bg};color:${textColor};
      border:2.5px solid ${border};font-weight:800;font-size:11px;
      box-shadow:0 4px 10px rgba(15,30,54,0.28);white-space:nowrap;">
      ${label}
    </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
}

export default function LocalityMap({
  centerLat = 28.5677,
  centerLon = 77.21,
  zoom = 12,
  customerLabel = 'Service Location',
  electricians = [],
  selectedElectricianId = null,
  onSelectElectrician = null,
  interactivePicker = false,
  onPickLocation = null,
  heightClass = 'h-80',
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const layerGroupRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: [centerLat, centerLon],
      zoom,
      scrollWheelZoom: false,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);

    layerGroupRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      layerGroupRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const handleClick = (e) => {
      if (interactivePicker && onPickLocation) {
        onPickLocation(Number(e.latlng.lat.toFixed(5)), Number(e.latlng.lng.toFixed(5)));
      }
    };
    map.on('click', handleClick);
    return () => {
      map.off('click', handleClick);
    };
  }, [interactivePicker, onPickLocation]);

  useEffect(() => {
    const map = mapRef.current;
    const group = layerGroupRef.current;
    if (!map || !group) return;

    group.clearLayers();

    const custIcon = createPinIcon({
      bg: '#0F1E36',
      border: '#FACC15',
      textColor: '#FACC15',
      label: 'YOU',
    });

    const custMarker = L.marker([centerLat, centerLon], { icon: custIcon }).bindPopup(
      `<div style="font-size:12px;"><strong>${customerLabel}</strong><br/>Lat: ${centerLat.toFixed(4)}, Lon: ${centerLon.toFixed(4)}</div>`
    );
    custMarker.addTo(group);

    const boundsPoints = [[centerLat, centerLon]];

    electricians.forEach((elec, idx) => {
      if (typeof elec.latitude !== 'number' || typeof elec.longitude !== 'number') return;
      const isSelected = selectedElectricianId === elec.electrician_id || selectedElectricianId === elec.id;
      const isAvail = elec.is_available;

      const icon = createPinIcon({
        bg: isSelected ? '#FACC15' : isAvail ? '#10B981' : '#94A3B8',
        border: '#0F1E36',
        textColor: isSelected ? '#0F1E36' : '#FFFFFF',
        label: elec.match_score ? `#${idx + 1} ${Math.round(elec.match_score)}%` : `#${idx + 1}`,
      });

      const marker = L.marker([elec.latitude, elec.longitude], { icon });
      const verText = elec.is_verified ? 'Admin Verified' : elec.verification_status;
      const distText = elec.distance_km !== undefined ? `${elec.distance_km} km • ~${elec.estimated_arrival_mins}m ETA` : elec.locality;

      marker.bindPopup(`
        <div style="min-width:170px;font-size:12px;line-height:1.45;">
          <div style="font-weight:700;color:#0F1E36;font-size:13px;">${elec.full_name}</div>
          <div style="color:#475569;">${elec.locality} • ${verText}</div>
          <div style="margin-top:4px;font-weight:600;">${distText}</div>
          ${elec.match_score ? `<div>Match Score: <strong>${elec.match_score}/100</strong></div>` : ''}
        </div>
      `);

      marker.on('click', () => {
        if (onSelectElectrician) onSelectElectrician(elec);
      });

      marker.addTo(group);
      boundsPoints.push([elec.latitude, elec.longitude]);
    });

    if (boundsPoints.length > 1) {
      map.fitBounds(boundsPoints, { padding: [36, 36], maxZoom: 13 });
    } else {
      map.setView([centerLat, centerLon], zoom);
    }
  }, [centerLat, centerLon, electricians, selectedElectricianId, customerLabel, zoom, onSelectElectrician]);

  return (
    <div className="relative rounded-2xl overflow-hidden border border-[#E5E0D0] shadow-card">
      <div ref={containerRef} className={`w-full ${heightClass}`} />
      {interactivePicker && (
        <div className="absolute bottom-3 left-3 z-[400] bg-navy/90 text-ivory text-xs px-3 py-1.5 rounded-full shadow">
          Click anywhere on the Delhi map to fine-tune pin coordinates
        </div>
      )}
    </div>
  );
}
