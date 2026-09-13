import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { useTranslation } from '../i18n';

import {
  Card,
  EmptyState,
  ErrorBox,
  PageHeader,
  RiskBadge,
  ScoreBar,
  Spinner,
} from '../components/ui';

import { fmtNum, timeAgo } from '../utils/format';
import { RISK_LEVELS, STATES } from '../utils/risk';


export default function Monitoring() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const {
    data: zones,
    loading,
    error,
    refresh,
  } = useApi('/api/risk/zones', { pollMs: 15000 });

  const [search, setSearch] = useState('');
  const [state, setState] = useState('');
  const [level, setLevel] = useState('');


  // =========================================================
  // FILTERED LOCATIONS
  // =========================================================

  const rows = useMemo(() => {
    if (!zones) return [];

    const q = search.trim().toLowerCase();

    return zones.filter((z) => {
      if (
        q &&
        !`${z.name} ${z.district} ${z.state}`
          .toLowerCase()
          .includes(q)
      ) {
        return false;
      }

      if (state && z.state !== state) return false;

      if (level && z.risk_level !== level) return false;

      return true;
    });
  }, [zones, search, state, level]);


  // =========================================================
  // TERRAIN INTELLIGENCE STATISTICS
  // =========================================================

  const stats = useMemo(() => {
    if (!zones || zones.length === 0) {
      return {
        avgElevation: 0,
        avgSlope: 0,
        maxSlope: 0,
        highSusceptibility: 0,
        highRisk: 0,
      };
    }

    const elevations = zones
      .map((z) => Number(z.elevation))
      .filter((v) => Number.isFinite(v));

    const slopes = zones
      .map((z) => Number(z.slope_angle))
      .filter((v) => Number.isFinite(v));

    const historical = zones
      .map((z) => Number(z.historical_landslide_factor))
      .filter((v) => Number.isFinite(v));

    const avgElevation =
      elevations.length > 0
        ? elevations.reduce((a, b) => a + b, 0) / elevations.length
        : 0;

    const avgSlope =
      slopes.length > 0
        ? slopes.reduce((a, b) => a + b, 0) / slopes.length
        : 0;

    const maxSlope =
      slopes.length > 0
        ? Math.max(...slopes)
        : 0;

    const highSusceptibility = historical.filter(
      (v) => v >= 0.6
    ).length;

    const highRisk = zones.filter(
      (z) =>
        z.risk_level === 'HIGH' ||
        z.risk_level === 'CRITICAL'
    ).length;

    return {
      avgElevation,
      avgSlope,
      maxSlope,
      highSusceptibility,
      highRisk,
    };
  }, [zones]);


  return (
    <div>

      {/* =====================================================
          PAGE HEADER
      ===================================================== */}

      <PageHeader
        title="Satellite & Terrain Intelligence"
        icon="🛰️"
        subtitle={`${zones?.length || 0} monitored locations · live refresh every 15 seconds`}
        actions={
          <button
            onClick={refresh}
            className="btn-ghost text-xs"
          >
            ↻ {t('common.refresh')}
          </button>
        }
      />


      {/* =====================================================
          REMOTE SENSING INFORMATION
      ===================================================== */}

      <Card className="mb-4">

        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">

          <div>

            <div className="flex items-center gap-2">

              <span className="text-xl">🛰️</span>

              <h2 className="font-bold text-slate-800">
                Remote Sensing & Terrain Intelligence
              </h2>

            </div>

            <p className="mt-1 text-sm text-slate-500">

              Geographic terrain parameters, slope characteristics,
              elevation and historical landslide susceptibility are
              integrated with live environmental conditions to support
              AI-based landslide risk assessment.

            </p>

          </div>


          <div className="flex items-center gap-2">

            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />

            <span className="text-xs font-semibold text-emerald-700">

              TERRAIN DATA ACTIVE

            </span>

          </div>

        </div>

      </Card>


      {/* =====================================================
          INTELLIGENCE STATISTICS
      ===================================================== */}

      {zones && (

        <div className="mb-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">


          {/* MONITORED LOCATIONS */}

          <Card>

            <div className="flex items-start justify-between">

              <div>

                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">

                  Locations

                </p>

                <p className="mt-2 text-2xl font-bold text-slate-800">

                  {zones.length}

                </p>

                <p className="mt-1 text-xs text-slate-500">

                  Across NER

                </p>

              </div>

              <span className="text-2xl">📍</span>

            </div>

          </Card>


          {/* AVERAGE ELEVATION */}

          <Card>

            <div className="flex items-start justify-between">

              <div>

                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">

                  Avg Elevation

                </p>

                <p className="mt-2 text-2xl font-bold text-slate-800">

                  {fmtNum(stats.avgElevation, 0)} m

                </p>

                <p className="mt-1 text-xs text-slate-500">

                  Terrain profile

                </p>

              </div>

              <span className="text-2xl">⛰️</span>

            </div>

          </Card>


          {/* AVERAGE SLOPE */}

          <Card>

            <div className="flex items-start justify-between">

              <div>

                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">

                  Avg Slope

                </p>

                <p className="mt-2 text-2xl font-bold text-slate-800">

                  {fmtNum(stats.avgSlope, 1)}°

                </p>

                <p className="mt-1 text-xs text-slate-500">

                  Terrain gradient

                </p>

              </div>

              <span className="text-2xl">📐</span>

            </div>

          </Card>


          {/* HIGH SUSCEPTIBILITY */}

          <Card>

            <div className="flex items-start justify-between">

              <div>

                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">

                  Historical Risk

                </p>

                <p className="mt-2 text-2xl font-bold text-amber-600">

                  {stats.highSusceptibility}

                </p>

                <p className="mt-1 text-xs text-slate-500">

                  High susceptibility

                </p>

              </div>

              <span className="text-2xl">📚</span>

            </div>

          </Card>


          {/* HIGH RISK */}

          <Card>

            <div className="flex items-start justify-between">

              <div>

                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">

                  Active Risk

                </p>

                <p className="mt-2 text-2xl font-bold text-red-600">

                  {stats.highRisk}

                </p>

                <p className="mt-1 text-xs text-slate-500">

                  High / Critical

                </p>

              </div>

              <span className="text-2xl">⚠️</span>

            </div>

          </Card>

        </div>

      )}


      {/* =====================================================
          AI / TERRAIN EXPLANATION
      ===================================================== */}

      {zones && (

        <Card className="mb-4">

          <div className="grid gap-5 lg:grid-cols-2">


            {/* DATA SOURCES */}

            <div>

              <div className="mb-3 flex items-center gap-2">

                <span className="text-lg">🛰️</span>

                <h3 className="font-bold text-slate-800">

                  Geographic Intelligence Layer

                </h3>

              </div>


              <div className="grid grid-cols-2 gap-3">


                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">

                  <p className="font-semibold text-slate-700">

                    ⛰️ Elevation

                  </p>

                  <p className="mt-1 text-xs text-slate-500">

                    Geographic terrain profile

                  </p>

                </div>


                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">

                  <p className="font-semibold text-slate-700">

                    📐 Slope

                  </p>

                  <p className="mt-1 text-xs text-slate-500">

                    Terrain instability indicator

                  </p>

                </div>


                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">

                  <p className="font-semibold text-slate-700">

                    📚 History

                  </p>

                  <p className="mt-1 text-xs text-slate-500">

                    Landslide susceptibility

                  </p>

                </div>


                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">

                  <p className="font-semibold text-slate-700">

                    📍 GIS

                  </p>

                  <p className="mt-1 text-xs text-slate-500">

                    Location-based intelligence

                  </p>

                </div>

              </div>

            </div>


            {/* AI FLOW */}

            <div>

              <div className="mb-3 flex items-center gap-2">

                <span className="text-lg">🤖</span>

                <h3 className="font-bold text-slate-800">

                  AI Risk Integration

                </h3>

              </div>


              <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4">

                <div className="flex flex-wrap items-center justify-center gap-2 text-xs font-semibold text-slate-600">

                  <span className="rounded-lg bg-white px-3 py-2 shadow-sm">

                    🌧️ Rainfall

                  </span>

                  <span>+</span>

                  <span className="rounded-lg bg-white px-3 py-2 shadow-sm">

                    💧 Soil

                  </span>

                  <span>+</span>

                  <span className="rounded-lg bg-white px-3 py-2 shadow-sm">

                    ⛰️ Terrain

                  </span>

                  <span>+</span>

                  <span className="rounded-lg bg-white px-3 py-2 shadow-sm">

                    📚 History

                  </span>

                </div>


                <div className="my-3 text-center text-lg">

                  ↓

                </div>


                <div className="rounded-lg bg-white p-3 text-center shadow-sm">

                  <p className="font-bold text-blue-700">

                    Hybrid AI / ML Risk Engine

                  </p>

                  <p className="mt-1 text-xs text-slate-500">

                    Dynamic environmental + terrain risk analysis

                  </p>

                </div>


                <div className="my-3 text-center text-lg">

                  ↓

                </div>


                <div className="text-center">

                  <span className="rounded-full bg-slate-800 px-4 py-2 text-xs font-bold text-white">

                    LANDSLIDE RISK SCORE 0–100

                  </span>

                </div>

              </div>

            </div>

          </div>

        </Card>

      )}


      {/* =====================================================
          FILTERS
      ===================================================== */}

      <div className="mb-4 grid gap-3 md:grid-cols-[1fr_220px_220px]">

        <input
          className="input"
          placeholder={t('common.search')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />


        <select
          className="input"
          value={state}
          onChange={(e) => setState(e.target.value)}
        >

          <option value="">

            {t('common.allStates')}

          </option>


          {STATES.map((s) => (

            <option key={s} value={s}>

              {s}

            </option>

          ))}

        </select>


        <select
          className="input"
          value={level}
          onChange={(e) => setLevel(e.target.value)}
        >

          <option value="">

            {t('common.allLevels')}

          </option>


          {RISK_LEVELS.map((l) => (

            <option key={l} value={l}>

              {t(`risk.${l.toLowerCase()}`)} ({l})

            </option>

          ))}

        </select>

      </div>


      {/* =====================================================
          LOADING
      ===================================================== */}

      {loading && !zones && (

        <Spinner label={t('common.loading')} />

      )}


      {/* =====================================================
          ERROR
      ===================================================== */}

      {error && !zones && (

        <ErrorBox
          message={error}
          onRetry={refresh}
          t={t}
        />

      )}


      {/* =====================================================
          TERRAIN INTELLIGENCE TABLE
      ===================================================== */}

      {zones && (

        <Card pad={false}>

          <div className="border-b border-slate-100 px-4 py-3">

            <div className="flex items-center justify-between">

              <div>

                <h2 className="font-bold text-slate-800">

                  🛰️ Location Terrain Intelligence

                </h2>

                <p className="mt-1 text-xs text-slate-400">

                  Environmental, terrain and historical susceptibility data

                </p>

              </div>

            </div>

          </div>


          <div className="overflow-x-auto">

            <table className="w-full min-w-[1250px]">

              <thead className="border-b border-slate-100 bg-slate-50/70">

                <tr>

                  <th className="th">

                    Location

                  </th>


                  <th className="th text-center">

                    Elevation

                  </th>


                  <th className="th text-center">

                    Rainfall

                  </th>


                  <th className="th text-center">

                    Soil

                  </th>


                  <th className="th text-center">

                    Slope

                  </th>


                  <th className="th text-center">

                    Historical

                  </th>


                  <th className="th text-center">

                    AI Score

                  </th>


                  <th className="th text-center">

                    Risk Level

                  </th>


                  <th className="th text-center">

                    Updated

                  </th>

                </tr>

              </thead>


              <tbody className="divide-y divide-slate-100">

                {rows.length === 0 && (

                  <tr>

                    <td
                      className="td"
                      colSpan={9}
                    >

                      <EmptyState
                        text={t('common.noData')}
                      />

                    </td>

                  </tr>

                )}


                {rows.map((z) => (

                  <tr
                    key={z.location_id}
                    className="cursor-pointer transition hover:bg-govblue-50/50"
                    onClick={() =>
                      navigate('/map', {
                        state: {
                          focus: z.location_id,
                        },
                      })
                    }
                  >

                    {/* LOCATION */}

                    <td className="td">

                      <p className="font-bold text-slate-800">

                        {z.name}

                      </p>

                      <p className="text-xs text-slate-400">

                        {z.district}, {z.state}

                      </p>

                    </td>


                    {/* ELEVATION */}

                    <td className="td text-center font-semibold tabular-nums text-slate-700">

                      {fmtNum(z.elevation, 0)} m

                    </td>


                    {/* RAINFALL */}

                    <td className="td text-center font-semibold tabular-nums text-blue-700">

                      {fmtNum(z.rainfall, 0)} mm

                    </td>


                    {/* SOIL */}

                    <td className="td text-center font-semibold tabular-nums text-emerald-700">

                      {fmtNum(z.soil_moisture, 0)}%

                    </td>


                    {/* SLOPE */}

                    <td className="td text-center tabular-nums text-slate-600">

                      {fmtNum(z.slope_angle, 1)}°

                    </td>


                    {/* HISTORICAL SUSCEPTIBILITY */}

                    <td className="td text-center">

                      {Number.isFinite(
                        Number(z.historical_landslide_factor)
                      ) ? (

                        <div>

                          <p className="font-semibold text-amber-700">

                            {fmtNum(
                              z.historical_landslide_factor * 100,
                              0
                            )}%

                          </p>

                          <p className="text-[10px] text-slate-400">

                            susceptibility

                          </p>

                        </div>

                      ) : (

                        <span className="text-slate-400">

                          —

                        </span>

                      )}

                    </td>


                    {/* AI SCORE */}

                    <td className="td text-center">

                      <ScoreBar
                        score={z.risk_score}
                      />

                    </td>


                    {/* RISK LEVEL */}

                    <td className="td text-center">

                      <RiskBadge
                        level={z.risk_level}
                      />

                    </td>


                    {/* UPDATED */}

                    <td className="td text-center text-xs text-slate-400">

                      {timeAgo(z.last_updated)}

                    </td>

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