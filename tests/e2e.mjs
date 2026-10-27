// Headless browser check: page loads, the in-browser model runs, the animation plays,
// compare mode works, no console errors, and axe finds no WCAG 2.1 A/AA violations.
// Run: node tests/e2e.mjs   (serves the site on a local port by itself)
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import http from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { writeFileSync, mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, '..');
const PORT = 8765, URL0 = `http://127.0.0.1:${PORT}/`;
// Small in-process static server (more robust under load than python's http.server).
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.wasm': 'application/wasm', '.zip': 'application/zip', '.whl': 'application/zip', '.py': 'text/plain', '.gz': 'application/gzip', '.txt': 'text/plain' };
const srv = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, URL0).pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(root, path.normalize(p));
  if (!f.startsWith(root) || !existsSync(f) || !statSync(f).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream', 'Content-Length': statSync(f).size });
  createReadStream(f).pipe(res);
}).listen(PORT, '127.0.0.1');
await new Promise(r => srv.once('listening', r));
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
      // Formal result set: the table shows what results/robustness.json says (M-D, main view), variant rows included.
      if (same) {
        const R = JSON.parse(readFileSync(path.join(here, '..', 'results', 'robustness.json'), 'utf8'));
        const pc = x => Math.round(100 * x) + '%';
        const want = pw => {
          const tab = pw.includes('approval') ? R.table_variant_approval : R.table;
          const z = pw.includes('approval') ? R.table_variant_approval : R.table_zero_direct;
          const a = tab.find(x => x.pathway === pw && x.mechanism === 'M-D' && (x.control || 'positive') === 'positive');
          const b = z.find(x => x.pathway === pw && x.mechanism === 'M-D' && x.control === 'zero_direct');
          return [pc(a.P_money_flows_5y_mean), pc(a.share_better_than_PW0), pc(b.share_better_than_PW0)];
        };
        const rows = await page.$$eval('#robust tbody tr', trs => trs.map(tr => [tr.querySelector('th').textContent, ...[...tr.querySelectorAll('td')].map(td => td.textContent)]));
        const got = name => { const r = rows.find(x => x[0].startsWith(name)); return r ? [r[2], r[3], r[4]] : null; };
        const pairs = [['PW4 · ', 'PW4'], ['PW4 + approval', 'PW4-approval'], ['PW5 + approval', 'PW5-approval'], ['PW3 · ', 'PW3']];
        const bad = pairs.filter(([n, k]) => JSON.stringify(got(n)) !== JSON.stringify(want(k)));
        ok('pathway table matches the result file, variant rows included', rows.length === 9 && !bad.length, bad.map(b => b[0]).join(',') || `${rows.length} rows`);
        await page.selectOption('#line-view', 'pooled');
        ok('pooled view: variant rows say they were not run', /computed only for sets with no standing line[\s\S]*cannot be run here/.test(await page.textContent('#robust tbody')));
        await page.selectOption('#line-view', 'main');
        const prim = await page.$$eval('#prim tbody tr', trs => trs.map(tr => tr.textContent));
        ok('PRIM conditions shown for every pathway', prim.length === 7 && /standing local line/.test(prim[0]) && /written for APS/.test(prim[4]), prim[0]);
        const body = await page.textContent('body');
        ok('no stale wording', !/\$580|580k|580,000|preliminary result set|base prior|display pending|Not yet available|max_regret|up to 10%|undefined|NaN/.test(body));
        const pw5v = await page.$$eval('#reach tbody tr', trs => (trs.find(tr => /PW5 \+ approval/.test(tr.textContent)) || {}).textContent || '');
        ok('variant steps in model order with plain names', /start: 100% → local line triggered[^→]*→ Prop L amendment requested[^→]*→ General Fund requested/.test(pw5v), pw5v.slice(0, 120));
        const { humanize } = await import('../assets/story.js');
        ok('SG017 events not described as a Prop L amendment',
          /SG017/.test(humanize({ action: 'approve', actor: 'SFCTA', detail: 'SG017 allocation includes new APS', intersections: [] })) &&
          /SG017/.test(humanize({ action: 'failure:F-j', actor: 'SFCTA', detail: 'SG017 allocation limited to replacement' })));
        await page.check('#p-sw_line'); await page.click('#run');
        await page.waitForFunction(() => /standing local APS line at the start/.test(document.querySelector('#hist-cap').textContent), null, { timeout: 60000 });
        ok('line switched on: run comparison hidden, not mixed with the main view', await page.$('#hist svg rect.bar') === null && !/higher than/.test(await page.textContent('#run-summary')));
        await page.uncheck('#p-sw_line');
      }
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
  await browser.close(); srv.close();
}
ok('no console errors', out.console.filter(x => !/favicon/.test(x)).length === 0, out.console.slice(0, 5).join(' | '));
writeFileSync(path.join(here, 'e2e-report.json'), JSON.stringify(out, null, 1));
process.exit(out.checks.every(c => c.pass) ? 0 : 1);
