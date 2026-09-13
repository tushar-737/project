import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { useTranslation } from '../i18n';
import { api } from '../services/api';
import { Card, PageHeader, RiskBadge } from '../components/ui';
import { fmtNum } from '../utils/format';
import { RISK_META, SCENARIO_META, SCENARIOS } from '../utils/risk';

const STEP_ICONS = ['🌦️', '📡', '💾', '🧠', '📊', '🗄️', '🗺️', '🚨', '🚑'];

function ScoreGauge({ score }) {
  const r = 56;
  const circ = 2 * Math.PI * r;
  const frac = Math.max(0, Math.min(100, score)) / 100;

  const level =
    score >= 76
      ? 'CRITICAL'
      : score >= 51
        ? 'HIGH'
        : score >= 26
          ? 'MODERATE'
          : 'LOW';

  const color = RISK_META[level].color;

  return (
    <div className="relative mx-auto h-40 w-40">
      <svg viewBox="0 0 140 140" className="h-full w-full -rotate-90">
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="12"
        />

        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - frac)}
          style={{
            transition:
              'stroke-dashoffset 1.1s cubic-bezier(0.22,1,0.36,1)',
          }}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <p
          className="text-4xl font-extrabold tabular-nums"
          style={{ color }}
        >
          {Math.round(score)}
        </p>

        <p className="text-[9px] font-bold uppercase tracking-widest text-slate-400">
          / 100
        </p>
      </div>
    </div>
  );
}

function EnvStat({ label, value, unit, icon }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center">
      <p className="text-lg">{icon}</p>

      <p className="mt-1 text-xl font-extrabold tabular-nums text-govblue-950">
        {fmtNum(value, 1)}
        <span className="text-xs font-bold text-slate-400">
          {' '}
          {unit}
        </span>
      </p>

      <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
        {label}
      </p>
    </div>
  );
}

