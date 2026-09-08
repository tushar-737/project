import { useMemo, useState } from 'react';
import { useApi, useMutate } from '../hooks/useApi';
import { useTranslation } from '../i18n';
import { Card, EmptyState, ErrorBox, PageHeader, RiskBadge, Spinner } from '../components/ui';
import { fmtDate } from '../utils/format';
import { RISK_META } from '../utils/risk';

export default function Alerts() {
  const { t } = useTranslation();
  const [status, setStatus] = useState('');
  const [level, setLevel] = useState('');
  const { data: alerts, loading, error, refresh } = useApi('/api/alerts', { pollMs: 15000 });
  const resolve = useMutate(refresh);
  const [busyId, setBusyId] = useState(null);

  const rows = useMemo(() => {
    if (!alerts) return [];
    return alerts.filter((a) => {
      if (status && a.status !== status) return false;
      if (level && a.risk_level !== level) return false;
      return true;
    });
  }, [alerts, status, level]);

  async function handleResolve(alert) {
    setBusyId(alert.id);
    await resolve(`/api/alerts/${alert.id}/resolve`, {}, 'PUT');
    setBusyId(null);
  }

  return (
    <div>
      <PageHeader
        title={`🔔 ${t('nav.alerts')}`}
        icon="🔔"
        subtitle={`${alerts?.filter((a) => a.status === 'ACTIVE').length || 0} active · ${t('alerts.smsLog')}`}
      />
      <div className="mb-4 flex flex-wrap gap-3">
        <select className="input !w-52" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">{t('alerts.filterStatus')}</option>
          <option value="ACTIVE">{t('common.active')}</option>
          <option value="RESOLVED">{t('common.resolved')}</option>
        </select>
        <select className="input !w-52" value={level} onChange={(e) => setLevel(e.target.value)}>
          <option value="">{t('alerts.filterLevel')}</option>
          <option value="HIGH">HIGH</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>
        <span className="ml-auto self-center text-xs text-slate-400">{rows.length} shown</span>
      </div>

      {loading && !alerts && <Spinner label={t('common.loading')} />}
      {error && !alerts && <ErrorBox message={error} onRetry={refresh} t={t} />}

      {alerts && (
        <div className="space-y-3">
          {rows.length === 0 && <Card><EmptyState icon="🔕" text={t('common.noData')} /></Card>}
          {rows.map((a) => {
            const meta = RISK_META[a.risk_level] || RISK_META.HIGH;
            const critical = a.risk_level === 'CRITICAL';
            return (
              <div
                key={a.id}
                className={`card overflow-hidden ${critical ? 'border-l-8' : 'border-l-8'} ${a.status === 'ACTIVE' ? (critical ? 'border-l-red-600' : 'border-l-orange-500') : 'border-l-slate-300 opacity-75'}`}
              >
                <div className="flex flex-wrap items-start gap-4 p-4">
                  <div
                    className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-2xl"
                    style={{ backgroundColor: meta.color + '1c' }}
                  >
                    {a.status === 'ACTIVE' ? (critical ? '🚨' : '⚠️') : '✅'}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-base font-extrabold text-govblue-950">{a.location_name}</p>
                      <RiskBadge level={a.risk_level} />
                      <span className={`rounded-md px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide ${a.status === 'ACTIVE' ? 'bg-slate-100 text-slate-600' : 'bg-emerald-100 text-emerald-700'}`}>
                        {a.status}
                      </span>
                      <span className="text-xs font-bold tabular-nums text-slate-400">
                        Alert #{a.id} · score {Math.round(a.risk_score)}/100
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-400">
                      {a.district}, {a.state} · {fmtDate(a.created_at)}
                    </p>
                    <pre className="mt-3 whitespace-pre-wrap rounded-xl bg-slate-50 p-3 font-sans text-[13px] leading-relaxed text-slate-700 ring-1 ring-slate-100">
                      {a.message}
                    </pre>
                  </div>
                  {a.status === 'ACTIVE' && (
                    <button
                      className="btn-ghost shrink-0 text-xs"
                      disabled={busyId === a.id}
                      onClick={() => handleResolve(a)}
                    >
                      {busyId === a.id ? '…' : t('alerts.resolve')}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
