import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { useTranslation } from '../i18n';
import { Card, EmptyState, ErrorBox, PageHeader, RiskBadge, ScoreBar, Spinner } from '../components/ui';
import { fmtNum, timeAgo } from '../utils/format';
import { RISK_LEVELS, STATES } from '../utils/risk';

export default function Monitoring() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data: zones, loading, error, refresh } = useApi('/api/risk/zones', { pollMs: 15000 });
  const [search, setSearch] = useState('');
  const [state, setState] = useState('');
  const [level, setLevel] = useState('');

  const rows = useMemo(() => {
    if (!zones) return [];
    const q = search.trim().toLowerCase();
    return zones.filter((z) => {
      if (q && !`${z.name} ${z.district} ${z.state}`.toLowerCase().includes(q)) return false;
      if (state && z.state !== state) return false;
      if (level && z.risk_level !== level) return false;
      return true;
    });
  }, [zones, search, state, level]);

  return (
    <div>
      <PageHeader
        title={t('monitoring.title')}
        icon="🛰️"
        subtitle={`${zones?.length || 0} monitored locations · refresh 15s`}
        actions={
          <button onClick={refresh} className="btn-ghost text-xs">
            ↻ {t('common.refresh')}
          </button>
        }
      />

      {/* Filters */}
      <div className="mb-4 grid gap-3 md:grid-cols-[1fr_220px_220px]">
        <input className="input" placeholder={t('common.search')} value={search} onChange={(e) => setSearch(e.target.value)} />
        <select className="input" value={state} onChange={(e) => setState(e.target.value)}>
          <option value="">{t('common.allStates')}</option>
          {STATES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select className="input" value={level} onChange={(e) => setLevel(e.target.value)}>
          <option value="">{t('common.allLevels')}</option>
          {RISK_LEVELS.map((l) => (
            <option key={l} value={l}>
              {t(`risk.${l.toLowerCase()}`)} ({l})
            </option>
          ))}
        </select>
      </div>

      {loading && !zones && <Spinner label={t('common.loading')} />}
      {error && !zones && <ErrorBox message={error} onRetry={refresh} t={t} />}

      {zones && (
        <Card pad={false}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px]">
              <thead className="border-b border-slate-100 bg-slate-50/70">
                <tr>
                  <th className="th">{t('monitoring.table.location')}</th>
                  <th className="th text-center">{t('monitoring.table.rainfall')}</th>
                  <th className="th text-center">{t('monitoring.table.soil')}</th>
                  <th className="th text-center">{t('monitoring.table.slope')}</th>
                  <th className="th text-center">{t('monitoring.table.score')}</th>
                  <th className="th text-center">{t('monitoring.table.level')}</th>
                  <th className="th text-center">{t('monitoring.table.updated')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.length === 0 && (
                  <tr>
                    <td className="td" colSpan={7}>
                      <EmptyState text={t('common.noData')} />
                    </td>
                  </tr>
                )}
                {rows.map((z) => (
                  <tr
                    key={z.location_id}
                    className="cursor-pointer transition hover:bg-govblue-50/50"
                    onClick={() => navigate('/map', { state: { focus: z.location_id } })}
                  >
                    <td className="td">
                      <p className="font-bold text-slate-800">{z.name}</p>
                      <p className="text-xs text-slate-400">
                        {z.district}, {z.state}
                      </p>
                    </td>
                    <td className="td text-center font-semibold tabular-nums text-blue-700">{fmtNum(z.rainfall, 0)} mm</td>
                    <td className="td text-center font-semibold tabular-nums text-emerald-700">{fmtNum(z.soil_moisture, 0)}%</td>
                    <td className="td text-center tabular-nums text-slate-600">{fmtNum(z.slope_angle, 1)}°</td>
                    <td className="td text-center">
                      <ScoreBar score={z.risk_score} />
                    </td>
                    <td className="td text-center">
                      <RiskBadge level={z.risk_level} />
                    </td>
                    <td className="td text-center text-xs text-slate-400">{timeAgo(z.last_updated)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rows.length > 0 && (
            <div className="border-t border-slate-100 px-4 py-2 text-xs text-slate-400">
              {rows.length} of {zones.length} locations shown — click a row to view it on the GIS map
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
