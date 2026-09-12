import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const AccessibilityContext = createContext(null);

const SIZES = ['sm', 'base', 'lg', 'xl'];
const SIZE_PX = { sm: '15px', base: '16px', lg: '18px', xl: '20px' };

export function AccessibilityProvider({ children }) {
  const [fontStep, setFontStep] = useState(() => {
    try {
      const saved = localStorage.getItem('ner_font_step');
      return saved ? Number(saved) : 1; // index into SIZES, default 'base'
    } catch {
      return 1;
    }
  });
  const [highContrast, setHighContrast] = useState(() => {
    try {
      return localStorage.getItem('ner_high_contrast') === '1';
    } catch {
      return false;
    }
  });

  useEffect(() => {
    document.documentElement.style.fontSize = SIZE_PX[SIZES[fontStep]] || SIZE_PX.base;
    try {
      localStorage.setItem('ner_font_step', String(fontStep));
    } catch {
      /* ignore */
    }
  }, [fontStep]);

  useEffect(() => {
    document.documentElement.classList.toggle('high-contrast', highContrast);
    try {
      localStorage.setItem('ner_high_contrast', highContrast ? '1' : '0');
    } catch {
      /* ignore */
    }
  }, [highContrast]);

  const value = useMemo(
    () => ({
      fontStep,
      canIncrease: fontStep < SIZES.length - 1,
      canDecrease: fontStep > 0,
      increaseFont: () => setFontStep((s) => Math.min(s + 1, SIZES.length - 1)),
      decreaseFont: () => setFontStep((s) => Math.max(s - 1, 0)),
      resetFont: () => setFontStep(1),
      highContrast,
      toggleHighContrast: () => setHighContrast((v) => !v),
    }),
    [fontStep, highContrast],
  );

  return <AccessibilityContext.Provider value={value}>{children}</AccessibilityContext.Provider>;
}

export function useAccessibility() {
  const ctx = useContext(AccessibilityContext);
  if (!ctx) throw new Error('useAccessibility must be used inside AccessibilityProvider');
  return ctx;
}
