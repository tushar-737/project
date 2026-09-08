import { describe, expect, test } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LanguageProvider } from '../i18n';
import { AuthProvider } from '../context/AuthContext';
import App from '../App';

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <LanguageProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </LanguageProvider>
    </MemoryRouter>,
  );
}

describe('page smoke tests (against live backend on :8000)', () => {
  test('health: backend reachable', async () => {
    const res = await fetch('/api/health');
    const body = await res.json();
    expect(body.status).toBe('healthy');
  });

  test('/ (Dashboard) renders summary cards', async () => {
    renderAt('/');
    expect(await screen.findByText('NER LandslideAI', {}, { timeout: 15000 })).toBeTruthy();
    await waitFor(() => {
      expect(screen.getAllByText(/high risk zones/i).length).toBeGreaterThan(0);
      expect(document.body.textContent).toContain('Recent Alerts');
    }, { timeout: 15000 });
  }, 30000);

  test('/monitoring renders the risk table', async () => {
    renderAt('/monitoring');
    await waitFor(() => {
      expect(screen.getAllByRole('heading', { level: 1 }).some((h) => h.textContent.includes('Risk Monitoring'))).toBe(true);
      const rows = document.querySelectorAll('tbody tr');
      expect(rows.length).toBeGreaterThan(20);
    }, { timeout: 15000 });
  }, 30000);

  test('/alerts renders bulletins', async () => {
    renderAt('/alerts');
    await waitFor(() => {
      expect(document.body.textContent).toContain('CRITICAL');
    }, { timeout: 15000 });
  }, 30000);

  test('/reports renders the form + cards', async () => {
    renderAt('/reports');
    await waitFor(() => {
      expect(document.body.textContent).toContain('Field & Citizen Reports');
    }, { timeout: 15000 });
    expect(document.body.textContent).toContain('New Report');
  }, 30000);

  test('/roads renders corridors', async () => {
    renderAt('/roads');
    await waitFor(() => {
      // one table row per monitored road corridor
      const rows = document.querySelectorAll('tbody tr');
      expect(rows.length).toBeGreaterThanOrEqual(9);
      expect(document.body.textContent).toContain('NH-6 Shillong-Guwahati Rd');
    }, { timeout: 15000 });
  }, 30000);

  test('/emergency renders tiers', async () => {
    renderAt('/emergency');
    await waitFor(() => {
      expect(document.body.textContent).toContain('PRIORITY 1');
      expect(document.body.textContent).toContain('PRIORITY 3');
    }, { timeout: 15000 });
  }, 30000);

  test('/analytics renders charts', async () => {
    renderAt('/analytics');
    await waitFor(() => {
      expect(document.body.textContent).toContain('Rainfall vs Risk Score');
      expect(document.querySelectorAll('svg').length).toBeGreaterThan(0);
    }, { timeout: 15000 });
  }, 30000);

  test('/simulation renders the run controls', async () => {
    renderAt('/simulation');
    await waitFor(() => {
      expect(document.body.textContent).toContain('RUN SIMULATION');
    }, { timeout: 15000 });
  }, 30000);

  test('/map renders with stubs without crashing', async () => {
    renderAt('/map');
    await waitFor(() => {
      expect(document.body.textContent).toContain('Live GIS Risk Map');
    }, { timeout: 15000 });
  }, 30000);
});

describe('full simulation workflow (UI -> backend pipeline)', () => {
  test('selects EXTREME_RAIN on a location and shows the AI result', async () => {
    renderAt('/simulation');
    // wait until location options are loaded from the backend
    const select = await screen.findByRole('combobox', {}, { timeout: 15000 });
    await waitFor(() => {
      expect(select.options.length).toBeGreaterThan(10);
    }, { timeout: 15000 });

    // Choose a location (find the option containing "Aizawl")
    const aizawl = [...select.options].find((o) => o.textContent.includes('Aizawl'));
    expect(aizawl).toBeTruthy();
    fireEvent.change(select, { target: { value: aizawl.value } });

    // Choose EXTREME_RAIN scenario
    const scenarioButtons = [...document.querySelectorAll('button')].filter((b) => b.textContent.includes('EXTREME RAIN'));
    fireEvent.click(scenarioButtons[0]);

    // Click RUN SIMULATION
    const runBtn = [...document.querySelectorAll('button')].find((b) => b.textContent.includes('RUN SIMULATION'));
    fireEvent.click(runBtn);

    // Full pipeline result card appears (risk score + steps + alert)
    await waitFor(() => {
      expect(document.body.textContent).toContain('AI RISK SCORE');
    }, { timeout: 30000 });
    await waitFor(() => {
      expect(document.body.textContent).toMatch(/CRITICAL|HIGH|MODERATE/);
      expect(document.body.textContent).toContain('Pipeline Steps');
    }, { timeout: 30000 });
  }, 60000);
});
