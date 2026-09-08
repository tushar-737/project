const { chromium: pw } = require('playwright-core');
const chromium = require('@sparticuz/chromium');

(async () => {
  const execPath = await chromium.executablePath();
  const browser = await pw.launch({
    executablePath: execPath,
    args: [...chromium.args, '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
  });
  console.log('BROWSER OK');
  await browser.close();
})().catch((e) => { console.error('LAUNCH FAIL:', e.message); process.exit(1); });
