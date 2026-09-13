import { useEffect, useMemo, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';

import {
  isOnline,
  syncPendingReports,
  subscribeOnline,
} from '../services/offline';

import { useTranslation } from '../i18n';
import { useAuth } from '../context/AuthContext';
import { LangSwitch } from './ui';

import UtilityBar from './UtilityBar';
import Footer from './Footer';


/* =========================================================
   NAVIGATION CONFIGURATION
========================================================= */

const NAV = [
  {
    to: '/',
    icon: '📊',
    key: 'dashboard',
    end: true,
    section: 'monitoring',
    roles: ['ADMIN', 'FIELD_OFFICER', 'CITIZEN'],
  },

  {
    to: '/map',
    icon: '🗺️',
    key: 'riskMap',
    section: 'monitoring',
    roles: ['ADMIN', 'FIELD_OFFICER', 'CITIZEN'],
  },

  {
    to: '/monitoring',
    icon: '🛰️',
    key: 'monitoring',
    section: 'monitoring',
    roles: ['ADMIN', 'FIELD_OFFICER'],
  },

  {
    to: '/alerts',
    icon: '🔔',
    key: 'alerts',
    section: 'monitoring',
    roles: ['ADMIN', 'FIELD_OFFICER', 'CITIZEN'],
  },

  {
    to: '/reports',
    icon: '📝',
    key: 'reports',
    section: 'operations',
    roles: ['ADMIN', 'FIELD_OFFICER', 'CITIZEN'],
  },

  {
    to: '/roads',
    icon: '🛣️',
    key: 'roads',
    section: 'operations',
    roles: ['ADMIN', 'FIELD_OFFICER', 'CITIZEN'],
  },

  {
    to: '/emergency',
    icon: '🚑',
    key: 'emergency',
    section: 'operations',
    roles: ['ADMIN', 'FIELD_OFFICER'],
  },

  {
    to: '/analytics',
    icon: '📈',
    key: 'analytics',
    section: 'intelligence',
    roles: ['ADMIN'],
  },

  {
    to: '/simulation',
    icon: '🧪',
    key: 'simulation',
    section: 'intelligence',
    roles: ['ADMIN'],
  },
];


/* =========================================================
   ROLE-SPECIFIC SECTION NAMES
========================================================= */

const SECTION_CONFIG = {
  CITIZEN: [
    { id: 'monitoring', label: 'MONITORING' },
    { id: 'operations', label: 'COMMUNITY SERVICES' },
  ],

  FIELD_OFFICER: [
    { id: 'monitoring', label: 'MONITORING' },
    { id: 'operations', label: 'FIELD OPERATIONS' },
  ],

  ADMIN: [
    { id: 'monitoring', label: 'MONITORING' },
    { id: 'operations', label: 'OPERATIONS' },
    { id: 'intelligence', label: 'INTELLIGENCE' },
  ],

  GUEST: [
    { id: 'monitoring', label: 'MONITORING' },
    { id: 'operations', label: 'COMMUNITY SERVICES' },
  ],
};


/* =========================================================
   ROLE INFORMATION
========================================================= */

const ROLE_INFO = {
  ADMIN: {
    icon: '🛡️',
    title: 'ADMIN OFFICER',
    description: 'Full command access',
  },

  FIELD_OFFICER: {
    icon: '👷',
    title: 'FIELD OFFICER',
    description: 'Field operations access',
  },

  CITIZEN: {
    icon: '🧑',
    title: 'CITIZEN',
    description: 'Community safety access',
  },

  GUEST: {
    icon: '👤',
    title: 'GUEST',
    description: 'Basic public access',
  },
};


/* =========================================================
   NAVIGATION ITEM
========================================================= */

function NavigationItem({ item, t, mobile = false }) {
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        mobile
          ? `flex min-w-[64px] flex-1 flex-col items-center gap-0.5 px-2 py-2 text-[10px] font-bold ${
              isActive
                ? 'text-govblue-800'
                : 'text-slate-500'
            }`
          : `relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-all duration-150 ${
              isActive
                ? 'bg-govblue-50 text-govblue-900 shadow-inner'
                : 'text-slate-600 hover:bg-slate-50 hover:text-govblue-900'
            }`
      }
    >
      {({ isActive }) => (
        <>
          {!mobile && isActive && (
            <span className="absolute left-0 top-1.5 h-[calc(100%-0.75rem)] w-1 rounded-r bg-govblue-700" />
          )}

          <span className={mobile ? 'text-lg' : 'text-base'}>
            {item.icon}
          </span>

          <span>{t(`nav.${item.key}`)}</span>
        </>
      )}
    </NavLink>
  );
}


