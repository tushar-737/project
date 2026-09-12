import { useTranslation } from '../i18n';
import { useAccessibility } from '../context/AccessibilityContext';
import { LangSwitch } from './ui';

/** Generic emblem placeholder — swap the <svg> below for the official
 * National Emblem asset (public domain) before a real government deployment. */
function Emblem() {
  return (
    <svg viewBox="0 0 48 48" className="h-8 w-8 shrink-0" aria-hidden="true">
      <circle cx="24" cy="24" r="22" fill="#0f2557" stroke="#f59e0b" strokeWidth="1.5" />
      <path d="M24 10c-6 4-10 9-10 15 0 6 4.5 11 10 13 5.5-2 10-7 10-13 0-6-4-11-10-15z" fill="#fff" opacity="0.95" />
      <circle cx="24" cy="24" r="4.5" fill="#0f2557" />
      <path d="M24 19.5v9M20 22l8 4M28 22l-8 4" stroke="#0f2557" strokeWidth="1.2" />
    </svg>
  );
}

export default function GovMasthead() {
  const { t, lang } = useTranslation();
  const { fontStep, canIncrease, canDecrease, increaseFont, decreaseFont, highContrast, toggleHighContrast } =
    useAccessibility();

  return (
    <div className="relative z-50">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-[100] focus:rounded focus:bg-amber-400 focus:px-3 focus:py-1.5 focus:text-xs focus:font-bold focus:text-govblue-950"
      >
        {t('masthead.skip')}
      </a>

      {/* tricolour strip */}
      <div className="flex h-1.5 w-full">
        <div className="flex-1 bg-[#FF9933]" />
        <div className="flex-1 bg-white" />
        <div className="flex-1 bg-[#138808]" />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 bg-slate-50 px-4 py-1.5 text-[11px] text-slate-600">
        <div className="flex items-center gap-2 font-semibold">
          <Emblem />
          <span>
            {lang === 'hi' ? 'भारत सरकार' : 'Government of India'}
            <span className="mx-1.5 text-slate-300">|</span>
            {t('masthead.ministry')}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1 rounded border border-slate-200 bg-white px-1.5 py-0.5">
            <span className="hidden pr-1 font-bold uppercase tracking-wide text-slate-400 sm:inline">
              {t('masthead.textSize')}
            </span>
            <button
              type="button"
              onClick={decreaseFont}
              disabled={!canDecrease}
              aria-label={t('masthead.decreaseText')}
              className="rounded px-1.5 py-0.5 text-[10px] font-bold text-slate-600 hover:bg-slate-100 disabled:opacity-30"
            >
              A-
            </button>
            <button
              type="button"
              onClick={() => {}}
              aria-hidden="true"
              className="cursor-default px-1 text-[12px] font-bold text-govblue-800"
            >
              A
            </button>
            <button
              type="button"
              onClick={increaseFont}
              disabled={!canIncrease}
              aria-label={t('masthead.increaseText')}
              className="rounded px-1.5 py-0.5 text-[13px] font-bold text-slate-600 hover:bg-slate-100 disabled:opacity-30"
            >
              A+
            </button>
          </div>

          <button
            type="button"
            onClick={toggleHighContrast}
            aria-pressed={highContrast}
            className={`rounded border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide transition ${
              highContrast
                ? 'border-amber-500 bg-amber-400 text-amber-950'
                : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-100'
            }`}
          >
            {highContrast ? t('masthead.contrastOn') : t('masthead.contrast')}
          </button>

          <LangSwitch />
        </div>
      </div>
    </div>
  );
}
