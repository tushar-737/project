import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n';
import { ApiError } from '../services/api';

const DEMO_ACCOUNTS = [
  { label: 'Admin Officer', email: 'admin@ner.gov.in', role: 'ADMIN', icon: '🛡️' },
  { label: 'Field Officer', email: 'officer@ner.gov.in', role: 'FIELD_OFFICER', icon: '👷' },
  { label: 'Citizen User', email: 'citizen@ner.gov.in', role: 'CITIZEN', icon: '🧑' },
];
const DEMO_PASS = { 'admin@ner.gov.in': 'admin123', 'officer@ner.gov.in': 'officer123', 'citizen@ner.gov.in': 'citizen123' };

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'FIELD_OFFICER' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      if (mode === 'login') {
        await login(form.email.trim(), form.password);
      } else {
        const resp = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...form, email: form.email.trim() }),
        });
        const body = await resp.json();
        if (!resp.ok) throw new ApiError(body.detail || 'Registration failed', resp.status);
        await login(form.email.trim(), form.password);
      }
      navigate('/', { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unexpected error');
    } finally {
      setBusy(false);
    }
  }

  async function quickLogin(email) {
    setBusy(true);
    setError('');
    try {
      await login(email, DEMO_PASS[email]);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unexpected error');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="gov-texture flex min-h-screen items-center justify-center bg-govblue-950 p-4">
      <div className="grid w-full max-w-4xl overflow-hidden rounded-2xl bg-white shadow-2xl lg:grid-cols-2">
        {/* Brand panel */}
        <div className="gov-texture relative hidden flex-col justify-between bg-gradient-to-br from-govblue-900 via-govblue-950 to-govblue-950 p-10 text-white lg:flex">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-red-500 to-orange-500 text-2xl shadow-lg">⛰️</div>
              <div>
                <p className="text-xl font-extrabold">{t('app.name')}</p>
                <p className="text-xs text-slate-300">{t('app.subtitle')}</p>
              </div>
            </div>
            <h1 className="mt-10 text-3xl font-extrabold leading-tight">{t('app.tagline')}</h1>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">{t('app.region')}</p>
            <ul className="mt-8 space-y-3 text-sm text-slate-200">
              <li className="flex items-center gap-3"><span>📡</span> Simulated sensor network (IoT-ready)</li>
              <li className="flex items-center gap-3"><span>🧠</span> AI landslide risk engine</li>
              <li className="flex items-center gap-3"><span>🗺️</span> Live GIS risk map</li>
              <li className="flex items-center gap-3"><span>🚨</span> Automated alerts &amp; SMS broadcast</li>
              <li className="flex items-center gap-3"><span>🚑</span> Emergency response prioritisation</li>
            </ul>
          </div>
          <p className="text-[11px] text-slate-400">
            Academic / disaster-management demonstration prototype.
            Does not predict the exact time of a landslide event.
          </p>
        </div>

        {/* Form panel */}
        <div className="p-8 lg:p-12">
          <div className="mb-8 text-center lg:hidden">
            <div className="mb-2 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-red-500 to-orange-500 text-2xl">⛰️</div>
            <p className="text-lg font-extrabold text-govblue-950">{t('app.name')}</p>
          </div>

          <h2 className="text-xl font-extrabold text-govblue-950">
            {mode === 'login' ? t('auth.welcome') : t('auth.register')}
          </h2>
          <p className="mt-1 text-sm text-slate-500">{t('auth.loginHint')}</p>

          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-semibold text-red-700">{error}</div>
          )}

          <form onSubmit={submit} className="mt-6 space-y-4">
            {mode === 'register' && (
              <>
                <input className="input" placeholder={t('auth.name')} required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                  <option value="FIELD_OFFICER">{t('common.fieldOfficer')}</option>
                  <option value="CITIZEN">{t('common.citizen')}</option>
                  <option value="ADMIN">{t('common.admin')}</option>
                </select>
              </>
            )}
            <input className="input" type="email" placeholder={t('auth.email')} required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <input className="input" type="password" placeholder={t('auth.password')} required minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            <button className="btn-primary w-full" disabled={busy}>
              {busy ? '…' : mode === 'login' ? t('auth.login') : t('auth.register')}
            </button>
          </form>

          <div className="my-6 flex items-center gap-3 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <span className="h-px flex-1 bg-slate-200" /> Quick demo sign-in <span className="h-px flex-1 bg-slate-200" />
          </div>
          <div className="grid gap-2">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                disabled={busy}
                onClick={() => quickLogin(acc.email)}
                className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-left transition hover:border-govblue-600 hover:bg-govblue-50 disabled:opacity-50"
              >
                <span className="text-lg">{acc.icon}</span>
                <span className="flex-1">
                  <span className="block text-sm font-bold text-slate-800">{acc.label}</span>
                  <span className="block text-xs text-slate-500">{acc.email}</span>
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">demo</span>
              </button>
            ))}
          </div>

          <p className="mt-6 text-center text-sm text-slate-500">
            {mode === 'login' ? t('auth.noAccount') : t('auth.hasAccount')}{' '}
            <button className="font-bold text-govblue-800 hover:underline" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
              {mode === 'login' ? t('auth.register') : t('auth.login')}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
