import { useTranslation } from '../i18n';

export default function Footer() {
  const { t } = useTranslation();
  const year = new Date().getFullYear();

  const links = [
    t('footer.about'),
    t('footer.sitemap'),
    t('footer.accessibility'),
    t('footer.terms'),
    t('footer.privacy'),
    t('footer.contact'),
  ];

  return (
    <footer className="mt-auto border-t border-slate-200 bg-govblue-950 text-slate-300">
      <div className="mx-auto max-w-7xl px-5 py-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{t('app.name')}</p>
          <nav aria-label={t('footer.linksLabel')} className="flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
            {links.map((label) => (
              <a key={label} href="#" className="hover:text-white hover:underline">
                {label}
              </a>
            ))}
          </nav>
        </div>
        <div className="mt-4 grid gap-3 text-[11px] leading-relaxed text-slate-400 md:grid-cols-3">
          <p>{t('footer.owned')}</p>
          <p>{t('footer.hosted')}</p>
          <p>
            {t('footer.lastUpdated')}: {new Date().toLocaleDateString()}
            <span className="mx-1.5">·</span>
            {t('footer.visitors')}: {Math.floor(10000 + (year % 97) * 137)}
          </p>
        </div>
        <p className="mt-4 rounded-md bg-white/5 px-3 py-2 text-[10.5px] leading-relaxed text-slate-400">
          {t('footer.disclaimer')}
        </p>
        <p className="mt-3 text-center text-[10.5px] text-slate-500">
          © {year} {t('footer.copyright')}
        </p>
      </div>
    </footer>
  );
}
