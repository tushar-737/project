import { useMemo } from 'react';
import { useApi } from '../hooks/useApi';
import { useTranslation } from '../i18n';
import { Card, EmptyState, ErrorBox, PageHeader, Spinner } from '../components/ui';
import { fmtNum } from '../utils/format';
import { levelColor, REPORT_TYPES, REPORT_TYPE_META, ROAD_META } from '../utils/risk';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';

function Section({ title, children, span = 'xl:col-span-1' }) {
  return <Card title={title} className={span}>{children}</Card>;
}

export default function Analytics() {
  const { t } = useTranslation();
  const { data: zones, loading: lz, error: ez, refresh: rz } = useApi('/api/risk/zones');
  const { data: roads } = useApi('/api/roads');
  const { data: reports } = useApi('/api/reports');
  const { data: trend } = useApi('/api/risk/trend/overview');

  const dist = useMemo(() => {
    const c = { LOW: 0, MODERATE: 0, HIGH: 0, CRITICAL: 0 };
    (zones || []).forEach((z) => {
      c[z.risk_level] += 1;
    });
    return Object.entries(c).map(([k, v]) => ({ name: k, value: v, fill: levelColor(k) }));
  }, [zones]);

  const rainScatter = useMemo(
    () => (zones || []).filter((z) => z.rainfall != null).map((z) => ({ x: +z.rainfall.toFixed(1), y: +z.risk_score.toFixed(1), level: z.risk_level, name: z.name })),
    [zones],
  );
  const soilScatter = useMemo(
    () => (zones || []).filter((z) => z.soil_moisture != null).map((z) => ({ x: +z.soil_moisture.toFixed(1), y: +z.risk_score.toFixed(1), level: z.risk_level, name: z.name })),
    [zones],
  );

  const roadData = useMemo(() => {
    const c = { OPEN: 0, HIGH_RISK: 0, PARTIALLY_BLOCKED: 0, BLOCKED: 0 };
    (roads || []).forEach((r) => {
      c[r.status] += 1;
    });
    return Object.entries(c).map(([k, v]) => ({ name: k.replace(/_/g, ' '), value: v, fill: ROAD_META[k].color }));
  }, [roads]);

  const reportData = useMemo(() => {
    const c = Object.fromEntries(REPORT_TYPES.map((rt) => [rt, 0]));
    (reports || []).forEach((r) => {
      if (c[r.report_type] !== undefined) c[r.report_type] += 1;
    });
    return REPORT_TYPES.filter((rt) => c[rt] > 0).map((rt) => ({ name: REPORT_TYPE_META[rt].label, value: c[rt], fill: '#1e40af' }));
  }, [reports]);

  const trendData = useMemo(
    () =>
      (trend || []).map((p) => ({
        time: new Date(p.time).toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit' }),
        avg: p.avg_score,
        max: p.max_score,
      })),
    [trend],
  );

  if (lz && !zones) return <Spinner label={t('common.loading')} />;
  if (ez && !zones)
    return (
      <div className="py-10">
        <ErrorBox message={ez} onRetry={rz} t={t} />
      </div>
    );

  const tooltipStyle = { borderRadius: 10, fontSize: 12, border: '1px solid #e2e8f0' };
  const axisTick = { fontSize: 10, fill: '#64748b' };

  return (
    <div>
      <PageHeader title={`📈 ${t('analytics.title')}`} icon="📈" subtitle="all charts are computed live from the backend APIs" />
      <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
        <Section title={`1 · ${t('risk.distribution')}`}>
          <ResponsiveContainer width="100%" height={230}>
            <PieChart>
              <Pie data={dist} dataKey="value" nameKey="name" outerRadius={82} innerRadius={45} paddingAngle={3} strokeWidth={0}>
                {dist.map((d) => (
                  <Cell key={d.name} fill={d.fill} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
          <p className="text-center text-xs text-slate-400">{zones?.length || 0} zones in total</p>
        </Section>

        <Section title={`2 · ${t('analytics.rainfallVsRisk')}`}>
          <ResponsiveContainer width="100%" height={230}>
            <ScatterChart margin={{ left: -12, right: 8, top: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis type="number" dataKey="x" name="rainfall" unit=" mm" tick={axisTick} domain={[0, 'dataMax + 20']} />
              <YAxis type="number" dataKey="y" name="risk" unit="" domain={[0, 100]} tick={axisTick} />
              <ZAxis range={[50, 50]} />
              <Tooltip
                contentStyle={tooltipStyle}
                cursor={{ strokeDasharray: '3 3' }}
                formatter={(value, name) => [name === 'rainfall' ? `${value} mm` : `${value}/100`, name === 'rainfall' ? t('env.rainfall') : t('risk.score')]}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.name || ''}
              />
              {['LOW', 'MODERATE', 'HIGH', 'CRITICAL'].map((lv) => (
                <Scatter key={lv} name={lv} data={rainScatter.filter((p) => p.level === lv)} fill={levelColor(lv)} />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </Section>

        <Section title={`3 · ${t('analytics.soilVsRisk')}`}>
          <ResponsiveContainer width="100%" height={230}>
            <ScatterChart margin={{ left: -12, right: 8, top: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis type="number" dataKey="x" name="soil" unit="%" tick={axisTick} domain={[0, 100]} />
              <YAxis type="number" dataKey="y" name="risk" domain={[0, 100]} tick={axisTick} />
              <ZAxis range={[50, 50]} />
              <Tooltip
                contentStyle={tooltipStyle}
                cursor={{ strokeDasharray: '3 3' }}
                formatter={(value, name) => [name === 'soil' ? `${value}%` : `${value}/100`, name === 'soil' ? t('env.soilMoisture') : t('risk.score')]}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.name || ''}
              />
              {['LOW', 'MODERATE', 'HIGH', 'CRITICAL'].map((lv) => (
                <Scatter key={lv} name={lv} data={soilScatter.filter((p) => p.level === lv)} fill={levelColor(lv)} />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </Section>

        <Section title={`4 · ${t('analytics.roadStatus')}`}>
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={roadData} margin={{ left: -22, right: 8, top: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="name" tick={{ ...axisTick, fontSize: 9 }} interval={0} />
              <YAxis allowDecimals={false} tick={axisTick} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#f8fafc' }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {roadData.map((d) => (
                  <Cell key={d.name} fill={d.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title={`5 · ${t('analytics.reportsByType')}`}>
          {reportData.length === 0 ? (
            <EmptyState text={t('common.noData')} />
          ) : (
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={reportData} layout="vertical" margin={{ left: 70, right: 12, top: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" allowDecimals={false} tick={axisTick} />
                <YAxis type="category" dataKey="name" width={72} tick={{ ...axisTick, fontSize: 10 }} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#f8fafc' }} />
                <Bar dataKey="value" fill="#1d4ed8" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Section>

        <Section title={`6 · ${t('analytics.trend')}`} span="lg:col-span-2 xl:col-span-3">
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={trendData} margin={{ left: -18, right: 10, top: 8 }}>
              <defs>
                <linearGradient id="avgFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#dc2626" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#dc2626" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="time" tick={axisTick} minTickGap={30} />
              <YAxis domain={[0, 100]} tick={axisTick} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Area type="monotone" dataKey="max" name="max zone risk" stroke="#dc2626" strokeWidth={1.6} strokeDasharray="4 4" fill="none" />
              <Area type="monotone" dataKey="avg" name="regional average" stroke="#1e40af" strokeWidth={2.4} fill="url(#avgFill)" />
            </AreaChart>
          </ResponsiveContainer>
          {trendData.length === 0 && <p className="text-center text-xs text-slate-400">no history yet — run simulations to build it</p>}
        </Section>
      </div>

      <p className="mt-5 text-center text-[11px] text-slate-400">
        Scatter plots map every monitored zone: {fmtNum(rainScatter.length)} zones with rainfall samples, {fmtNum(soilScatter.length)} with soil moisture samples
      </p>
    </div>
  );
}