export default function SimulationCenter() {
  const { t } = useTranslation();

  const navigate = useNavigate();
  const location = useLocation();

  const { data: zones } = useApi('/api/risk/zones');

  const autoFired = useRef(false);
  const timer = useRef(null);

  const [locationId, setLocationId] = useState('');
  const [scenario, setScenario] = useState('EXTREME_RAIN');

  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState('');
  const [result, setResult] = useState(null);
  const [revealed, setRevealed] = useState(0);

  useEffect(() => {
    if (!running && result) {
      setRevealed(0);

      const total = (result.pipeline_steps || []).length;

      let i = 0;

      timer.current = setInterval(() => {
        i += 1;

        setRevealed(i);

        if (i >= total) {
          clearInterval(timer.current);
        }
      }, 420);

      return () => clearInterval(timer.current);
    }

    return undefined;
  }, [result, running]);

  useEffect(() => {
    return () => clearInterval(timer.current);
  }, []);

  useEffect(() => {
    if (
      location.state?.autoDemo &&
      zones?.length &&
      !autoFired.current
    ) {
      autoFired.current = true;
      run({}, true);
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zones, location.state]);

  async function run(body, demo = false) {
    setRunning(true);
    setRunError('');
    setResult(null);

    try {
      const data = await api.post(
        demo
          ? '/api/simulation/run-demo'
          : '/api/simulation/run',
        body || {}
      );

      setResult(data);
    } catch (err) {
      setRunError(err.message || 'Simulation failed');
    } finally {
      setRunning(false);
    }
  }

  const sortedZones = [...(zones || [])].sort(
    (a, b) => b.risk_score - a.risk_score
  );

  const currentZone = zones?.find(
    (z) => z.location_id === Number(locationId)
  );

  return (
    <div>
      <PageHeader
        title={t('simulation.title')}
        icon="🧪"
        subtitle={t('simulation.subtitle')}
        actions={
          <button
            className="btn bg-gradient-to-r from-red-600 to-orange-600 text-white shadow-md hover:from-red-500 hover:to-orange-500"
            disabled={running}
            onClick={() => run({}, true)}
          >
            {running ? 'Running…' : t('simulation.demo')}
          </button>
        }
      />

      <div className="grid gap-5 xl:grid-cols-[400px_1fr]">

        <div className="space-y-4">

          <Card title={`📍 ${t('simulation.location')}`}>
            <select
              className="input"
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
            >
              <option value="">
                — Select Location —
              </option>

              {sortedZones.map((z) => (
                <option
                  key={z.location_id}
                  value={z.location_id}
                >
                  {z.name} · {z.state} ({z.risk_level},{' '}
                  {Math.round(z.risk_score)})
                </option>
              ))}
            </select>

            {currentZone && (
              <div className="mt-3 rounded-xl bg-slate-50 p-3 text-xs">

                <p className="font-extrabold text-govblue-950">
                  {currentZone.name}
                </p>

                <p className="text-slate-500">
                  {currentZone.district},{' '}
                  {currentZone.state} · Elevation{' '}
                  {fmtNum(currentZone.elevation, 0)} m · Slope{' '}
                  {fmtNum(currentZone.slope_angle, 1)}°
                </p>

                <div className="mt-2 flex items-center justify-between">
                  <RiskBadge
                    level={currentZone.risk_level}
                  />

                  <span className="text-xs font-bold">
                    Current {Math.round(currentZone.risk_score)}
                    /100
                  </span>
                </div>

              </div>
            )}
          </Card>

          <Card title={`🌦️ ${t('simulation.scenario')}`}>

            <div className="space-y-2">

              {SCENARIOS.map((sc) => {
                const meta = SCENARIO_META[sc];

                const active = scenario === sc;

                return (
                  <button
                    key={sc}
                    onClick={() => setScenario(sc)}
                    className={`flex w-full items-center gap-3 rounded-xl border-2 px-3.5 py-2.5 text-left transition ${
                      active
                        ? 'border-govblue-800 bg-govblue-50/60 shadow-sm'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >

                    <span className="text-2xl">
                      {meta.icon}
                    </span>

                    <span className="flex-1">

                      <span
                        className={`block text-sm font-extrabold ${
                          active
                            ? 'text-govblue-950'
                            : 'text-slate-700'
                        }`}
                      >
                        {sc.replace(/_/g, ' ')}
                      </span>

                      <span className="block text-[11px] text-slate-400">
                        {t(`simulation.scenarios.${sc}`)}
                      </span>

                    </span>

                    <span
                      className={`h-4 w-4 rounded-full border-2 ${
                        active
                          ? 'border-govblue-800 bg-govblue-800'
                          : 'border-slate-300'
                      }`}
                      style={
                        active
                          ? {
                              boxShadow:
                                'inset 0 0 0 2.5px #fff',
                            }
                          : {}
                      }
                    />

                  </button>
                );
              })}

            </div>

          </Card>

          <button
            className="btn-primary w-full py-3 text-base shadow-md disabled:opacity-60"
            disabled={running || !locationId}
            onClick={() =>
              run({
                location_id: Number(locationId),
                scenario,
              })
            }
          >

            {running ? (
              <span className="flex items-center gap-2">

                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />

                Analysing…

              </span>
            ) : (
              <>⚡ {t('simulation.run')}</>
            )}

          </button>

          <button
            className="btn w-full border-2 border-red-600 bg-white py-3 text-base text-red-600 shadow-md hover:bg-red-50"
            disabled={running}
            onClick={() => run({}, true)}
          >
            🚨 {t('simulation.demo')}
          </button>

          {!locationId && !running && (
            <p className="text-center text-[11px] text-slate-400">
              Select a location to enable scenario runs ·
              demo works automatically
            </p>
          )}

          {runError && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-semibold text-red-700">
              {runError}
            </div>
          )}

          <Card className="border-amber-200 bg-amber-50/70">

            <p className="text-[11px] leading-relaxed text-amber-900">
              ℹ️ {t('simulation.note')}
            </p>

          </Card>

        </div>

        <div className="space-y-4">

          {!result && !running && (

            <Card className="flex min-h-[420px] flex-col items-center justify-center text-center">

              <p className="text-6xl opacity-60">
                🛰️
              </p>

              <h3 className="mt-4 text-lg font-extrabold text-govblue-950">
                DATA → AI → PREDICTION → MAP → ALERT → RESPONSE
              </h3>

              <p className="mt-2 max-w-md text-sm text-slate-500">

                Pick a location and weather scenario, then run a
                simulation. The backend generates environmental data
                and drives the complete landslide early-warning pipeline.

              </p>

              <div className="mt-5 flex flex-wrap justify-center gap-2 text-[11px] font-bold uppercase tracking-wide text-slate-400">

                {STEP_ICONS.map((icon, index) => (
                  <span
                    key={index}
                    className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100"
                  >
                    {icon}
                  </span>
                ))}

              </div>

            </Card>

          )}

          {running && (

            <Card>

              <div className="flex flex-col items-center justify-center gap-4 py-24">

                <div className="relative">

                  <div className="h-14 w-14 animate-spin rounded-full border-4 border-slate-200 border-t-govblue-800" />

                  <span className="absolute inset-0 flex items-center justify-center text-2xl">
                    🧠
                  </span>

                </div>

                <p className="text-sm font-bold text-govblue-950">
                  AI risk engine running…
                </p>

                <p className="text-xs text-slate-400">
                  Saving data → Predicting → Alerting → Prioritising
                </p>

              </div>

            </Card>

          )}

          {result && !running && (

            <>

              <Card
                title={`⚙️ ${t('simulation.steps')} (${result.pipeline_steps.length})`}
                pad={false}
              >

                <ol className="divide-y divide-slate-100">

                  {(result.pipeline_steps || [])
                    .slice(0, revealed)
                    .map((step, index) => (

                      <li
                        key={index}
                        className="flex items-center gap-3 px-5 py-2.5 text-sm transition"
                        style={{
                          animation:
                            'fadeIn .3s',
                        }}
                      >

                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-[11px]">
                          ✓
                        </span>

                        <span className="text-slate-600">
                          {step}
                        </span>

                      </li>

                    ))}

                  {(result.pipeline_steps || [])
                    .slice(revealed)
                    .map((step, index) => (

                      <li
                        key={`pending-${index}`}
                        className="flex items-center gap-3 px-5 py-2.5 text-sm opacity-30"
                      >

                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[11px]">
                          ·
                        </span>

                        <span className="text-slate-400">
                          {step}
                        </span>

                      </li>

                    ))}

                </ol>

              </Card>

              <div className="card overflow-hidden">

               <div className="relative hidden flex-col justify-between bg-gradient-to-br from-govblue-900 via-govblue-950 to-govblue-950 p-10 text-white lg:flex">

                  <div className="rounded-2xl bg-white/95 p-4">

                    <ScoreGauge
                      score={result.risk_score}
                    />

                  </div>

                  <div className="min-w-[240px] flex-1">

                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                      AI RISK SCORE ·{' '}
                      {result.scenario.replace(/_/g, ' ')}
                    </p>

                    <h2 className="mt-1 text-2xl font-extrabold">
                      {result.location_name}
                    </h2>

                    <p className="text-sm text-slate-300">
                      {result.district}, {result.state}
                    </p>

                    <div className="mt-3 flex flex-wrap items-center gap-2">

                      <RiskBadge
                        level={result.risk_level}
                      />

                      <span className="rounded-md bg-white/10 px-2 py-0.5 text-xs font-bold">

                        Confidence{' '}
                        {(result.confidence * 100).toFixed(0)}%

                      </span>

                    </div>

                    <div className="mt-4 flex flex-wrap gap-1.5">

                      {(result.contributing_factors || []).map(
                        (factor) => (

                          <span
                            key={factor}
                            className="rounded-full bg-white/10 px-2.5 py-1 text-[11px] font-semibold text-amber-200 ring-1 ring-white/15"
                          >
                            ⚠️ {factor}
                          </span>

                        )
                      )}

                    </div>

                  </div>

                </div>

                <div className="grid gap-3 p-5 sm:grid-cols-3 lg:grid-cols-5">

                  <EnvStat
                    label="Rainfall"
                    value={result.rainfall}
                    unit="mm/24h"
                    icon="🌧️"
                  />

                  <EnvStat
                    label="Soil Moisture"
                    value={result.soil_moisture}
                    unit="%"
                    icon="🟫"
                  />

                  <EnvStat
                    label="Humidity"
                    value={result.humidity}
                    unit="%"
                    icon="💧"
                  />

                  <EnvStat
                    label="Temperature"
                    value={result.temperature}
                    unit="°C"
                    icon="🌡️"
                  />

                  <EnvStat
                    label="Slope"
                    value={result.slope_angle}
                    unit="°"
                    icon="📐"
                  />

                </div>

                {result.alert_message && (

                  <div
                    className={`mx-5 mb-5 rounded-xl border-2 p-4 ${
                      result.risk_level === 'CRITICAL'
                        ? 'border-red-300 bg-red-50'
                        : 'border-orange-300 bg-orange-50'
                    }`}
                  >

                    <p className="text-xs font-extrabold uppercase tracking-wider text-red-700">

                      {result.risk_level === 'CRITICAL'
                        ? `🚨 ${t('alerts.levelCritical')}`
                        : `⚠️ ${t('alerts.levelHigh')}`}

                      {' · '}

                      {result.sms_log_id
                        ? `SMS #${result.sms_log_id}`
                        : 'SMS not sent'}

                    </p>

                    <pre className="mt-2 whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-800">

                      {result.alert_message}

                    </pre>

                  </div>

                )}

                <div className="flex flex-wrap items-center gap-4 border-t border-slate-100 px-5 py-4">

                  <span className="text-xs font-bold uppercase tracking-wide text-slate-400">
                    Emergency Response
                  </span>

                  <span
                    className={`rounded-lg px-3 py-1.5 text-sm font-extrabold text-white ${
                      result.priority_level === 'PRIORITY 1'
                        ? 'bg-red-600'
                        : result.priority_level === 'PRIORITY 2'
                          ? 'bg-orange-500'
                          : 'bg-yellow-500'
                    }`}
                  >
                    🚑{' '}
                    {result.priority_level || 'PRIORITY 3'}
                  </span>

                  <span className="text-xs font-bold text-slate-500">
                    Score: {fmtNum(result.priority_score, 1)}
                  </span>

                  <span className="ml-auto flex items-center gap-4 text-xs text-slate-400">

                    <span>
                      Alert #{result.alert_id ?? '—'}
                    </span>

                    <span>
                      Environment #{result.environment_id}
                    </span>

                    <button
                      className="font-bold text-govblue-800 hover:underline"
                      onClick={() =>
                        navigate('/map', {
                          state: {
                            focus: result.location_id,
                          },
                        })
                      }
                    >
                      View on Map →
                    </button>

                  </span>

                </div>

              </div>

              <style>
                {`
                  @keyframes fadeIn {
                    from {
                      opacity: 0;
                      transform: translateY(4px);
                    }

                    to {
                      opacity: 1;
                      transform: none;
                    }
                  }
                `}
              </style>

            </>

          )}

        </div>

      </div>
    </div>
  );
}