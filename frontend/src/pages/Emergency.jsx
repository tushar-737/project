import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { useTranslation } from '../i18n';
import { api } from '../services/api';
import { Card, EmptyState, ErrorBox, PageHeader, PriorityBadge, RiskBadge, Spinner } from '../components/ui';
import { PRIORITY_META } from '../utils/risk';

export default function Emergency() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data, loading, error, refresh } = useApi('/api/emergency/priorities', { pollMs: 20000 });

  const ranked = useMemo(() => {
    const list = [...(data || [])];
    const order = { 'PRIORITY 1': 0, 'PRIORITY 2': 1, 'PRIORITY 3': 2 };
    return list.sort((a, b) => order[a.priority_level] - order[b.priority_level] || b.priority_score - a.priority_score);
  }, [data]);

  async function recompute() {
    try {
      await api.post('/api/emergency/recompute');
      refresh();
    } catch {
      /* surface via refresh failure */
    }
  }

  const tiers = ['PRIORITY 1', 'PRIORITY 2', 'PRIORITY 3'];

  return (
    <div>
      <PageHeader
        title={`🚑 ${t('emergency.title')}`}
        icon="🚑"
        subtitle="ranked by risk score 55% · road isolation 25% · population 12% · isolation 8%"
        actions={
          <button className="btn-ghost text-xs" onClick={recompute}>
            ↻ Recompute ranking
          </button>
        }
      />

      {loading && !data && <Spinner label={t('common.loading')} />}
      {error && !data && <ErrorBox message={error} onRetry={refresh} t={t} />}

      {data && (
        <div className="space-y-6">
          {tiers.map((tier) => {
            const rows = ranked.filter((r) => r.priority_level === tier);
            const meta = PRIORITY_META[tier];
            return (
              <div key={tier}>
                <div className="mb-2 flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full" style={{ background: meta.color }} />
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-govblue-950">
                    {t(`emergency.${tier.split(' ').join('').toLowerCase()}`)} — {meta.desc}
                  </h2>
                  <span className="text-xs text-slate-400">({rows.length})</span>
                </div>
                {rows.length === 0 ? (
                  <Card><EmptyState icon="✅" text="No locations in this tier" /></Card>
                ) : (
                  <Card pad={false}>
                    <table className="w-full min-w-[760px]">
                      <tbody className="divide-y divide-slate-100">
                        {rows.map((row) => (
                          <tr key={row.id} className="cursor-pointer hover:bg-govblue-50/40" onClick={() => navigate('/map', { state: { focus: row.location_id } })}>
                            <td className="td w-14 text-center">
                              <span className="text-lg font-extrabold tabular-nums" style={{ color: meta.color }}>
                                {ranked.indexOf(row) + 1}
                              </span>
                            </td>
                            <td className="td">
                              <p className="font-extrabold text-slate-800">{row.location?.name}</p>
                              <p className="text-xs text-slate-400">{row.location?.district}, {row.location?.state}</p>
                            </td>
                            <td className="td w-28 text-center"><PriorityBadge level={row.priority_level} /></td>
                            <td className="td w-32 text-center">
                              <div>
                                <p className="text-sm font-extrabold tabular-nums text-govblue-950">{Math.round(row.priority_score)}</p>
                                <p className="h-1 w-20 overflow-hidden rounded-full bg-slate-100"><span className="block h-full rounded-full" style={{ width: `${row.priority_score}%`, background: meta.color }} /></p>
                              </div>
                            </td>
                            <td className="td">
                              <p className="text-xs leading-relaxed text-slate-500">{row.reason}</p>
                            </td>
                            <td className="td w-24 text-center">
                              <RiskBadge level={row.risk_level || 'LOW'} />
                              {row.risk_score != null && <p className="mt-1 text-[10px] text-slate-400">{Math.round(row.risk_score)}/100</p>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </Card>
                )}
              </div>
            );
          })}
          <p className="text-center text-[11px] text-slate-400">
            Ranking updates automatically after every simulation run and road-status change
          </p>
        </div>
      )}
    </div>
  );
}
