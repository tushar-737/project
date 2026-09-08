import { RISK_META, ROAD_META, PRIORITY_META } from '../utils/risk';
import { useTranslation } from '../i18n';

export function RiskBadge({ level, size = 'md' }) {
  const meta = RISK_META[level] || RISK_META.LOW;
  const pad = size === 'lg' ? 'px-2.5 py-1 text-xs' : 'px-2 py-0.5 text-[11px]';
  return (
    <span className={`chip ${meta.bg} ${meta.text} ring-1 ${pad} ring-inset`} style={{ ['--tw-ring-color']: meta.color + '55' }}>
      <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: meta.color }} />
      {level}
    </span>
  );
}

export function RoadBadge({ status }) {
  const meta = ROAD_META[status] || ROAD_META.OPEN;
  return (
    <span className={`chip ${meta.bg} ${meta.text}`}>
      <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: meta.color }} />
      {status.replace(/_/g, ' ')}
    </span>
  );
}

export function PriorityBadge({ level }) {
  const meta = PRIORITY_META[level] || PRIORITY_META['PRIORITY 3'];
  return (
    <span className={`chip ${meta.bg} ${meta.text}`}>
      <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: meta.color }} />
      {level}
    </span>
  );
}

export function StatusPill({ status }) {
  const map = {
    PENDING: 'bg-amber-100 text-amber-800',
    VERIFIED: 'bg-emerald-100 text-emerald-700',
    REJECTED: 'bg-slate-200 text-slate-600',
    ACTIVE: 'bg-red-100 text-red-700',
    RESOLVED: 'bg-emerald-100 text-emerald-700',
    OPEN: 'bg-emerald-100 text-emerald-700',
    HIGH_RISK: 'bg-orange-100 text-orange-800',
    PARTIALLY_BLOCKED: 'bg-yellow-100 text-yellow-800',
    BLOCKED: 'bg-red-100 text-red-700',
  };
  return (
    <span className={`inline-flex rounded-md px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide ${map[status] || 'bg-slate-100 text-slate-600'}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
}

export function StatCard({ label, value, sub, icon, accent = 'border-t-govblue-700' }) {
  return (
    <div className={`card border-t-4 ${accent} flex items-start gap-4 p-5`}>
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-xl">{icon}</div>
      <div className="min-w-0">
        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
        <p className="mt-0.5 text-3xl font-extrabold tabular-nums text-govblue-950">{value}</p>
        {sub && <p className="mt-0.5 truncate text-xs text-slate-500">{sub}</p>}
      </div>
    </div>
  );
}

export function Card({ title, actions, children, className = '', pad = true }) {
  return (
    <div className={`card ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-5 py-3.5">
          {title && <h3 className="text-sm font-bold uppercase tracking-wide text-govblue-950">{title}</h3>}
          {actions}
        </div>
      )}
      <div className={pad ? 'card-pad' : ''}>{children}</div>
    </div>
  );
}

export function PageHeader({ title, subtitle, actions, icon }) {
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        {icon && (
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-govblue-800 text-xl text-white shadow-card">
            {icon}
          </div>
        )}
        <div>
          <h1 className="text-xl font-extrabold text-govblue-950">{title}</h1>
          {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
        </div>
      </div>
      {actions}
    </div>
  );
}

export function Spinner({ label }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-14 text-slate-400">
      <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-slate-200 border-t-govblue-700" />
      {label && <p className="text-sm">{label}</p>}
    </div>
  );
}

export function ErrorBox({ message, onRetry, t }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-6 py-10 text-center">
      <div className="text-3xl">⚠️</div>
      <p className="text-sm font-semibold text-red-700">{message || (t ? t('common.error') : 'Request failed')}</p>
      {onRetry && (
        <button className="btn-ghost" onClick={onRetry}>
          {t ? t('common.retry') : 'Retry'}
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon = '🗂️', text }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-slate-400">
      <div className="text-3xl">{icon}</div>
      <p className="text-sm">{text}</p>
    </div>
  );
}

export function ScoreBar({ score }) {
  const color =
    score >= 76 ? '#dc2626' : score >= 51 ? '#f97316' : score >= 26 ? '#eab308' : '#22c55e';
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-200">
        <div className="gauge-fill h-full rounded-full" style={{ width: `${Math.max(2, Math.min(100, score))}%`, backgroundColor: color }} />
      </div>
      <span className="text-sm font-bold tabular-nums text-slate-700">{Math.round(score)}</span>
    </div>
  );
}

export function LangSwitch() {
  const { lang, setLang } = useTranslation();
  return (
    <div className="flex items-center rounded-lg border border-slate-200 bg-white p-0.5 text-xs font-bold">
      {['en', 'hi'].map((code) => (
        <button
          key={code}
          onClick={() => setLang(code)}
          className={`rounded-md px-2 py-1 uppercase transition ${lang === code ? 'bg-govblue-800 text-white' : 'text-slate-500 hover:text-govblue-800'}`}
        >
          {code === 'en' ? 'EN' : 'हिं'}
        </button>
      ))}
    </div>
  );
}
