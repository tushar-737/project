import { useMemo, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useTranslation } from '../i18n';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Card, EmptyState, ErrorBox, PageHeader, RoadBadge, Spinner } from '../components/ui';
import { fmtDate } from '../utils/format';
import { ROAD_META } from '../utils/risk';

const STATUSES = ['OPEN', 'HIGH_RISK', 'PARTIALLY_BLOCKED', 'BLOCKED'];

export default function RoadsPage() {
  const { t } = useTranslation();
  const { isOfficer } = useAuth();
  const { data: roads, loading, error, refresh } = useApi('/api/roads', { pollMs: 20000 });
  const [filter, setFilter] = useState('');
  const [busyId, setBusyId] = useState(null);

  const counts = useMemo(() => {
    const c = { OPEN: 0, HIGH_RISK: 0, PARTIALLY_BLOCKED: 0, BLOCKED: 0 };
    (roads || []).forEach((r) => {
      c[r.status] += 1;
    });
    return c;
  }, [roads]);

  const rows = useMemo(() => (roads || []).filter((r) => !filter || r.status === filter), [roads, filter]);

  async function setStatus(road, status) {
    setBusyId(road.id);
    try {
      await api.put(`/api/roads/${road.id}`, { status });
      refresh();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <PageHeader title={`🛣️ ${t('roads.title')}`} icon="🛣️" subtitle="10 corridors · live status · officers can update any road" />

      {/* status tiles */}
      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(filter === s ? '' : s)}
            className={`card flex items-center gap-3 p-4 text-left transition hover:shadow-md ${filter === s ? 'ring-2 ring-govblue-700' : ''}`}
          >
            <span className="h-4 w-4 rounded-full" style={{ background: ROAD_META[s].color }} />
            <span>
              <span className="block text-2xl font-extrabold tabular-nums text-govblue-950">{counts[s] || 0}</span>
              <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">{s.replace(/_/g, ' ')}</span>
            </span>
          </button>
        ))}
      </div>

      {loading && !roads && <Spinner label={t('common.loading')} />}
      {error && !roads && <ErrorBox message={error} onRetry={refresh} t={t} />}

      {roads && (
        <Card pad={false}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px]">
              <thead className="border-b border-slate-100 bg-slate-50/70">
                <tr>
                  <th className="th">{t('roads.name')}</th>
                  <th className="th">{t('common.district')} / {t('common.state')}</th>
                  <th className="th text-center">{t('common.status')}</th>
                  <th className="th text-center">risk</th>
                  <th className="th text-center">{t('common.updated')}</th>
                  {isOfficer && <th className="th text-right">{t('common.actions')}</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.length === 0 && (
                  <tr>
                    <td className="td" colSpan={6}><EmptyState text={t('common.noData')} /></td>
                  </tr>
                )}
                {rows.map((road) => (
                  <tr key={road.id} className="hover:bg-slate-50/60">
                    <td className="td font-bold text-slate-800">{road.name}</td>
                    <td className="td text-slate-500">{road.district}, {road.state}</td>
                    <td className="td text-center"><RoadBadge status={road.status} /></td>
                    <td className="td text-center text-xs font-bold uppercase text-slate-500">{road.risk_level}</td>
                    <td className="td text-center text-xs text-slate-400">{fmtDate(road.updated_at)}</td>
                    {isOfficer && (
                      <td className="td text-right">
                        <div className="flex justify-end gap-1.5">
                          {STATUSES.map((s) => (
                            <button
                              key={s}
                              disabled={busyId === road.id}
                              onClick={() => setStatus(road, s)}
                              title={s.replace(/_/g, ' ')}
                              className={`h-7 rounded-md px-2 text-[10px] font-extrabold uppercase tracking-wide ring-1 transition disabled:opacity-40 ${
                                road.status === s ? 'text-white ring-transparent' : 'bg-white text-slate-500 ring-slate-200 hover:ring-slate-400'
                              }`}
                              style={road.status === s ? { background: ROAD_META[s].color } : {}}
                            >
                              {s === 'PARTIALLY_BLOCKED' ? 'PART' : s === 'HIGH_RISK' ? 'RISK' : s === 'BLOCKED' ? 'BLOCK' : 'OPEN'}
                            </button>
                          ))}
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {isOfficer && (
            <div className="border-t border-slate-100 px-4 py-2 text-[11px] text-slate-400">
              Changing a road status immediately re-ranks the linked location in the emergency priority list.
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
