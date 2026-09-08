import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Browser-only libs: no-op stubs for the jsdom smoke tests.
      leaflet: fileURLToPath(new URL('./src/test/leafletStub.js', import.meta.url)),
      'react-leaflet': fileURLToPath(new URL('./src/test/reactLeafletStub.jsx', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    include: ['src/**/*.test.jsx'],
    testTimeout: 25000,
    hookTimeout: 25000,
  },
});
