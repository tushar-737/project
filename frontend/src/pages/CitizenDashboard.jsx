import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function CitizenDashboard() {
  const { user } = useAuth();

  const citizenName =
    user?.name ||
    user?.full_name ||
    'Citizen';

  return (
    <div className="min-h-full space-y-5">

      {/* HERO */}

      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-govblue-950 via-govblue-900 to-blue-700 p-6 text-white shadow-lg">

        <div className="relative z-10">

          <div className="flex flex-wrap items-start justify-between gap-4">

            <div>

              <div className="flex items-center gap-3">

                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-3xl ring-1 ring-white/20">
                  🛡️
                </div>

                <div>
                  <p className="text-xs font-bold uppercase tracking-widest text-blue-200">
                    NER-SHIELD
                  </p>

                  <h1 className="text-2xl font-extrabold">
                    Citizen Safety Portal
                  </h1>
                </div>

              </div>

              <h2 className="mt-6 text-xl font-bold">
                Hello, {citizenName} 👋
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-relaxed text-blue-100">
                Stay informed about landslide risks, road conditions and
                emergency alerts in your area.
              </p>

            </div>

            <div className="rounded-full bg-emerald-500/20 px-4 py-2 text-xs font-bold text-emerald-200 ring-1 ring-emerald-300/30">
              ● SAFETY SYSTEM ACTIVE
            </div>

          </div>

        </div>

      </div>


      {/* AREA STATUS */}

      <div className="rounded-2xl border border-orange-200 bg-gradient-to-br from-orange-50 to-white p-6 shadow-sm">

        <div className="flex flex-wrap items-center justify-between gap-5">

          <div>

            <p className="text-xs font-extrabold uppercase tracking-wider text-slate-500">
              Your Area Status
            </p>

            <div className="mt-2 flex items-center gap-3">

              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-orange-100 text-3xl">
                🟠
              </div>

              <div>

                <h2 className="text-2xl font-extrabold text-orange-600">
                  MODERATE RISK
                </h2>

                <p className="text-sm text-slate-500">
                  Monitor weather updates and follow safety instructions.
                </p>

              </div>

            </div>

          </div>


          <Link
            to="/map"
            className="btn-primary"
          >
            📍 CHECK MY AREA
          </Link>

        </div>

      </div>


      {/* QUICK ACTIONS */}

      <div>

        <div className="mb-3">

          <h2 className="text-lg font-extrabold text-govblue-950">
            Quick Safety Actions
          </h2>

          <p className="text-sm text-slate-500">
            Important services for citizens and local communities.
          </p>

        </div>


        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">


          <Link
            to="/alerts"
            className="group rounded-2xl border border-red-100 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-md"
          >

            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-50 text-2xl">
              🚨
            </div>

            <h3 className="mt-4 font-extrabold text-slate-800">
              Safety Alerts
            </h3>

            <p className="mt-1 text-xs leading-relaxed text-slate-500">
              View active warnings and emergency notifications.
            </p>

            <p className="mt-4 text-xs font-bold text-red-600">
              VIEW ALERTS →
            </p>

          </Link>


          <Link
            to="/reports"
            className="group rounded-2xl border border-blue-100 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-md"
          >

            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-2xl">
              📸
            </div>

            <h3 className="mt-4 font-extrabold text-slate-800">
              Report Incident
            </h3>

            <p className="mt-1 text-xs leading-relaxed text-slate-500">
              Report cracks, landslides or blocked roads.
            </p>

            <p className="mt-4 text-xs font-bold text-blue-700">
              SUBMIT REPORT →
            </p>

          </Link>


          <Link
            to="/roads"
            className="group rounded-2xl border border-orange-100 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-md"
          >

            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-50 text-2xl">
              🛣️
            </div>

            <h3 className="mt-4 font-extrabold text-slate-800">
              Road Status
            </h3>

            <p className="mt-1 text-xs leading-relaxed text-slate-500">
              Check road connectivity before travelling.
            </p>

            <p className="mt-4 text-xs font-bold text-orange-600">
              CHECK ROADS →
            </p>

          </Link>


          <Link
            to="/map"
            className="group rounded-2xl border border-emerald-100 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-md"
          >

            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-2xl">
              🗺️
            </div>

            <h3 className="mt-4 font-extrabold text-slate-800">
              Risk Map
            </h3>

            <p className="mt-1 text-xs leading-relaxed text-slate-500">
              Explore landslide risk zones near you.
            </p>

            <p className="mt-4 text-xs font-bold text-emerald-600">
              OPEN MAP →
            </p>

          </Link>

        </div>

      </div>


      {/* SAFETY INFORMATION */}

      <div className="grid gap-5 lg:grid-cols-2">


        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

          <h2 className="text-lg font-extrabold text-govblue-950">
            🌧️ Current Safety Conditions
          </h2>

          <div className="mt-4 space-y-3">

            <div className="flex items-center justify-between rounded-xl bg-blue-50 p-4">

              <span className="text-sm font-semibold text-slate-600">
                🌧️ Rainfall Activity
              </span>

              <span className="font-extrabold text-blue-700">
                Moderate
              </span>

            </div>


            <div className="flex items-center justify-between rounded-xl bg-cyan-50 p-4">

              <span className="text-sm font-semibold text-slate-600">
                💧 Soil Condition
              </span>

              <span className="font-extrabold text-cyan-700">
                Monitor
              </span>

            </div>


            <div className="flex items-center justify-between rounded-xl bg-orange-50 p-4">

              <span className="text-sm font-semibold text-slate-600">
                ⛰️ Landslide Risk
              </span>

              <span className="font-extrabold text-orange-600">
                Moderate
              </span>

            </div>

          </div>

        </div>


        <div className="rounded-2xl border border-red-200 bg-gradient-to-br from-red-50 to-white p-5 shadow-sm">

          <h2 className="text-lg font-extrabold text-red-700">
            🚨 Emergency Information
          </h2>

          <p className="mt-2 text-sm text-slate-600">
            If you observe a landslide, slope movement or immediate danger,
            move to a safe location and contact emergency services.
          </p>


          <div className="mt-5 grid grid-cols-2 gap-3">

            <div className="rounded-xl bg-white p-4 text-center shadow-sm">

              <p className="text-2xl font-extrabold text-red-600">
                112
              </p>

              <p className="mt-1 text-[10px] font-bold uppercase text-slate-400">
                Emergency
              </p>

            </div>


            <Link
              to="/emergency"
              className="rounded-xl bg-red-600 p-4 text-center text-white shadow-sm transition hover:bg-red-700"
            >

              <p className="text-lg font-extrabold">
                SOS
              </p>

              <p className="mt-1 text-[10px] font-bold uppercase text-red-100">
                Response Center
              </p>

            </Link>

          </div>

        </div>

      </div>


      {/* SAFETY TIPS */}

      <div className="rounded-2xl border border-govblue-100 bg-govblue-50 p-5">

        <h2 className="text-lg font-extrabold text-govblue-950">
          🛡️ Landslide Safety Tips
        </h2>

        <div className="mt-4 grid gap-3 md:grid-cols-3">

          <div className="rounded-xl bg-white p-4">
            <p className="font-bold text-slate-800">
              👀 Stay Alert
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Watch for cracks, unusual sounds and slope movement.
            </p>
          </div>

          <div className="rounded-xl bg-white p-4">
            <p className="font-bold text-slate-800">
              🚫 Avoid Danger Zones
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Avoid travelling through high-risk areas during heavy rainfall.
            </p>
          </div>

          <div className="rounded-xl bg-white p-4">
            <p className="font-bold text-slate-800">
              📱 Report Early
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Report visible warning signs to help authorities respond faster.
            </p>
          </div>

        </div>

      </div>

    </div>
  );
}