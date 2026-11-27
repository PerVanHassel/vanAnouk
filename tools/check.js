// Opens every page of the local copy, lists requests that fail locally and
// requests that still go to vananouk.nl, and saves screenshots.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const base = process.argv[2];          // e.g. http://127.0.0.1:8765
const shotDir = process.argv[3];
const pages = process.argv.slice(4);

(async () => {
  fs.mkdirSync(shotDir, { recursive: true });
  const browser = await chromium.launch();
  const missing = new Set();
  const live = new Set();
  const consoleErrors = [];
  for (const [w, h, tag] of [[1440, 900, 'desktop'], [390, 844, 'mobile']]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const page = await ctx.newPage();
    page.on('response', r => {
      if (r.url().startsWith(base) && r.status() >= 400) missing.add(r.status() + ' ' + r.url().slice(base.length));
    });
    page.on('request', r => { if (/\/\/(www\.)?vananouk\.nl\//.test(r.url())) live.add(r.url()); });
    page.on('requestfailed', r => { if (r.url().startsWith(base)) missing.add('FAILED ' + r.url().slice(base.length)); });
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(tag + ' ' + page.url().slice(base.length) + ': ' + m.text().slice(0, 200)); });
    for (const p of pages) {
      await page.goto(base + p, { waitUntil: 'networkidle' }).catch(e => missing.add('GOTO ' + p + ' ' + e.message));
      await page.waitForTimeout(2500);
      // scroll to trigger lazy content and appear-animations
      await page.evaluate(async () => {
        for (let y = 0; y < document.body.scrollHeight; y += 400) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(1200);
      const name = (p.replace(/\//g, '_').replace(/^_|_$/g, '') || 'home') + '-' + tag + '.png';
      await page.screenshot({ path: path.join(shotDir, name), fullPage: true });
    }
    await ctx.close();
  }
  await browser.close();
  console.log('MISSING:\n' + [...missing].sort().join('\n'));
  console.log('STILL TO LIVE SITE:\n' + [...live].sort().join('\n'));
  console.log('CONSOLE ERRORS:\n' + [...new Set(consoleErrors)].join('\n'));
})();
