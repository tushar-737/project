import { useEffect, useMemo, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { isOnline, syncPendingReports, subscribeOnline } from '../services/offline';
import { useTranslation } from '../i18n';
import { useAuth } from '../context/AuthContext';
import { LangSwitch } from './ui';

const NAV = [
  { to: '/', icon: '📊', key: 'dashboard', end: true },
  { to: '/map', icon: '🗺️', key: 'riskMap' },
  { to: '/monitoring', icon: '🛰️', key: 'monitoring' },
  { to: '/alerts', icon: '🔔', key: 'alerts' },
  { to: '/reports', icon: '📝', key: 'reports' },
  { to: '/roads', icon: '🛣️', key: 'roads' },
  { to: '/emergency', icon: '🚑', key: 'emergency' },
  { to: '/analytics', icon: '📈', key: 'analytics' },
  { to: '/simulation', icon: '🧪', key: 'simulation' },
];

export default function Layout() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [online, setOnline] = useState(isOnline());
  const [pending, setPending] = useState(0);

  useEffect(() => {
    const update = () => {
      setOnline(isOnline());
      if (isOnline()) syncPendingReports((n) => setPending(n)).then(() => setPending(0));
    };
    const unsub = subscribeOnline(update);
    window.addEventListener('offline', update);
    return () => {
      unsub();
      window.removeEventListener('offline', update);
    };
  }, []);

  const initials = useMemo(() => {
    if (!user) return 'NA';
    return user.name
      .split(' ')
      .map((p) => p[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  }, [user]);

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Top brand bar */}
      <header className="gov-texture sticky top-0 z-40 bg-govblue-950 text-white shadow-lg">
        <div className="flex h-16 items-center justify-between gap-4 px-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-red-500 to-orange-500 text-xl shadow">⛰️</div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-extrabold tracking-tight">{t('app.name')}</h1>
                <span className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-300">India · NER</span>
              </div>
              <p className="text-[11px] text-slate-300">{t('app.tagline')} · {t('app.region')}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span
              className={`hidden items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold sm:flex ${
                online ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/20 text-red-300'
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${online ? 'bg-emerald-400' : 'bg-red-400'} ${online ? '' : 'animate-pulse'}`} />
              {online ? 'LIVE' : 'OFFLINE'}
            </span>
            {!online && (
              <span className="rounded-full bg-red-600 px-2.5 py-1 text-[11px] font-bold text-white animate-pulse">
                {pending ? `${pending} pending` : 'OFFLINE MODE'}
              </span>
            )}
            <LangSwitch />
            {user ? (
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-orange-500 text-xs font-extrabold text-govblue-950">
                  {initials}
                </div>
                <div className="hidden text-right md:block">
                  <p className="text-xs font-bold leading-tight">{user.name}</p>
                  <p className="text-[10px] uppercase tracking-wider text-slate-300">{user.role.replace(/_/g, ' ')}</p>
                </div>
                <button
                  onClick={() => {
                    logout();
                    navigate('/login');
                  }}
                  title={t('nav.logout')}
                  className="ml-1 rounded-lg p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </button>
              </div>
            ) : (
              <button className="btn bg-white/10 text-white hover:bg-white/20" onClick={() => navigate('/login')}>
                {t('auth.login')}
              </button>
            )}
          </div>
        </div>
      </header>

      {!online && (
        <div className="bg-amber-400 px-5 py-2 text-center text-xs font-bold text-amber-950">
          {t('common.offline')}
        </div>
      )}

      <div className="flex">
        {/* Sidebar */}
        <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-60 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
          <nav className="flex-1 space-y-0.5 overflow-y-auto p-3">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition ${
                    isActive ? 'bg-govblue-800 text-white shadow' : 'text-slate-600 hover:bg-slate-100 hover:text-govblue-900'
                  }`
                }
              >
                <span className="text-base">{item.icon}</span>
                {t(`nav.${item.key}`)}
              </NavLink>
            ))}
          </nav>
          <div className="border-t border-slate-200 p-4">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Demo access</p>
            <p className="mt-1 text-[11px] text-slate-500">
              admin@ner.gov.in · officer@ner.gov.in · citizen@ner.gov.in
            </p>
          </div>
        </aside>

        {/* Mobile nav */}
        <div className="fixed bottom-0 left-0 right-0 z-40 flex overflow-x-auto border-t border-slate-200 bg-white/95 backdrop-blur md:hidden">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex min-w-[64px] flex-1 flex-col items-center gap-0.5 px-2 py-2 text-[10px] font-bold ${
                  isActive ? 'text-govblue-800' : 'text-slate-500'
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              {t(`nav.${item.key}`)}
            </NavLink>
          ))}
        </div>

        <main className="min-w-0 flex-1 px-5 pb-24 pt-6 md:px-8 md:pb-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
