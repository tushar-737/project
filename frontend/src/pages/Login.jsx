import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n';
import { ApiError } from '../services/api';

import UtilityBar from '../components/UtilityBar';
import Footer from '../components/Footer';

const DEMO_ACCOUNTS = [
  {
    label: 'Admin Officer',
    email: 'admin@ner.gov.in',
    role: 'ADMIN',
    icon: '🛡️',
  },
  {
    label: 'Field Officer',
    email: 'officer@ner.gov.in',
    role: 'FIELD_OFFICER',
    icon: '👷',
  },
  {
    label: 'Citizen User',
    email: 'citizen@ner.gov.in',
    role: 'CITIZEN',
    icon: '🧑',
  },
];

const DEMO_PASS = {
  'admin@ner.gov.in': 'admin123',
  'officer@ner.gov.in': 'officer123',
  'citizen@ner.gov.in': 'citizen123',
};

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [mode, setMode] = useState('login');

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'FIELD_OFFICER',
  });

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(e) {
    e.preventDefault();

    setBusy(true);
    setError('');

    try {
      if (mode === 'login') {
        await login(
          form.email.trim(),
          form.password
        );
      } else {
        const resp = await fetch(
          '/api/auth/register',
          {
            method: 'POST',

            headers: {
              'Content-Type':
                'application/json',
            },

            body: JSON.stringify({
              ...form,
              email:
                form.email.trim(),
            }),
          }
        );

        const body =
          await resp.json();

        if (!resp.ok) {
          throw new ApiError(
            body.detail ||
              'Registration failed',
            resp.status
          );
        }

        await login(
          form.email.trim(),
          form.password
        );
      }

      navigate('/', {
        replace: true,
      });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Unexpected error'
      );
    } finally {
      setBusy(false);
    }
  }

  async function quickLogin(email) {
    setBusy(true);
    setError('');

    try {
      await login(
        email,
        DEMO_PASS[email]
      );

      navigate('/', {
        replace: true,
      });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Unexpected error'
      );
    } finally {
      setBusy(false);
    }
  }

  function updateForm(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  return (
    <div className="flex min-h-screen flex-col bg-govblue-950">

      <UtilityBar />

      <main
        id="main-content"
        className="
          gov-texture
          relative
          flex
          flex-1
          items-center
          justify-center
          overflow-hidden
          px-4
          py-8
          sm:px-6
        "
      >

        {/* Background glow */}
        <div
          className="
            pointer-events-none
            absolute
            left-1/4
            top-1/4
            h-72
            w-72
            rounded-full
            bg-blue-500/10
            blur-3xl
          "
        />

        <div
          className="
            relative
            grid
            w-full
            max-w-5xl
            overflow-hidden
            rounded-2xl
            border
            border-white/10
            bg-white
            shadow-2xl
            lg:grid-cols-2
          "
        >

          {/* ================================================= */}
          {/* LEFT BRAND PANEL */}
          {/* ================================================= */}

          <section
            className="
              gov-texture
              relative
              hidden
              flex-col
              justify-between
              overflow-hidden
              bg-gradient-to-br
              from-govblue-800
              via-govblue-900
              to-govblue-950
              p-10
              text-white
              lg:flex
            "
          >

            {/* Decorative circles */}

            <div
              className="
                pointer-events-none
                absolute
                -right-20
                -top-20
                h-64
                w-64
                rounded-full
                border
                border-white/5
              "
            />

            <div
              className="
                pointer-events-none
                absolute
                -bottom-24
                -left-24
                h-72
                w-72
                rounded-full
                border
                border-white/5
              "
            />

            <div className="relative z-10">

              {/* Logo */}

              <div className="flex items-center gap-3">

                <div
                  className="
                    flex
                    h-14
                    w-14
                    shrink-0
                    items-center
                    justify-center
                    rounded-2xl
                    bg-gradient-to-br
                    from-red-500
                    to-orange-500
                    text-2xl
                    shadow-lg
                    ring-1
                    ring-white/20
                  "
                >
                  ⛰️
                </div>

                <div>

                  <p
                    className="
                      text-xl
                      font-extrabold
                      tracking-tight
                      text-white
                    "
                  >
                    {t('app.name')}
                  </p>

                  <p
                    className="
                      mt-0.5
                      text-xs
                      font-medium
                      text-slate-300
                    "
                  >
                    Landslide Early Warning System
                  </p>

                </div>

              </div>


              {/* Badge */}

              <div
                className="
                  mt-10
                  inline-flex
                  items-center
                  gap-2
                  rounded-full
                  border
                  border-emerald-400/20
                  bg-emerald-400/10
                  px-3
                  py-1.5
                  text-xs
                  font-bold
                  text-emerald-300
                "
              >

                <span
                  className="
                    h-2
                    w-2
                    rounded-full
                    bg-emerald-400
                    animate-pulse
                  "
                />

                LIVE DISASTER MONITORING

              </div>


              {/* Heading */}

              <h1
                className="
                  mt-6
                  text-3xl
                  font-extrabold
                  leading-tight
                  text-white
                "
              >
                AI-powered landslide
                <br />
                risk intelligence
                <br />
                for the North East.
              </h1>


              <p
                className="
                  mt-4
                  max-w-md
                  text-sm
                  leading-relaxed
                  text-slate-300
                "
              >
                A unified monitoring and early-warning
                platform designed to support disaster
                management authorities, field officers
                and communities.
              </p>


              {/* Features */}

              <div className="mt-8 space-y-3">

                <Feature
                  icon="📡"
                  title="Simulated sensor network"
                  text="IoT-ready environmental monitoring"
                />

                <Feature
                  icon="🧠"
                  title="AI risk engine"
                  text="Multi-factor landslide risk analysis"
                />

                <Feature
                  icon="🗺️"
                  title="Live GIS monitoring"
                  text="Risk zones, roads and vulnerable areas"
                />

                <Feature
                  icon="🚨"
                  title="Automated alerts"
                  text="Early warning and SMS notification pipeline"
                />

                <Feature
                  icon="🚑"
                  title="Emergency prioritisation"
                  text="Supports faster disaster response decisions"
                />

              </div>

            </div>


            {/* Bottom information */}

            <div
              className="
                relative
                z-10
                mt-10
                border-t
                border-white/10
                pt-5
              "
            >

              <p
                className="
                  text-[11px]
                  leading-relaxed
                  text-slate-400
                "
              >
                Academic / disaster-management demonstration
                prototype. Risk predictions are decision-support
                indicators and do not predict the exact time of a
                landslide event.
              </p>

            </div>

          </section>


          {/* ================================================= */}
          {/* RIGHT LOGIN PANEL */}
          {/* ================================================= */}

          <section
            className="
              bg-white
              p-7
              sm:p-10
              lg:p-12
            "
          >

            {/* Mobile branding */}

            <div
              className="
                mb-8
                text-center
                lg:hidden
              "
            >

              <div
                className="
                  mb-3
                  inline-flex
                  h-14
                  w-14
                  items-center
                  justify-center
                  rounded-2xl
                  bg-gradient-to-br
                  from-red-500
                  to-orange-500
                  text-2xl
                  shadow-lg
                "
              >
                ⛰️
              </div>

              <p
                className="
                  text-xl
                  font-extrabold
                  text-govblue-950
                "
              >
                {t('app.name')}
              </p>

              <p
                className="
                  mt-1
                  text-xs
                  text-slate-500
                "
              >
                Landslide Early Warning System
              </p>

            </div>


            {/* Form heading */}

            <div>

              <div
                className="
                  inline-flex
                  items-center
                  rounded-full
                  bg-govblue-50
                  px-3
                  py-1
                  text-[10px]
                  font-extrabold
                  uppercase
                  tracking-wider
                  text-govblue-700
                "
              >
                Secure Access
              </div>


              <h2
                className="
                  mt-4
                  text-2xl
                  font-extrabold
                  tracking-tight
                  text-govblue-950
                "
              >
                {mode === 'login'
                  ? 'Welcome back'
                  : 'Create your account'}
              </h2>


              <p
                className="
                  mt-2
                  text-sm
                  leading-relaxed
                  text-slate-600
                "
              >
                {mode === 'login'
                  ? 'Sign in to access the NER LandslideAI monitoring platform.'
                  : 'Register to access the disaster monitoring platform.'}
              </p>

            </div>


            {/* Error */}

            {error && (

              <div
                className="
                  mt-5
                  rounded-xl
                  border
                  border-red-200
                  bg-red-50
                  px-4
                  py-3
                  text-sm
                  font-semibold
                  text-red-700
                "
              >
                {error}
              </div>

            )}


            {/* Login Form */}

            <form
              onSubmit={submit}
              className="mt-7 space-y-4"
            >

              {mode === 'register' && (

                <>

                  <div>

                    <label
                      className="
                        mb-1.5
                        block
                        text-xs
                        font-bold
                        text-slate-700
                      "
                    >
                      Full Name
                    </label>

                    <input
                      className="input"
                      placeholder={t('auth.name')}
                      required
                      value={form.name}
                      onChange={(e) =>
                        updateForm(
                          'name',
                          e.target.value
                        )
                      }
                    />

                  </div>


                  <div>

                    <label
                      className="
                        mb-1.5
                        block
                        text-xs
                        font-bold
                        text-slate-700
                      "
                    >
                      Account Role
                    </label>

                    <select
                      className="input"
                      value={form.role}
                      onChange={(e) =>
                        updateForm(
                          'role',
                          e.target.value
                        )
                      }
                    >

                      <option value="FIELD_OFFICER">
                        {t('common.fieldOfficer')}
                      </option>

                      <option value="CITIZEN">
                        {t('common.citizen')}
                      </option>

                      <option value="ADMIN">
                        {t('common.admin')}
                      </option>

                    </select>

                  </div>

                </>

              )}


              <div>

                <label
                  className="
                    mb-1.5
                    block
                    text-xs
                    font-bold
                    text-slate-700
                  "
                >
                  Email Address
                </label>

                <input
                  className="input"
                  type="email"
                  placeholder={t('auth.email')}
                  required
                  value={form.email}
                  onChange={(e) =>
                    updateForm(
                      'email',
                      e.target.value
                    )
                  }
                />

              </div>


              <div>

                <label
                  className="
                    mb-1.5
                    block
                    text-xs
                    font-bold
                    text-slate-700
                  "
                >
                  Password
                </label>

                <input
                  className="input"
                  type="password"
                  placeholder={t('auth.password')}
                  required
                  minLength={6}
                  value={form.password}
                  onChange={(e) =>
                    updateForm(
                      'password',
                      e.target.value
                    )
                  }
                />

              </div>


              <button
                className="
                  btn-primary
                  mt-2
                  w-full
                  py-2.5
                "
                disabled={busy}
              >
                {busy
                  ? 'Signing in...'
                  : mode === 'login'
                    ? 'Sign in'
                    : 'Create account'}
              </button>

            </form>


            {/* Divider */}

            {mode === 'login' && (

              <div
                className="
                  my-7
                  flex
                  items-center
                  gap-3
                "
              >

                <span className="h-px flex-1 bg-slate-200" />

                <span
                  className="
                    whitespace-nowrap
                    text-[10px]
                    font-extrabold
                    uppercase
                    tracking-wider
                    text-slate-400
                  "
                >
                  Quick Demo Sign-in
                </span>

                <span className="h-px flex-1 bg-slate-200" />

              </div>

            )}


            {/* Demo Accounts */}

            {mode === 'login' && (

              <div className="space-y-2.5">

                {DEMO_ACCOUNTS.map(
                  (acc) => (

                    <button
                      key={acc.email}
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        quickLogin(acc.email)
                      }
                      className="
                        group
                        flex
                        w-full
                        items-center
                        gap-3
                        rounded-xl
                        border
                        border-slate-200
                        bg-slate-50
                        px-4
                        py-3
                        text-left
                        transition-all
                        duration-200
                        hover:-translate-y-0.5
                        hover:border-govblue-400
                        hover:bg-govblue-50
                        hover:shadow-sm
                        disabled:cursor-not-allowed
                        disabled:opacity-50
                      "
                    >

                      <div
                        className="
                          flex
                          h-9
                          w-9
                          shrink-0
                          items-center
                          justify-center
                          rounded-lg
                          bg-white
                          text-lg
                          shadow-sm
                          ring-1
                          ring-slate-200
                        "
                      >
                        {acc.icon}
                      </div>


                      <div className="min-w-0 flex-1">

                        <p
                          className="
                            text-sm
                            font-bold
                            text-slate-800
                            group-hover:text-govblue-900
                          "
                        >
                          {acc.label}
                        </p>

                        <p
                          className="
                            truncate
                            text-xs
                            text-slate-500
                          "
                        >
                          {acc.email}
                        </p>

                      </div>


                      <span
                        className="
                          rounded-full
                          bg-govblue-100
                          px-2
                          py-1
                          text-[9px]
                          font-extrabold
                          uppercase
                          tracking-wider
                          text-govblue-700
                        "
                      >
                        Demo
                      </span>

                    </button>

                  )
                )}

              </div>

            )}


            {/* Toggle Login / Register */}

            <div
              className="
                mt-7
                border-t
                border-slate-100
                pt-5
                text-center
              "
            >

              <p className="text-sm text-slate-600">

                {mode === 'login'
                  ? t('auth.noAccount')
                  : t('auth.hasAccount')}

                {' '}

                <button
                  type="button"
                  className="
                    font-bold
                    text-govblue-800
                    transition
                    hover:text-govblue-600
                    hover:underline
                  "
                  onClick={() => {

                    setMode(
                      mode === 'login'
                        ? 'register'
                        : 'login'
                    );

                    setError('');

                  }}
                >

                  {mode === 'login'
                    ? t('auth.register')
                    : t('auth.login')}

                </button>

              </p>

            </div>

          </section>

        </div>

      </main>

      <Footer />

    </div>
  );
}


/* ========================================================= */
/* FEATURE COMPONENT */
/* ========================================================= */

function Feature({
  icon,
  title,
  text,
}) {
  return (

    <div
      className="
        flex
        items-center
        gap-3
        rounded-xl
        border
        border-white/5
        bg-white/[0.04]
        px-3
        py-2.5
      "
    >

      <div
        className="
          flex
          h-9
          w-9
          shrink-0
          items-center
          justify-center
          rounded-lg
          bg-white/10
          text-base
        "
      >
        {icon}
      </div>

      <div>

        <p
          className="
            text-sm
            font-bold
            text-white
          "
        >
          {title}
        </p>

        <p
          className="
            mt-0.5
            text-[11px]
            text-slate-300
          "
        >
          {text}
        </p>

      </div>

    </div>

  );
}