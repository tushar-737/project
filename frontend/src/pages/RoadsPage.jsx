import { useMemo, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useTranslation } from '../i18n';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

import {
  Card,
  EmptyState,
  ErrorBox,
  PageHeader,
  RoadBadge,
  Spinner,
} from '../components/ui';

import { fmtDate } from '../utils/format';
import { ROAD_META } from '../utils/risk';


const STATUSES = [
  'OPEN',
  'HIGH_RISK',
  'PARTIALLY_BLOCKED',
  'BLOCKED',
];


function getStatusIcon(status) {
  switch (status) {
    case 'OPEN':
      return '🟢';

    case 'HIGH_RISK':
      return '🟠';

    case 'PARTIALLY_BLOCKED':
      return '⚠️';

    case 'BLOCKED':
      return '🔴';

    default:
      return '⚪';
  }
}


function getStatusDescription(status) {
  switch (status) {
    case 'OPEN':
      return 'Road currently operational';

    case 'HIGH_RISK':
      return 'Landslide risk detected near corridor';

    case 'PARTIALLY_BLOCKED':
      return 'Traffic movement partially affected';

    case 'BLOCKED':
      return 'Road connectivity disrupted';

    default:
      return 'Road status unavailable';
  }
}


export default function RoadsPage() {

  const { t } = useTranslation();

  const { isOfficer } = useAuth();


  const {
    data: roads,
    loading,
    error,
    refresh,
  } = useApi(
    '/api/roads',
    {
      pollMs: 20000,
    }
  );


  const [filter, setFilter] = useState('');

  const [busyId, setBusyId] = useState(null);

  const [search, setSearch] = useState('');


  // =========================================================
  // ROAD STATISTICS
  // =========================================================

  const counts = useMemo(() => {

    const c = {
      OPEN: 0,
      HIGH_RISK: 0,
      PARTIALLY_BLOCKED: 0,
      BLOCKED: 0,
    };


    (roads || []).forEach((road) => {

      if (c[road.status] !== undefined) {

        c[road.status] += 1;

      }

    });


    return c;

  }, [roads]);



  const totalRoads = roads?.length || 0;


  const affectedRoads =
    counts.HIGH_RISK +
    counts.PARTIALLY_BLOCKED +
    counts.BLOCKED;


  const connectivityPercentage = useMemo(() => {

    if (!totalRoads) return 0;


    return Math.round(

      (counts.OPEN / totalRoads) * 100

    );

  }, [counts, totalRoads]);



  // =========================================================
  // FILTERED ROADS
  // =========================================================

  const rows = useMemo(() => {

    return (roads || []).filter((road) => {


      const statusMatch =
        !filter ||
        road.status === filter;


      const searchText = search.toLowerCase();


      const searchMatch =
        !search ||

        road.name
          .toLowerCase()
          .includes(searchText) ||

        road.district
          .toLowerCase()
          .includes(searchText) ||

        road.state
          .toLowerCase()
          .includes(searchText);


      return statusMatch && searchMatch;

    });

  }, [roads, filter, search]);



  // =========================================================
  // UPDATE ROAD STATUS
  // =========================================================

  async function setStatus(road, status) {

    setBusyId(road.id);


    try {

      await api.put(

        `/api/roads/${road.id}`,

        {
          status,
        }

      );


      await refresh();


    } catch (err) {

      console.error(
        'Failed to update road status:',
        err
      );


      alert(
        err?.message ||
        'Unable to update road status'
      );


    } finally {

      setBusyId(null);

    }

  }



  return (

    <div className="space-y-6">


      {/* =====================================================
          PAGE HEADER
      ====================================================== */}

      <PageHeader

        title="🛣️ Road Connectivity Intelligence"

        icon="🛣️"

        subtitle="Live monitoring of vulnerable road corridors across the North Eastern Region"

      />



      {/* =====================================================
          COMMAND CENTER STATUS
      ====================================================== */}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">


        {/* TOTAL ROADS */}

        <Card>

          <div className="flex items-center justify-between">


            <div>

              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">

                Monitored Corridors

              </p>


              <p className="mt-2 text-3xl font-extrabold text-govblue-950">

                {totalRoads}

              </p>


              <p className="mt-1 text-xs text-slate-500">

                Active GIS road monitoring

              </p>

            </div>


            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-govblue-50 text-2xl">

              🛣️

            </div>


          </div>

        </Card>



        {/* OPEN */}

        <Card>

          <div className="flex items-center justify-between">


            <div>

              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">

                Operational

              </p>


              <p className="mt-2 text-3xl font-extrabold text-emerald-600">

                {counts.OPEN}

              </p>


              <p className="mt-1 text-xs text-slate-500">

                Roads currently open

              </p>

            </div>


            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-2xl">

              🟢

            </div>


          </div>

        </Card>



        {/* AFFECTED */}

        <Card>

          <div className="flex items-center justify-between">


            <div>

              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">

                At Risk

              </p>


              <p className="mt-2 text-3xl font-extrabold text-amber-600">

                {affectedRoads}

              </p>


              <p className="mt-1 text-xs text-slate-500">

                Requires monitoring

              </p>

            </div>


            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50 text-2xl">

              ⚠️

            </div>


          </div>

        </Card>



        {/* BLOCKED */}

        <Card>

          <div className="flex items-center justify-between">


            <div>

              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">

                Connectivity Lost

              </p>


              <p className="mt-2 text-3xl font-extrabold text-red-600">

                {counts.BLOCKED}

              </p>


              <p className="mt-1 text-xs text-slate-500">

                Roads currently blocked

              </p>

            </div>


            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-50 text-2xl">

              🚫

            </div>


          </div>

        </Card>


      </div>



      {/* =====================================================
          CONNECTIVITY INTELLIGENCE
      ====================================================== */}

      <Card>


        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">


          <div>


            <div className="flex items-center gap-2">


              <span className="text-xl">

                📡

              </span>


              <h2 className="font-bold text-slate-900">

                Regional Connectivity Intelligence

              </h2>


              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-emerald-700">

                LIVE

              </span>


            </div>


            <p className="mt-2 max-w-2xl text-sm text-slate-500">

              Road corridors are continuously evaluated using
              landslide risk intelligence. High-risk environmental
              conditions can automatically affect road connectivity
              status.

            </p>


          </div>



          <div className="min-w-[240px]">


            <div className="mb-2 flex justify-between text-xs font-bold">


              <span className="text-slate-500">

                Connectivity

              </span>


              <span className="text-govblue-900">

                {connectivityPercentage}%

              </span>


            </div>


            <div className="h-3 overflow-hidden rounded-full bg-slate-100">


              <div

                className="h-full rounded-full bg-govblue-700 transition-all duration-500"

                style={{

                  width: `${connectivityPercentage}%`,

                }}

              />


            </div>


            <p className="mt-2 text-[11px] text-slate-400">

              {counts.OPEN} of {totalRoads} monitored corridors
              currently operational

            </p>


          </div>


        </div>


      </Card>



      {/* =====================================================
          STATUS FILTERS
      ====================================================== */}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">


        {STATUSES.map((status) => (


          <button

            key={status}

            onClick={() => {

              setFilter(

                filter === status
                  ? ''
                  : status

              );

            }}

            className={`card group flex items-center gap-3 p-4 text-left transition-all hover:-translate-y-0.5 hover:shadow-md ${
              filter === status
                ? 'ring-2 ring-govblue-700'
                : ''
            }`}

          >


            <div

              className="flex h-10 w-10 items-center justify-center rounded-xl text-lg"

              style={{

                background:
                  `${ROAD_META[status].color}18`,

              }}

            >


              {getStatusIcon(status)}


            </div>



            <div>


              <div className="text-2xl font-extrabold text-govblue-950">


                {counts[status] || 0}


              </div>


              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">


                {status.replace(/_/g, ' ')}


              </div>


            </div>


          </button>


        ))}


      </div>



      {/* =====================================================
          SEARCH + REFRESH
      ====================================================== */}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">


        <div className="flex flex-1 items-center gap-3">


          <div className="relative w-full max-w-md">


            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm">


              🔍

            </span>


            <input

              value={search}

              onChange={(event) => {

                setSearch(event.target.value);

              }}

              placeholder="Search road, district or state..."

              className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-4 text-sm outline-none transition focus:border-govblue-500 focus:ring-2 focus:ring-govblue-100"

            />


          </div>



          {(filter || search) && (


            <button

              onClick={() => {

                setFilter('');
                setSearch('');

              }}

              className="rounded-lg px-3 py-2 text-xs font-bold text-slate-500 transition hover:bg-slate-100"

            >


              Clear


            </button>


          )}


        </div>



        <button

          onClick={refresh}

          className="rounded-xl bg-govblue-800 px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-govblue-900"

        >


          🔄 Refresh Intelligence


        </button>


      </div>



      {/* =====================================================
          LOADING
      ====================================================== */}

      {loading && !roads && (


        <Spinner

          label="Loading road intelligence..."

        />


      )}



      {/* =====================================================
          ERROR
      ====================================================== */}

      {error && !roads && (


        <ErrorBox

          message={error}

          onRetry={refresh}

          t={t}

        />


      )}



      {/* =====================================================
          ROAD TABLE
      ====================================================== */}

      {roads && (


        <Card pad={false}>


          {/* TABLE HEADER */}

          <div className="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">


            <div>


              <h2 className="font-bold text-slate-900">


                🛰️ Live Road Connectivity Monitor


              </h2>


              <p className="mt-1 text-xs text-slate-400">


                Showing {rows.length} of {totalRoads} monitored
                road corridors


              </p>


            </div>



            <div className="text-[11px] text-slate-400">


              Auto-refresh: every 20 seconds


            </div>


          </div>



          <div className="overflow-x-auto">


            <table className="w-full min-w-[950px]">


              <thead className="border-b border-slate-100 bg-slate-50/70">


                <tr>


                  <th className="th">

                    Road Corridor

                  </th>


                  <th className="th">

                    Location

                  </th>


                  <th className="th text-center">

                    Connectivity

                  </th>


                  <th className="th text-center">

                    AI Risk

                  </th>


                  <th className="th">

                    Intelligence

                  </th>


                  <th className="th text-center">

                    Last Updated

                  </th>


                  {isOfficer && (

                    <th className="th text-right">

                      Control

                    </th>

                  )}


                </tr>


              </thead>



              <tbody className="divide-y divide-slate-100">


                {/* EMPTY STATE */}

                {rows.length === 0 && (


                  <tr>


                    <td

                      className="td"

                      colSpan={
                        isOfficer
                          ? 7
                          : 6
                      }

                    >


                      <EmptyState

                        text="No road corridors found"

                      />


                    </td>


                  </tr>


                )}



                {/* ROAD ROWS */}

                {rows.map((road) => (


                  <tr

                    key={road.id}

                    className="transition hover:bg-slate-50/70"

                  >


                    {/* ROAD NAME */}

                    <td className="td">


                      <div className="flex items-center gap-3">


                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100">


                          🛣️


                        </div>


                        <div>


                          <p className="font-bold text-slate-800">


                            {road.name}


                          </p>


                          <p className="mt-0.5 text-[11px] text-slate-400">


                            Corridor ID #{road.id}


                          </p>


                        </div>


                      </div>


                    </td>



                    {/* LOCATION */}

                    <td className="td">


                      <p className="font-semibold text-slate-700">


                        {road.district}


                      </p>


                      <p className="mt-0.5 text-xs text-slate-400">


                        {road.state}


                      </p>


                    </td>



                    {/* STATUS */}

                    <td className="td text-center">


                      <div className="flex flex-col items-center gap-1">


                        <RoadBadge

                          status={road.status}

                        />


                        <span className="text-[10px] text-slate-400">


                          {getStatusIcon(road.status)}


                        </span>


                      </div>


                    </td>



                    {/* RISK */}

                    <td className="td text-center">


                      <span

                        className="inline-flex rounded-full px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wide"

                        style={{

                          background:

                            road.risk_level === 'CRITICAL'

                              ? '#fee2e2'

                              : road.risk_level === 'HIGH'

                              ? '#ffedd5'

                              : road.risk_level === 'MODERATE'

                              ? '#fef3c7'

                              : '#dcfce7',


                          color:

                            road.risk_level === 'CRITICAL'

                              ? '#dc2626'

                              : road.risk_level === 'HIGH'

                              ? '#ea580c'

                              : road.risk_level === 'MODERATE'

                              ? '#b45309'

                              : '#16a34a',

                        }}

                      >


                        {road.risk_level}


                      </span>


                    </td>



                    {/* INTELLIGENCE */}

                    <td className="td">


                      <p className="max-w-[220px] text-xs leading-relaxed text-slate-500">


                        {getStatusDescription(
                          road.status
                        )}


                      </p>


                    </td>



                    {/* UPDATED */}

                    <td className="td text-center">


                      <span className="text-xs text-slate-400">


                        {fmtDate(
                          road.updated_at
                        )}


                      </span>


                    </td>



                    {/* OFFICER CONTROLS */}

                    {isOfficer && (


                      <td className="td text-right">


                        <div className="flex justify-end gap-1.5">


                          {STATUSES.map((status) => (


                            <button

                              key={status}

                              disabled={
                                busyId === road.id
                              }

                              onClick={() =>

                                setStatus(
                                  road,
                                  status
                                )

                              }

                              title={
                                status.replace(
                                  /_/g,
                                  ' '
                                )
                              }

                              className={`rounded-md px-2 py-1.5 text-[9px] font-extrabold uppercase tracking-wide transition disabled:cursor-not-allowed disabled:opacity-40 ${
                                road.status === status

                                  ? 'text-white'

                                  : 'border border-slate-200 bg-white text-slate-500 hover:border-slate-400'
                              }`}

                              style={

                                road.status === status

                                  ? {

                                      background:
                                        ROAD_META[
                                          status
                                        ].color,

                                    }

                                  : {}

                              }

                            >


                              {status === 'OPEN'
                                ? 'OPEN'
                                : status === 'HIGH_RISK'
                                ? 'RISK'
                                : status === 'PARTIALLY_BLOCKED'
                                ? 'PART'
                                : 'BLOCK'}


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



          {/* =================================================
              FOOTER
          ================================================== */}

          <div className="flex flex-col gap-2 border-t border-slate-100 bg-slate-50/50 px-5 py-3 text-[11px] text-slate-400 md:flex-row md:items-center md:justify-between">


            <span>


              🤖 Road intelligence integrates environmental
              risk assessment with connectivity monitoring.


            </span>


            {isOfficer && (


              <span>


                👮 Officer updates automatically recalculate
                emergency priority.


              </span>


            )}


          </div>


        </Card>


      )}



      {/* =====================================================
          AI INFORMATION PANEL
      ====================================================== */}

      <Card>


        <div className="flex gap-4">


          <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-xl">


            🤖


          </div>



          <div>


            <h3 className="font-bold text-slate-900">


              AI Road Intelligence


            </h3>


            <p className="mt-1 text-sm leading-relaxed text-slate-500">


              NER LandslideAI evaluates landslide risk around
              monitored locations and uses this intelligence to
              support road connectivity assessment. Critical
              environmental conditions can increase the operational
              risk of nearby corridors and influence emergency
              response priority.


            </p>


            <div className="mt-3 flex flex-wrap gap-2">


              <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-bold text-slate-600">


                🌧️ Rainfall


              </span>


              <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-bold text-slate-600">


                💧 Soil Moisture


              </span>


              <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-bold text-slate-600">


                ⛰️ Terrain


              </span>


              <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-bold text-slate-600">


                📍 GIS Location


              </span>


              <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-bold text-slate-600">


                🚨 Emergency Priority


              </span>


            </div>


          </div>


        </div>


      </Card>


    </div>

  );

}