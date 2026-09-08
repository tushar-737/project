import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { CircleMarker, MapContainer, Marker, Polyline, Popup, TileLayer, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useApi } from '../hooks/useApi';
import { useTranslation } from '../i18n';
import { Card, ErrorBox, PageHeader, RiskBadge, RoadBadge, Spinner, StatusPill } from '../components/ui';
import { fmtNum, fmtDate, timeAgo } from '../utils/format';
import { REPORT_TYPE_META, RISK_LEVELS, RISK_META, ROAD_META, STATES } from '../utils/risk';

const NE_CENTER = [25.85, 93.1];

function riskIcon(level) {
  const color = RISK_META[level]?.color || '#64748b';
  return L.divIcon({
    className: '',
    html: `<div class="risk-pin risk-pin--${(level || '').toLowerCase()}" style="background:${color}"><span>!</span></div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 28],
    popupAnchor: [0, -26],
  });
}

function reportIcon(type, status) {
  const meta = REPORT_TYPE_META[type] || REPORT_TYPE_META.OTHER;
  const border = status === 'VERIFIED' ? '#16a34a' : status === 'REJECTED' ? '#94a3b8' : '#f59e0b';
  return L.divIcon({
    className: '',
    html: `<div class="report-pin" style="background:${border}">${meta.icon}</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  });
}

function FocusController({ focusId, zones }) {
  const map = useMap();
  useEffect(() => {
    if (!focusId || !zones?.length) return;
    const zone = zones.find((z) => z.location_id === focusId);
    if (zone) {
      map.flyTo([zone.latitude, zone.longitude], 10, { duration: 1.2 });
    }
  }, [focusId, zones, map]);
  return null;
}

function RiskPopup({ z }) {
  const { t } = useTranslation();
  return (
    <div className="w-60 text-slate-800">
      <div className="mb-2 flex items-center justify-between gap-2 border-b border-slate-100 pb-2">
        <div>
          <p className="text-sm font-extrabold text-govblue-950">{z.name}</p>
          <p className="text-[11px] text-slate-500">
            {z.district}, {z.state}
          </p>
        </div>
        <RiskBadge level={z.risk_level} />
      </div>
      <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs">
        <dt className="text-slate-400">{t('env.rainfall')}</dt>
        <dd className="text-right font-bold text-blue-700">{fmtNum(z.rainfall, 1)} mm</dd>
        <dt className="text-slate-400">{t('env.soilMoisture')}</dt>
        <dd className="text-right font-bold text-emerald-700">{fmtNum(z.soil_moisture, 1)}%</dd>
        <dt className="text-slate-400">{t('env.slope')}</dt>
        <dd className="text-right font-bold">{fmtNum(z.slope_angle, 1)}°</dd>
        <dt className="text-slate-400">{t('risk.score')}</dt>
        <dd className="text-right text-sm font-extrabold tabular-nums text-govblue-950">{fmtNum(z.risk_score, 0)}/100</dd>
        <dt className="col-span-2 mt-1 border-t border-slate-100 pt-1 text-slate-400">
          {t('map.popup.updated')}: {timeAgo(z.last_updated)}
        </dt>
      </dl>
      <div className="mt-2">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full" style={{ width: `${z.risk_score}%`, background: RISK_META[z.risk_level]?.color }} />
        </div>
        <p className="mt-1 text-[10px] text-slate-400">confidence {(z.confidence * 100).toFixed(0)}%</p>
      </div>
    </div>
  );
}