/* =========================================================
   MAIN LAYOUT
========================================================= */

export default function Layout() {

  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [online, setOnline] = useState(isOnline());
  const [pending, setPending] = useState(0);


  /* =======================================================
     ONLINE / OFFLINE STATE
  ======================================================= */

  useEffect(() => {

    const update = () => {

      setOnline(isOnline());

      if (isOnline()) {

        syncPendingReports((n) => {
          setPending(n);
        })
          .then(() => {
            setPending(0);
          })
          .catch(() => {
            // Keep UI stable if background sync fails.
          });

      }

    };


    const unsub = subscribeOnline(update);

    window.addEventListener('offline', update);


    return () => {

      unsub();

      window.removeEventListener(
        'offline',
        update
      );

    };

  }, []);


  /* =======================================================
     USER INITIALS
  ======================================================= */

  const initials = useMemo(() => {

    if (!user) {
      return 'NA';
    }

    return user.name
      .split(' ')
      .map((part) => part[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();

  }, [user]);


  /* =======================================================
     USER ROLE
  ======================================================= */

  const userRole = user?.role || 'GUEST';

  const roleInfo =
    ROLE_INFO[userRole] || ROLE_INFO.GUEST;


  /* =======================================================
     ROLE-BASED NAVIGATION
  ======================================================= */

  const visibleNav = useMemo(() => {

    if (userRole === 'GUEST') {

      return NAV.filter((item) =>
        item.roles.includes('CITIZEN')
      );

    }

    return NAV.filter((item) =>
      item.roles.includes(userRole)
    );

  }, [userRole]);


  /* =======================================================
     NAVIGATION SECTIONS
  ======================================================= */

  const navigationSections = useMemo(() => {

    const config =
      SECTION_CONFIG[userRole] ||
      SECTION_CONFIG.GUEST;


    return config
      .map((section) => {

        const items = visibleNav.filter(
          (item) =>
            item.section === section.id
        );

        return {
          ...section,
          items,
        };

      })
      .filter(
        (section) =>
          section.items.length > 0
      );

  }, [userRole, visibleNav]);


  /* =======================================================
     LOGOUT
  ======================================================= */

  function handleLogout() {

    logout();

    navigate('/login');

  }


  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="flex min-h-screen flex-col bg-slate-100">


      {/* ===================================================
          UTILITY BAR
      =================================================== */}

      <UtilityBar />


      {/* ===================================================
          TOP HEADER
      =================================================== */}

      <header className="gov-texture sticky top-0 z-40 bg-[#0b1f3a] text-white shadow-lg">

        <div className="flex h-16 items-center justify-between gap-4 px-5">


          {/* BRAND */}

          <div className="flex min-w-0 items-center gap-3">

            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-red-500 to-orange-500 text-xl shadow-pop">
              ⛰️
            </div>


            <div className="min-w-0">

              <div className="flex items-center gap-2">

                <h1 className="truncate text-base font-extrabold tracking-tight">
                  {t('app.name')}
                </h1>

                <span className="hidden rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-300 ring-1 ring-inset ring-white/10 sm:inline">
                  Live Monitoring
                </span>

              </div>


              <p className="truncate text-[11px] text-slate-200">

                {t('app.tagline')} · {t('app.region')}

              </p>

            </div>

          </div>


          {/* USER AREA */}

          <div className="flex shrink-0 items-center gap-2 sm:gap-3">


            {/* ONLINE STATUS */}

            <span
              className={`hidden items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold sm:flex ${
                online
                  ? 'bg-emerald-500/15 text-emerald-300'
                  : 'bg-red-500/20 text-red-300'
              }`}
            >

              <span
                className={`h-2 w-2 rounded-full ${
                  online
                    ? 'bg-emerald-400'
                    : 'bg-red-400'
                } ${
                  online
                    ? ''
                    : 'animate-pulse'
                }`}
              />

              {online ? 'LIVE' : 'OFFLINE'}

            </span>


            {/* OFFLINE MODE */}

            {!online && (

              <span className="hidden animate-pulse rounded-full bg-red-600 px-2.5 py-1 text-[11px] font-bold text-white md:inline">

                {pending
                  ? `${pending} pending`
                  : 'OFFLINE MODE'
                }

              </span>

            )}


            <LangSwitch />


            {/* USER */}

            {user ? (

              <div className="flex items-center gap-2">


                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-orange-500 text-xs font-extrabold text-govblue-950">

                  {initials}

                </div>


                <div className="hidden text-right md:block">

                  <p className="text-xs font-bold leading-tight">

                    {user.name}

                  </p>

                  <p className="text-[10px] uppercase tracking-wider text-slate-300">

                    {roleInfo.title}

                  </p>

                </div>


                <button
                  onClick={handleLogout}
                  title={t('nav.logout')}
                  className="ml-1 rounded-lg p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
                >

                  <svg
                    className="h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >

                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013 3h4a3 3 0 013 3v1"
                    />

                  </svg>

                </button>

              </div>

            ) : (

              <button
                className="btn bg-white/10 text-white hover:bg-white/20"
                onClick={() => navigate('/login')}
              >

                {t('auth.login')}

              </button>

            )}

          </div>

        </div>

      </header>


      {/* ===================================================
          OFFLINE WARNING
      =================================================== */}

      {!online && (

        <div className="bg-amber-400 px-5 py-2 text-center text-xs font-bold text-amber-950">

          {t('common.offline')}

        </div>

      )}


      <div className="flex flex-1">


        {/* =================================================
            DESKTOP SIDEBAR
        ================================================= */}

        <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-60 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">


          <nav className="flex-1 overflow-y-auto p-3">


            {navigationSections.map(
              (section, index) => (

                <div
                  key={section.id}
                  className={
                    index > 0
                      ? 'mt-5'
                      : ''
                  }
                >


                  {/* SECTION TITLE */}

                  <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">

                    {section.label}

                  </p>


                  {/* SECTION ITEMS */}

                  <div className="space-y-1">

                    {section.items.map(
                      (item) => (

                        <NavigationItem
                          key={item.to}
                          item={item}
                          t={t}
                        />

                      )
                    )}

                  </div>


                </div>

              )
            )}


          </nav>


          {/* =================================================
              ROLE ACCESS CARD
          ================================================= */}

          <div className="border-t border-slate-200 p-4">


            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">

              Current Access

            </p>


            <div className="mt-2 rounded-xl border border-govblue-100 bg-gradient-to-br from-govblue-50 to-white p-3">


              <div className="flex items-center gap-2">


                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-lg shadow-sm">

                  {roleInfo.icon}

                </div>


                <div className="min-w-0">


                  <p className="truncate text-xs font-extrabold text-govblue-900">

                    {roleInfo.title}

                  </p>


                  <p className="mt-0.5 text-[10px] leading-snug text-slate-500">

                    {roleInfo.description}

                  </p>


                </div>

              </div>


              {user && (

                <div className="mt-3 border-t border-govblue-100 pt-2">

                  <p className="truncate text-[10px] font-semibold text-slate-600">

                    {user.name}

                  </p>

                </div>

              )}


            </div>


          </div>


        </aside>


        {/* =================================================
            MOBILE NAVIGATION
        ================================================= */}

        <div className="fixed bottom-0 left-0 right-0 z-40 flex overflow-x-auto border-t border-slate-200 bg-white/95 backdrop-blur md:hidden">


          {visibleNav.map((item) => (

            <NavigationItem
              key={item.to}
              item={item}
              t={t}
              mobile
            />

          ))}


        </div>


        {/* =================================================
            MAIN CONTENT
        ================================================= */}

        <main
          id="main-content"
          className="min-w-0 flex-1 px-5 pb-24 pt-6 md:px-8 md:pb-10"
        >

          <Outlet />

        </main>


      </div>


      <Footer />


    </div>

  );

}