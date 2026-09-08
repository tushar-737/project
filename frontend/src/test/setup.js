/* Vitest jsdom setup: browser-API polyfills needed by React/Recharts. */
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
if (!globalThis.ResizeObserver) globalThis.ResizeObserver = ResizeObserverStub;

if (!window.matchMedia) {
  window.matchMedia = () => ({
    matches: false,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
  });
}

// The app talks to /api relative paths - point them at the live backend so
// smoke tests exercise the real data flow.
const realFetch = globalThis.fetch.bind(globalThis);
globalThis.fetch = (input, init) =>
  realFetch(typeof input === 'string' && input.startsWith('/') ? 'http://localhost:8000' + input : input, init);

// jsdom has no layout: recharts measures 0-sized containers; force a size.
Object.defineProperty(HTMLElement.prototype, 'clientWidth', { configurable: true, value: 640 });
Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, value: 360 });
Object.defineProperty(HTMLElement.prototype, 'offsetWidth', { configurable: true, value: 640 });
Object.defineProperty(HTMLElement.prototype, 'offsetHeight', { configurable: true, value: 360 });
Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', {
  configurable: true,
  value: () => ({ width: 640, height: 360, top: 0, left: 0, right: 640, bottom: 360, x: 0, y: 0 }),
});

// Keep tests deterministic-ish: silence recharts ResizeObserver noise.
window.console.error = vi.fn((...args) => {
  const msg = args.join(' ');
  if (msg.includes('not wrapped in act') || msg.includes('ResizeObserver')) return;
  process.stderr.write('console.error: ' + msg + '\n');
});

afterEach(() => {
  cleanup();
  localStorage.clear();
});