export default function RiskMap() {
  const { t } = useTranslation();
  const navState = useLocation().state;
  const [state, setState] = useState('');
  const [level, setLevel] = useState('');
  const [showRoads, setShowRoads] = useState(true);
  const [showReports, setShowReports] = useState(true);

  const { data: zones, loading: loadingZones, error: errorZones, refresh: refreshZones } = useApi('/api/risk/zones', { pollMs: 15000 });
  const { data: roads, loading: loadingRoads } = useApi('/api/roads', { pollMs: 30000 });
  const { data: reports, loading: loadingReports } = useApi('/api/reports', { pollMs: 30000 });

  const filteredZones = useMemo(() => {
    if (!zones) return [];
    return zones.filter((z) => {
      if (state && z.state !== state) return false;
      if (level && z.risk_level !== level) return false;
      return true;
    });
  }, [zones, state, level]);

  const counts = useMemo(() => {
    const c = { LOW: 0, MODERATE: 0, HIGH: 0, CRITICAL: 0 };
    (zones || []).forEach((z) => {
      if (c[z.risk_level] !== undefined) c[z.risk_level] += 1;
    });
    return c;
  }, [zones]);

  const loading = loadingZones || loadingRoads || loadingReports;

  return (
    <div>
      <PageHeader title={t('map.title')} icon="🗺️" subtitle={`${zones?.length || 0} zones · OSM + Leaflet`} />

      <div className="grid gap-4 xl:grid-cols-[300px_1fr]">
        {/* Control panel */}
        <div className="order-2 space-y-4 xl:order-1">
          <Card title="Filters">
            <div className="space-y-3">
              <select className="input" value={state} onChange={(e) => setState(e.target.value)}>
                <option value="">{t('common.allStates')}</option>
                {STATES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <div className="flex flex-wrap gap-1.5">
                {RISK_LEVELS.map((l) => {
                  const active = level === l;
                  const meta = RISK_META[l];
                  return (
                    <button
                      key={l}
                      onClick={() => setLevel(active ? '' : l)}
                      className={`rounded-lg px-2.5 py-1.5 text-[11px] font-extrabold uppercase tracking-wide ring-1 transition ${
                        active ? 'text-white ring-transparent' : 'bg-white ring-slate-200 text-slate-600 hover:ring-slate-400'
                      }`}
                      style={active ? { background: meta.color } : {}}
                    >
                      {l} · {counts[l]}
                    </button>
                  );
                })}
              </div>
              <div className="space-y-2 border-t border-slate-100 pt-3 text-sm">
                <label className="flex cursor-pointer items-center gap-2.5 font-semibold text-slate-700">
                  <input type="checkbox" checked={showRoads} onChange={(e) => setShowRoads(e.target.checked)} className="h-4 w-4 accent-blue-800" />
                  🛣️ {t('map.roads')} ({roads?.length || 0})
                </label>
                <label className="flex cursor-pointer items-center gap-2.5 font-semibold text-slate-700">
                  <input type="checkbox" checked={showReports} onChange={(e) => setShowReports(e.target.checked)} className="h-4 w-4 accent-blue-800" />
                  📝 {t('map.reports')} ({reports?.length || 0})
                </label>
              </div>
            </div>
          </Card>

          <Card title="Legend">
            <ul className="space-y-1.5 text-xs">
              {RISK_LEVELS.map((l) => (
                <li key={l} className="flex items-center gap-2 font-semibold text-slate-700">
                  <span className="h-3 w-3 rounded-full" style={{ background: RISK_META[l].color }} />
                  {l}
                  <span className="ml-auto tabular-nums text-slate-400">{counts[l]}</span>
                </li>
              ))}
            </ul>
            <ul className="mt-3 space-y-1.5 border-t border-slate-100 pt-3 text-xs">
              {Object.entries(ROAD_META).map(([k, m]) => (
                <li key={k} className="flex items-center gap-2 font-semibold text-slate-700">
                  <span className="h-1 w-6 rounded" style={{ background: m.color }} />
                  {m.label}
                </li>
              ))}
            </ul>
          </Card>

          {(errorZones || (loading && !zones)) && (
            <Card>
              {errorZones ? <ErrorBox message={errorZones} onRetry={refreshZones} t={t} /> : <Spinner label={t('common.loading')} />}
            </Card>
          )}
        </div>

        {/* Map */}
        <div className="card order-1 overflow-hidden xl:order-2">
          <div className="h-[72vh] min-h-[520px] w-full">
            <MapContainer center={NE_CENTER} zoom={7} scrollWheelZoom className="h-full w-full" preferCanvas>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <FocusController focusId={navState?.focus} zones={zones} />

              {/* Roads as polylines */}
              {showRoads &&
                (roads || []).map((road) => {
                  const meta = ROAD_META[road.status] || ROAD_META.OPEN;
                  return (
                    <Polyline
                      key={`road-${road.id}`}
                      positions={[
                        [road.latitude, road.longitude],
                        [road.end_latitude ?? road.latitude, road.end_longitude ?? road.longitude],
                      ]}
                      pathOptions={{ color: meta.color, weight: road.status === 'BLOCKED' ? 5 : 4, dashArray: road.status === 'PARTIALLY_BLOCKED' ? '6 5' : road.status === 'HIGH_RISK' ? '2 6' : undefined, opacity: 0.85 }}
                    >
                      <Tooltip direction="top" offset={[0, -4]} opacity={1}>
                        <div className="text-xs font-bold">
                          {road.name}
                          <div className="font-normal">
                            <RoadBadge status={road.status} />
                          </div>
                        </div>
                      </Tooltip>
                    </Polyline>
                  );
                })}

              {/* Reports */}
              {showReports &&
                (reports || []).map((r) => (
                  <Marker key={`report-${r.id}`} position={[r.latitude, r.longitude]} icon={reportIcon(r.report_type, r.status)}>
                    <Popup>
                      <div className="w-60">
                        <div className="mb-1 flex items-center justify-between">
                          <p className="text-sm font-extrabold">
                            {REPORT_TYPE_META[r.report_type]?.icon} {REPORT_TYPE_META[r.report_type]?.label || r.report_type}
                          </p>
                          <StatusPill status={r.status} />
                        </div>
                        {r.image_url && (
                          <img src={r.image_url} alt="report" className="mb-2 h-28 w-full rounded-lg object-cover" />
                        )}
                        <p className="text-xs text-slate-600">{r.description}</p>
                        <p className="mt-2 text-[10px] text-slate-400">
                          {r.reporter_name || 'Anonymous'} · {fmtDate(r.created_at)}
                        </p>
                      </div>
                    </Popup>
                  </Marker>
                ))}

              {/* Risk markers */}
              {filteredZones.map((z) => (
                <Marker key={z.location_id} position={[z.latitude, z.longitude]} icon={riskIcon(z.risk_level)}>
                  <Popup>
                    <RiskPopup z={z} />
                  </Popup>
                </Marker>
              ))}

              {/* Region halo for context */}
              <CircleMarker center={[25.85, 93.1]} radius={1} pathOptions={{ color: 'transparent' }} />
            </MapContainer>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 px-4 py-2 text-[11px] text-slate-400">
            <span>📍 {t('map.clickHint')}</span>
            <span className="flex items-center gap-3">
              <span>🟢 LOW</span><span>🟡 MODERATE</span><span>🟠 HIGH</span><span className="animate-pulse">🔴 CRITICAL</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
