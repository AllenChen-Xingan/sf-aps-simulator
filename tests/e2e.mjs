// Headless browser check: page loads, the in-browser model runs, the animation plays,
// compare mode works, no console errors, and axe finds no WCAG 2.1 A/AA violations.
// Run: node tests/e2e.mjs   (serves the site on a local port by itself)
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, '..');
const PORT = 8765, URL0 = `http://127.0.0.1:${PORT}/`;
const srv = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], { cwd: root, stdio: 'ignore' });
await new Promise(r => setTimeout(r, 800));
const shots = path.join(here, 'screenshots'); mkdirSync(shots, { recursive: true });
const out = { checks: [], console: [], axe: {} };
const ok = (name, cond, info = '') => { out.checks.push({ name, pass: !!cond, info }); console.log((cond ? 'PASS ' : 'FAIL ') + name + (info ? ' — ' + info : '')); };
const browser = await chromium.launch();
try {
  for (const scheme of ['light', 'dark']) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: scheme });
    const page = await ctx.newPage();
    page.on('console', m => { if (['error', 'warning'].includes(m.type())) out.console.push(`${scheme}: ${m.type()}: ${m.text()}`); });
    page.on('pageerror', e => out.console.push(`${scheme}: pageerror: ${e.message}`));
    await page.goto(URL0);
    await page.waitForSelector('#robust tbody tr', { state: 'attached' });
    if (scheme === 'light') {
      // Before any run: the relationship map is drawn, and actor cards open and close by keyboard.
      ok('map drawn before running', (await page.$$('.stage .net path.edge')).length >= 19 && (await page.$$('.stage .net path.edge.broken')).length === 4);
      await page.focus('.stage .node[aria-label^="SFMTA funding staff"]'); await page.keyboard.press('Enter');
      ok('actor card opens by keyboard', /only actor in the model that makes a choice/.test(await page.textContent('.stage .card')) && await page.evaluate(() => document.activeElement.tagName === 'H4'));
      await page.screenshot({ path: path.join(shots, 'card-open.png') });
      await page.keyboard.press('Escape');
      ok('Escape closes card and returns focus', await page.$eval('.stage .card', c => c.hidden) && await page.evaluate(() => document.activeElement.getAttribute('role') === 'button'));
      ok('links available as a text list', (await page.$$('.stage .rel-list li')).length >= 19);
      const t0 = Date.now();
      await page.waitForSelector('#model-status.ok', { timeout: 180000 });
      ok('in-browser model loads', true, `${((Date.now() - t0) / 1000).toFixed(1)} s`);
      await page.selectOption('#pw-A', 'PW4');
      await page.selectOption('#speed', '10');
      await page.click('#run');
      await page.waitForFunction(() => document.querySelectorAll('#log > li').length >= 5, null, { timeout: 30000 });
      ok('log lines name their link', (await page.$$('#log .loglink')).length > 0);
      ok('animation plays and log fills', true);
      ok('announcer speaks', (await page.textContent('#announcer')).length > 10, (await page.textContent('#announcer')).slice(0, 120));
      await page.waitForFunction(() => !document.querySelector('#step') || document.querySelector('#step').disabled, null, { timeout: 60000 });
      const lanes = await page.$$eval('.stage .counts tbody td', tds => tds.map(t => +t.textContent));
      ok('run finished, lane counts present', lanes.length === 6, lanes.join(','));
      ok('summary shown', /Installed within 5 years/.test(await page.textContent('#run-summary')));
      ok('timeline drawn', await page.$('#timeline svg polyline.run') !== null);
      const same = await page.evaluate(() => /same model\./.test(document.querySelector('#version-line').textContent));
      if (same) ok('histogram drawn (result set matches loaded model)', await page.$('#hist svg rect.bar') !== null);
      else ok('comparison hidden (result set from another model version)', /different model version/.test(await page.textContent('#hist-cap')) && await page.$('#hist svg rect.bar') === null);
      await page.screenshot({ path: path.join(shots, 'desktop-light-run.png'), fullPage: true });
      // open every disclosure so axe also checks their contents
      await page.$$eval('details', ds => ds.forEach(d => { d.open = true; }));
      ok('histogram table matches comparison state', same ? (await page.$$('#hist-data tbody tr')).length > 3 : (await page.$$('#hist-data tbody tr')).length === 0);
      ok('consistency verified against the loaded model files and runtime', /passed for the model files and runtime loaded here/.test(await page.textContent('#consistency')), (await page.textContent('#consistency')).slice(0, 80));
      await page.locator('#sim').screenshot({ path: path.join(shots, 'desktop-light-sim.png') });
      // keyboard: tab to Run and press Enter
      await page.check('#compare');
      await page.selectOption('#pw-B', 'PW0');
      await page.focus('#run'); await page.keyboard.press('Enter');
      await page.waitForFunction(() => document.querySelectorAll('.stage').length === 2, null, { timeout: 30000 });
      ok('compare mode shows two stages (keyboard start)', true);
      await page.click('#pause');
      ok('pause toggles aria-pressed', (await page.getAttribute('#pause', 'aria-pressed')) === 'true');
      await page.click('#step');
      ok('step works', true);
    }
    const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
    out.axe[scheme] = { violations: axe.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, help: v.help, sample: v.nodes[0]?.target })), passes: axe.passes.length, incomplete: axe.incomplete.map(v => v.id) };
    ok(`axe ${scheme}: no violations`, axe.violations.length === 0, axe.violations.map(v => `${v.id}(${v.nodes.length})`).join(' '));
    await page.screenshot({ path: path.join(shots, `desktop-${scheme}-top.png`) });
    await ctx.close();
  }
  // Run while the model is still loading (runtime download held back): the result must say it is a
  // recorded run and that the user's settings were not used, and keep saying so after the model is ready.
  {
    const ctx = await browser.newContext();
    const pg = await ctx.newPage();
    await pg.route('**/pyodide.asm.wasm', async r => { await new Promise(x => setTimeout(x, 6000)); await r.continue(); });
    await pg.goto(URL0); await pg.waitForSelector('#robust tbody tr', { state: 'attached' });
    await pg.$eval('details.fold:nth-of-type(2)', d => { d.open = true; });
    await pg.fill('#seed', '999');
    await pg.selectOption('#speed', '10');
    await pg.click('#run');
    await pg.waitForSelector('.source.warn');
    ok('recorded run labelled while loading', /your settings were not used/.test(await pg.textContent('#run-summary')));
    await pg.waitForSelector('#model-status.ok', { timeout: 120000 });
    ok('label persists after model is ready', /Recorded run/.test(await pg.textContent('#run-summary')));
    const sameV = await pg.evaluate(() => /same model\./.test(document.querySelector('#version-line').textContent));
    const hiddenNow = await pg.$('#robust tbody tr td[colspan]') !== null;
    ok('after load, comparisons shown only if the result set matches the loaded model', sameV ? !hiddenNow : hiddenNow, sameV ? 'same model: shown' : 'different model: hidden');
    await ctx.close();
  }
  const m = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: 'light', reducedMotion: 'reduce' });
  const p = await m.newPage();
  await p.goto(URL0); await p.waitForSelector('#robust tbody tr', { state: 'attached' });
  const sw = await p.evaluate(() => document.documentElement.scrollWidth);
  ok('mobile: no horizontal scroll', sw <= 390, `scrollWidth ${sw}`);
  await p.click('#run');
  await p.waitForSelector('.stage', { timeout: 60000 });
  await p.waitForTimeout(1500);
  await p.screenshot({ path: path.join(shots, 'mobile-run.png'), fullPage: false });
  const ax = await new AxeBuilder({ page: p }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  out.axe.mobile = { violations: ax.violations.map(v => ({ id: v.id, nodes: v.nodes.length, help: v.help })) };
  ok('axe mobile reduced-motion: no violations', ax.violations.length === 0, ax.violations.map(v => v.id).join(' '));
  await m.close();
} finally {
  await browser.close(); srv.kill();
}
ok('no console errors', out.console.filter(x => !/favicon/.test(x)).length === 0, out.console.slice(0, 5).join(' | '));
writeFileSync(path.join(here, 'e2e-report.json'), JSON.stringify(out, null, 1));
process.exit(out.checks.every(c => c.pass) ? 0 : 1);
