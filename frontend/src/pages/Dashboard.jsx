import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useApi } from '../hooks/useApi';
import { useTranslation } from '../i18n';
import { useAuth } from '../context/AuthContext';

import {
  Card,
  EmptyState,
  ErrorBox,
  RiskBadge,
  Spinner,
  StatCard,
  StatusPill,
} from '../components/ui';

import { fmtNum, timeAgo } from '../utils/format';
import { levelColor, RISK_META } from '../utils/risk';

import {
  Area,
  AreaChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';


export default function Dashboard() {

  const { t } = useTranslation();

  const { user } = useAuth();

  const userRole = user?.role;


  const { data, loading, error, refresh } = useApi(
    '/api/dashboard/summary',
    { pollMs: 20000 }
  );


  const [weatherLoading, setWeatherLoading] = useState(false);

  const [weatherMessage, setWeatherMessage] = useState('');


  // =========================================================
  // FETCH LIVE WEATHER
  // =========================================================

  const fetchLiveWeather = async () => {

    try {

      setWeatherLoading(true);

      setWeatherMessage('');


      const response = await fetch(
        '/api/environment/fetch-live-weather/1',
        {
          method: 'POST',

          headers: {
            'Content-Type': 'application/json',
          },
        }
      );


      if (!response.ok) {

        throw new Error('Unable to fetch live weather');

      }


      const result = await response.json();


      setWeatherMessage(

        `Live weather updated · Risk: ${result.risk.risk_level} (${result.risk.risk_score})`

      );


      refresh();

    } catch (err) {

      console.error(err);

      setWeatherMessage(
        'Unable to fetch live weather. Please try again.'
      );

    } finally {

      setWeatherLoading(false);

    }

  };


  // =========================================================
  // LOADING
  // =========================================================

  if (loading && !data) {

    return (
      <Spinner label={t('common.loading')} />
    );

  }


  // =========================================================
  // ERROR
  // =========================================================

  if (error && !data) {

    return (

      <div className="py-10">

        <ErrorBox
          message={error}
          onRetry={refresh}
          t={t}
        />

      </div>

    );

  }


  if (!data) {

    return null;

  }


  // =========================================================
  // DATA PREPARATION
  // =========================================================

  const c = data.counts || {};

  const dist = data.distribution || {};


  const pieData = Object.entries(dist).map(([k, v]) => ({

    name: t(`risk.${k}`),

    value: v,

    color: levelColor(k.toUpperCase()),

  }));


  const trendData = (data.trend || []).map((p) => ({

    ...p,

    time: new Date(p.time).toLocaleString(
      'en-IN',
      {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
      }
    ),

  }));


  return (

    <div>


      {/* =====================================================
          DASHBOARD HEADER
      ===================================================== */}

      <div className="mb-7 flex flex-wrap items-end justify-between gap-4 border-b border-slate-200 pb-5">


        <div className="flex items-center gap-4">


          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-govblue-700 to-govblue-900 text-xl text-white shadow-pop">

            📊

          </div>


          <div>


            <p className="eyebrow mb-0.5">

              {t('app.region')}

            </p>


            <h1 className="text-[22px] font-extrabold leading-tight tracking-tight text-govblue-950">

              {t('nav.dashboard')}

            </h1>


            <p className="mt-0.5 text-sm text-slate-500">

              {c.locations || 0} monitored locations ·

              <span className="font-semibold text-emerald-600">

                {' '}● live

              </span>

            </p>


          </div>


        </div>



        {/* ACTION BUTTONS */}

        <div className="flex flex-wrap gap-3">


          <button
            type="button"
            onClick={fetchLiveWeather}
            disabled={weatherLoading}
            className="btn-ghost shadow-sm"
          >

            {weatherLoading
              ? '⏳ Updating...'
              : '🌦️ Fetch Live Weather'
            }

          </button>



          {/* ADMIN ONLY */}

          {userRole === 'ADMIN' && (

            <Link
              to="/simulation"
              state={{ autoDemo: true }}
              className="btn-danger shadow-pop"
            >

              🚨 {t('simulation.demo')}

            </Link>

          )}


        </div>


      </div>



      {/* =====================================================
          WEATHER MESSAGE
      ===================================================== */}

      {weatherMessage && (

        <div className="mb-5 flex items-center justify-between gap-3 rounded-xl border border-govblue-100 bg-govblue-50 px-4 py-3 text-sm font-medium text-govblue-900">


          <span>

            🌦️ {weatherMessage}

          </span>


          <button
            type="button"
            onClick={() => setWeatherMessage('')}
            className="text-govblue-700 hover:text-govblue-950"
          >

            ✕

          </button>


        </div>

      )}



      {/* =====================================================
          SUMMARY CARDS
      ===================================================== */}

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">


        <StatCard
          label={t('risk.highRiskZones')}
          value={c.high_risk_zones || 0}
          icon="⚠️"
          accent="border-t-risk-high"
          sub={`${c.critical_zones || 0} critical`}
        />


        <StatCard
          label={t('risk.criticalAlerts')}
          value={c.critical_alerts || 0}
          icon="🚨"
          accent="border-t-risk-critical"
          sub={`${c.active_alerts || 0} active total`}
        />


        <StatCard
          label={t('dashboard.blockedRoads')}
          value={c.blocked_roads || 0}
          icon="🛑"
          accent="border-t-govblue-700"
          sub={`${c.partially_blocked_roads || 0} partially blocked`}
        />


        <StatCard
          label={t('dashboard.activeReports')}
          value={c.active_reports || 0}
          icon="📝"
          accent="border-t-amber-400"
          sub={`${c.states || 0} states · ${c.locations || 0} zones`}
        />


      </div>



      {/* =====================================================
          MAIN GRID
      ===================================================== */}

      <div className="mt-6 grid gap-5 xl:grid-cols-3">



        {/* RISK DISTRIBUTION */}

        <Card title={t('risk.distribution')}>


          <div className="relative h-56">


            <ResponsiveContainer>

              <PieChart>


                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={58}
                  outerRadius={82}
                  paddingAngle={3}
                  strokeWidth={0}
                >

                  {pieData.map((p) => (

                    <Cell
                      key={p.name}
                      fill={p.color}
                    />

                  ))}

                </Pie>


                <Tooltip
                  contentStyle={{
                    borderRadius: 10,
                    fontSize: 12,
                  }}
                />


              </PieChart>

            </ResponsiveContainer>



            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">


              <p className="text-3xl font-extrabold text-govblue-950">

                {c.locations || 0}

              </p>


              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">

                zones

              </p>


            </div>


          </div>



          <div className="grid grid-cols-4 gap-1 text-center">


            {pieData.map((p) => (

              <div key={p.name}>


                <p
                  className="text-lg font-extrabold tabular-nums"
                  style={{ color: p.color }}
                >

                  {p.value}

                </p>


                <p className="text-[9px] font-bold uppercase tracking-wide text-slate-400">

                  {p.name}

                </p>


              </div>

            ))}


          </div>


        </Card>



        {/* RECENT ALERTS */}

        <Card
          title={`🔔 ${t('dashboard.recentAlerts')}`}

          actions={

            <Link
              to="/alerts"
              className="text-xs font-bold text-govblue-800 hover:underline"
            >

              {t('common.viewAll')}

            </Link>

          }

        >


          <ul className="divide-y divide-slate-100">


            {(data.recent_alerts || []).length === 0 && (

              <EmptyState text={t('common.noData')} />

            )}



            {(data.recent_alerts || []).map((a) => (

              <li
                key={a.id}
                className="flex items-center gap-3 py-2.5"
              >


                <span
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-base"

                  style={{

                    backgroundColor:
                      (RISK_META[a.risk_level]?.color || '#888') + '1f',

                  }}

                >

                  {a.risk_level === 'CRITICAL'
                    ? '🚨'
                    : '⚠️'
                  }

                </span>



                <div className="min-w-0 flex-1">


                  <p className="truncate text-sm font-bold text-slate-800">

                    {a.location_name}

                  </p>


                  <p className="truncate text-xs text-slate-500">

                    {a.message
                      ?.split('\n')
                      .filter(Boolean)
                      .slice(-1)[0]
                    }

                  </p>


                </div>



                <div className="shrink-0 text-right">


                  <RiskBadge
                    level={a.risk_level}
                  />


                  <p className="mt-1 text-[10px] text-slate-400">

                    {timeAgo(a.created_at)}

                  </p>


                </div>


              </li>

            ))}


          </ul>


        </Card>



        {/* RECENT REPORTS */}

        <Card
          title={`📝 ${t('dashboard.recentReports')}`}

          actions={

            <Link
              to="/reports"
              className="text-xs font-bold text-govblue-800 hover:underline"
            >

              {t('common.viewAll')}

            </Link>

          }

        >


          <ul className="divide-y divide-slate-100">


            {(data.recent_reports || []).length === 0 && (

              <EmptyState text={t('common.noData')} />

            )}



            {(data.recent_reports || []).map((r) => (

              <li
                key={r.id}
                className="flex items-center gap-3 py-2.5"
              >


                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-base">

                  📷

                </span>



                <div className="min-w-0 flex-1">


                  <p className="truncate text-sm font-bold text-slate-800">

                    {r.report_type?.replace(/_/g, ' ')}

                    {' · '}

                    {r.reporter_name || 'Anonymous'}

                  </p>


                  <p className="truncate text-xs text-slate-500">

                    {r.description}

                  </p>


                </div>



                <StatusPill
                  status={r.status}
                />


              </li>

            ))}


          </ul>


        </Card>


      </div>



      {/* =====================================================
          RISK TREND + TOP RISK
      ===================================================== */}

      <div className="mt-5 grid gap-5 xl:grid-cols-2">



        {/* RISK TREND */}

        <Card title={`📈 ${t('dashboard.trend')}`}>


          <ResponsiveContainer
            width="100%"
            height={235}
          >


            <AreaChart
              data={trendData}

              margin={{
                left: -18,
                right: 6,
                top: 6,
              }}

            >


              <defs>


                <linearGradient
                  id="trendFill"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >


                  <stop
                    offset="0%"
                    stopColor="#1e40af"
                    stopOpacity={0.35}
                  />


                  <stop
                    offset="100%"
                    stopColor="#1e40af"
                    stopOpacity={0.02}
                  />


                </linearGradient>


              </defs>



              <XAxis
                dataKey="time"

                tick={{
                  fontSize: 10,
                  fill: '#64748b',
                }}

                minTickGap={28}
              />


              <YAxis
                domain={[0, 100]}

                tick={{
                  fontSize: 10,
                  fill: '#64748b',
                }}
              />


              <Tooltip
                contentStyle={{
                  borderRadius: 10,
                  fontSize: 12,
                }}
              />


              <Area
                type="monotone"
                dataKey="avg_score"
                name="Avg risk"
                stroke="#1e40af"
                strokeWidth={2.4}
                fill="url(#trendFill)"
              />


            </AreaChart>


          </ResponsiveContainer>


        </Card>



        {/* TOP RISK */}

        <Card
          title={`⚠️ ${t('dashboard.topRisk')}`}
          pad={false}
        >


          <table className="w-full">


            <tbody className="divide-y divide-slate-100">


              {(data.top_risk || []).length === 0 && (

                <tr>

                  <td className="td">

                    <EmptyState
                      text={t('common.noData')}
                    />

                  </td>

                </tr>

              )}



              {(data.top_risk || []).map((z, i) => (

                <tr
                  key={z.location_id}
                  className="hover:bg-slate-50/70"
                >


                  <td className="td w-12 text-center font-extrabold text-slate-300">

                    {i + 1}

                  </td>


                  <td className="td font-bold text-slate-800">

                    {z.name}

                    <span className="ml-2 text-xs font-normal text-slate-400">

                      {z.state}

                    </span>

                  </td>


                  <td className="td text-right">

                    <RiskBadge
                      level={z.risk_level}
                    />

                  </td>


                  <td className="td w-24 text-right font-extrabold tabular-nums text-govblue-950">

                    {fmtNum(
                      z.risk_score,
                      0
                    )}

                  </td>


                </tr>

              ))}


            </tbody>


          </table>


        </Card>


      </div>



      {/* =====================================================
          WEATHER OUTLOOK
      ===================================================== */}

      <div className="mt-5">


        <Card
          title={`🌦️ ${t('risk.forecast')}`}
          pad={false}
        >


          <div className="overflow-x-auto">


            <table className="w-full min-w-[640px]">


              <thead className="border-b border-slate-100 bg-slate-50/70">


                <tr>


                  <th className="th">

                    {t('common.state')}

                  </th>


                  <th className="th text-center">

                    Avg Rainfall

                  </th>


                  <th className="th text-center">

                    Avg Humidity

                  </th>


                  <th className="th text-center">

                    Outlook

                  </th>


                  <th className="th text-center">

                    Zones

                  </th>


                </tr>


              </thead>



              <tbody className="divide-y divide-slate-50">


                {(data.weather_outlook || []).map((w) => (

                  <tr
                    key={w.state}
                    className="hover:bg-slate-50/60"
                  >


                    <td className="td font-bold text-slate-800">

                      {w.state}

                    </td>


                    <td className="td text-center tabular-nums">

                      {fmtNum(
                        w.avg_rainfall,
                        0
                      )} mm

                    </td>


                    <td className="td text-center tabular-nums">

                      {fmtNum(
                        w.avg_humidity,
                        0
                      )}%

                    </td>


                    <td className="td text-center">

                      <RiskBadge
                        level={w.outlook}
                      />

                    </td>


                    <td className="td text-center tabular-nums text-slate-500">

                      {w.locations}

                    </td>


                  </tr>

                ))}


              </tbody>


            </table>


          </div>


        </Card>


      </div>



      {/* =====================================================
          EMERGENCY RESPONSE
          ADMIN + FIELD OFFICER ONLY
      ===================================================== */}

      {(userRole === 'ADMIN' ||
        userRole === 'FIELD_OFFICER') && (

        <Link
          to="/emergency"
          className="mt-5 block"
        >


          <div className="card flex flex-wrap items-center justify-between gap-3 border-l-4 border-l-red-500 p-4 transition hover:shadow-md">


            <div>


              <p className="text-sm font-extrabold text-govblue-950">

                🚑 {t('emergency.title')}

              </p>


              <p className="text-xs text-slate-500">

                PRIORITY 1 → immediate response · live ranking

              </p>


            </div>



            <span className="btn-ghost text-xs">

              {t('common.viewAll')} →

            </span>


          </div>


        </Link>

      )}


    </div>

  );

}