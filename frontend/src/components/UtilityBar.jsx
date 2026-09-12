import { useTranslation } from '../i18n';
import { useAccessibility } from '../context/AccessibilityContext';
import { LangSwitch } from './ui';

/** Slim accessibility/utility strip — text size, contrast, language, skip link.
 * Purely a UX affordance, no institutional branding or claims. */
export default function UtilityBar() {
  const { t } = useTranslation();
  const { canIncrease, canDecrease, increaseFont, decreaseFont, highContrast, toggleHighContrast } =
    useAccessibility();

  return (
    <div className="relative z-50">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-[100] focus:rounded focus:bg-amber-400 focus:px-3 focus:py-1.5 focus:text-xs focus:font-bold focus:text-govblue-950"
      >
        {t('masthead.skip')}
      </a>

      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 bg-slate-900 px-4 py-1 text-[11px] text-slate-300">
        <span className="font-semibold tracking-wide text-slate-400">{t('masthead.ministry')}</span>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 py-0.5">
            <span className="hidden pr-1 font-bold uppercase tracking-wide text-slate-500 sm:inline">
              {t('masthead.textSize')}
            </span>
            <button
              type="button"
              onClick={decreaseFont}
              disabled={!canDecrease}
              aria-label={t('masthead.decreaseText')}
              className="rounded px-1.5 py-0.5 text-[10px] font-bold text-slate-300 hover:bg-white/10 disabled:opacity-30"
            >
              A-
            </button>
            <button type="button" aria-hidden="true" className="cursor-default px-1 text-[12px] font-bold text-amber-400">
              A
            </button>
            <button
              type="button"
              onClick={increaseFont}
              disabled={!canIncrease}
              aria-label={t('masthead.increaseText')}
              className="rounded px-1.5 py-0.5 text-[13px] font-bold text-slate-300 hover:bg-white/10 disabled:opacity-30"
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
                : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
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
