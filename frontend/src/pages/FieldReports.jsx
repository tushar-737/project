import { useCallback, useEffect, useRef, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useTranslation } from '../i18n';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { getPendingReports, isOnline, queueReport } from '../services/offline';
import { Card, EmptyState, ErrorBox, PageHeader, Spinner, StatusPill } from '../components/ui';
import { fmtDate } from '../utils/format';
import { REPORT_TYPES, REPORT_TYPE_META } from '../utils/risk';
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet';
import L from 'leaflet';

function ClickPicker({ onPick }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

const PIN = L.divIcon({
  className: '',
  html: '<div style="background:#1e40af;border:3px solid #fff;border-radius:50% 50% 50% 0;width:26px;height:26px;transform:rotate(-45deg);box-shadow:0 2px 8px rgba(0,0,0,.35)"></div>',
  iconSize: [26, 26],
  iconAnchor: [13, 26],
});

export default function FieldReports() {
  const { t } = useTranslation();
  const { user, isOfficer } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState('');
  const [online, setOnline] = useState(isOnline());
  const { data: reports, loading, error, refresh } = useApi('/api/reports', { pollMs: 20000 });
  const [syncing, setSyncing] = useState(false);

  // form state
  const [form, setForm] = useState({
    report_type: 'LANDSLIDE',
    description: '',
    latitude: null,
    longitude: null,
  });
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [video, setVideo] = useState(null);
const [videoPreview, setVideoPreview] = useState(null);
  const [gpsState, setGpsState] = useState('idle'); // idle|locating|ok|denied
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const fileRef = useRef(null);
  const videoRef = useRef(null);

  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => {
      window.removeEventListener('online', on);
      window.removeEventListener('offline', off);
    };
  }, []);

  const pendingCount = getPendingReports().length;

  const syncNow = useCallback(async () => {
    setSyncing(true);
    try {
      await api.get('/api/health'); // ensure reachable
    } catch {
      setSyncing(false);
      return;
    }
    await import('../services/offline').then(async (m) => {
      await m.syncPendingReports();
      refresh();
    });
    setSyncing(false);
  }, [refresh]);

  function useGps() {
    if (!navigator.geolocation) {
      setGpsState('denied');
      return;
    }
    setGpsState('locating');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm((f) => ({ ...f, latitude: pos.coords.latitude, longitude: pos.coords.longitude }));
        setGpsState('ok');
      },
      () => setGpsState('denied'),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  }

  function onFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      setFormError('Only JPG/JPEG/PNG images are accepted');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setFormError('Image must be under 5 MB');
      return;
    }
    setImage(file);
    setFormError('');
    const reader = new FileReader();
    reader.onload = () => setImagePreview(reader.result);
    reader.readAsDataURL(file);
  }
  function onVideoFile(e) {
  const file = e.target.files?.[0];

  if (!file) return;

  if (!['video/mp4', 'video/webm'].includes(file.type)) {
    setFormError('Only MP4 or WebM videos are accepted');
    return;
  }

  if (file.size > 20 * 1024 * 1024) {
    setFormError('Video must be under 20 MB');
    return;
  }

  setVideo(file);
  setFormError('');

  const url = URL.createObjectURL(file);
  setVideoPreview(url);
}

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setFormError('');
    const { report_type, description, latitude, longitude } = form;
    if (latitude === null || longitude === null) {
      setFormError('Choose your location with GPS or by clicking the mini-map');
      setSaving(false);
      return;
    }

    const payload = {
      report_type,
      description,
      latitude: Number(latitude.toFixed(6)),
      longitude: Number(longitude.toFixed(6)),
    };

    try {
      if (online) {
        const fd = new FormData();
        Object.entries(payload).forEach(([k, v]) => fd.append(k, String(v)));
        if (image) fd.append('image', image);
if (video) fd.append('video', video);

await api.postForm('/api/reports', fd);
      } else {
        // Offline: store locally with the photo embedded, sync later.
        let imageData = null;
        if (image) imageData = await new Promise((res) => {
          const r = new FileReader();
          r.onload = () => res(r.result);
          r.readAsDataURL(image);
        });
        queueReport({ ...payload, imageData, imageName: image?.name });
      }
      setShowForm(false);
      setForm({ report_type: 'LANDSLIDE', description: '', latitude: null, longitude: null });
      setImage(null);
      setImagePreview(null);
      setVideo(null);

if (videoPreview) {
  URL.revokeObjectURL(videoPreview);
}

setVideoPreview(null);
      if (online) refresh();
    } catch (err) {
      setFormError(err.message || 'Could not submit the report');
    } finally {
      setSaving(false);
    }
  }

  const rows = reports || [];

  return (
    <div>
      <PageHeader
        title={`📝 ${t('reports.title')}`}
        icon="📝"
        subtitle={online ? undefined : `${pendingCount} offline report(s) waiting for sync`}
        actions={
          <div className="flex items-center gap-2">
            {!online && pendingCount > 0 && (
              <button className="btn-ghost text-xs" disabled={syncing} onClick={syncNow}>
                {syncing ? 'Syncing…' : `↻ Sync ${pendingCount}`}
              </button>
            )}
            <button className="btn-primary" onClick={() => setShowForm(true)}>
              ＋ {t('reports.newReport')}
            </button>
          </div>
        }
      />

      {showForm && (
        <Card className="mb-5 border-t-4 border-t-govblue-700">
          <form onSubmit={submit} className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500">{t('reports.type')}</span>
                  <select className="input" value={form.report_type} onChange={(e) => setForm({ ...form, report_type: e.target.value })}>
                    {REPORT_TYPES.map((rt) => (
                      <option key={rt} value={rt}>
                        {REPORT_TYPE_META[rt].icon} {REPORT_TYPE_META[rt].label} ({rt})
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500">{t('reports.dateReported')}</span>
                  <input className="input bg-slate-50" value={new Date().toLocaleDateString('en-IN')} disabled />
                </label>
              </div>
              <label className="block">
                <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500">{t('reports.description')}</span>
                <textarea
                  className="input min-h-[110px]"
                  value={form.description}
                  maxLength={2000}
                  placeholder="Describe what you observed…"
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </label>
  <div>
  <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500">
    Media Evidence
  </span>

  <div className="flex flex-wrap items-center gap-3">

    {/* Hidden image input */}
    <input
      ref={fileRef}
      type="file"
      accept="image/jpeg,image/png"
      className="hidden"
      onChange={onFile}
    />

    {/* Hidden video input */}
    <input
      ref={videoRef}
      type="file"
      accept="video/mp4,video/webm"
      className="hidden"
      onChange={onVideoFile}
    />

    {/* Choose photo */}
    <button
      type="button"
      className="btn-ghost text-xs"
      onClick={() => fileRef.current?.click()}
    >
      📷 Choose Photo
    </button>

    {/* Choose video */}
    <button
      type="button"
      className="btn-ghost text-xs"
      onClick={() => videoRef.current?.click()}
    >
      🎥 Choose Video
    </button>

  </div>

  {/* Selected image name */}
  {image && (
    <p className="mt-2 text-xs text-slate-500">
      📷 {image.name}
    </p>
  )}

  {/* Image preview */}
  {imagePreview && (
    <img
      src={imagePreview}
      alt="Selected evidence"
      className="mt-3 h-32 rounded-lg object-cover ring-1 ring-slate-200"
    />
  )}

  {/* Selected video name */}
  {video && (
    <p className="mt-2 text-xs text-slate-500">
      🎥 {video.name}
    </p>
  )}

  {/* Video preview */}
  {videoPreview && (
    <video
      src={videoPreview}
      controls
      className="mt-3 h-48 w-full rounded-lg object-cover ring-1 ring-slate-200"
    />
  )}

</div>

{/* IMPORTANT: This closes the LEFT COLUMN */}
</div>

{/* RIGHT COLUMN */}


            <div className="space-y-4">
              <div>
                <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500">GPS location</span>
                <div className="flex flex-wrap items-center gap-2">
                  <button type="button" className="btn-ghost text-xs" onClick={useGps}>
                      📍 Use My Current Location
                  </button>
                  {gpsState === 'locating' && <span className="text-xs text-slate-400">locating…</span>}
                  {gpsState === 'denied' && <span className="text-xs font-semibold text-amber-600">GPS unavailable — pick the point on the map</span>}
                  <span className="text-xs text-slate-400">
                    {form.latitude !== null ? `📍 ${form.latitude.toFixed(5)}, ${form.longitude.toFixed(5)}` : t('reports.pickOnMap')}
                  </span>
                </div>
              </div>
              <div className="h-64 overflow-hidden rounded-xl ring-1 ring-slate-200">
                <MapContainer center={[25.85, 93.1]} zoom={6} className="h-full w-full" scrollWheelZoom>
                  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                  <ClickPicker onPick={(lat, lng) => { setForm((f) => ({ ...f, latitude: lat, longitude: lng })); setGpsState('ok'); }} />
                  {form.latitude !== null && <Marker position={[form.latitude, form.longitude]} icon={PIN} />}
                </MapContainer>
              </div>
              <p className="text-[11px] text-slate-400">Click anywhere on the map to drop the report location.</p>
              {!online && (
                <p className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-800">
                  Offline: report + photo are stored on this device and synchronised automatically when you reconnect.
                </p>
              )}
              {formError && <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700">{formError}</p>}
              <div className="flex justify-end gap-2">
                <button type="button" className="btn-ghost" onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? 'Submitting…' : online ? 'Submit report' : 'Save offline'}
                </button>
              </div>
            </div>
          </form>
        </Card>
      )}

      {/* Filters + list */}
      <div className="mb-4 flex flex-wrap gap-2">
        <button onClick={() => setFilter('')} className={`chip ${!filter ? 'bg-govblue-800 text-white' : 'bg-white text-slate-600'}`}>All ({rows.length})</button>
        {['PENDING', 'VERIFIED', 'REJECTED'].map((s) => (
          <button key={s} onClick={() => setFilter(filter === s ? '' : s)} className={`chip ${filter === s ? 'bg-govblue-800 text-white' : 'bg-white text-slate-600'}`}>
            {t(`common.${s.toLowerCase()}`)} ({rows.filter((r) => r.status === s).length})
          </button>
        ))}
      </div>

      {loading && !reports && <Spinner label={t('common.loading')} />}
      {error && !reports && <ErrorBox message={error} t={t} onRetry={refresh} />}

      {reports && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {rows.filter((r) => !filter || r.status === filter).length === 0 && (
            <div className="md:col-span-2 xl:col-span-3"><Card><EmptyState icon="🗂️" text={t('common.noData')} /></Card></div>
          )}
          {rows
            .filter((r) => !filter || r.status === filter)
            .map((r) => (
              <Card key={r.id} className="flex flex-col" pad={false}>
               {r.image_url && (
  <img
    src={r.image_url}
    alt="report"
    className="h-40 w-full object-cover"
  />
)}

{r.video_url && (
  <video
    src={r.video_url}
    controls
    className="h-48 w-full object-cover"
  >
    Your browser does not support the video tag.
  </video>
)}
           <div className="flex flex-1 flex-col p-4">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-extrabold text-govblue-950">
                      {REPORT_TYPE_META[r.report_type]?.icon} {REPORT_TYPE_META[r.report_type]?.label || r.report_type}
                    </p>
                    <StatusPill status={r.status} />
                  </div>
                  <p className="mt-2 flex-1 text-sm text-slate-600">{r.description || '—'}</p>
                  <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2.5 text-[11px] text-slate-400">
                    <span>📍 {r.latitude.toFixed(4)}, {r.longitude.toFixed(4)}</span>
                    <span>{fmtDate(r.created_at)}</span>
                  </div>
                  {r.reporter_name && <p className="text-[11px] text-slate-400">by {r.reporter_name}</p>}
                  {isOfficer && r.status === 'PENDING' && (
                    <div className="mt-3 flex gap-2">
                      <button
                        className="btn flex-1 border border-emerald-600 bg-emerald-50 py-1.5 text-xs font-bold text-emerald-700 hover:bg-emerald-100"
                        onClick={async () => {
                          await api.put(`/api/reports/${r.id}/verify`, { status: 'VERIFIED' });
                          refresh();
                        }}
                      >
                        ✓ {t('reports.verify')}
                      </button>
                      <button
                        className="btn flex-1 border border-red-200 bg-white py-1.5 text-xs font-bold text-red-600 hover:bg-red-50"
                        onClick={async () => {
                          await api.put(`/api/reports/${r.id}/verify`, { status: 'REJECTED' });
                          refresh();
                        }}
                      >
                        ✕ {t('reports.reject')}
                      </button>
                    </div>
                  )}
                </div>
              </Card>
            ))}
        </div>
      )}
      {user && <p className="mt-4 text-center text-[11px] text-slate-400">Signed in as {user.name} · {user.role}</p>}
    </div>
  );
}
