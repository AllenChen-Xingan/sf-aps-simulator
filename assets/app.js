// SF APS Funding Simulator — page logic. No framework, no build step.
// The model itself runs in assets/worker.js (Pyodide); this file only draws and plays its output.

import { NODES, ALIAS, CARDS, TYPES, RELATIONS, REFORMS, relationFor, humanize, IMPORTANT, nodeName } from './story.js';

const $ = (s, el = document) => el.querySelector(s);
const SVGNS = 'http://www.w3.org/2000/svg';
const svg = (tag, attrs = {}, parent) => {
  const el = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  if (parent) parent.appendChild(el);
  return el;
};
const reduceMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const fmtInt = n => Number(n).toLocaleString('en-US');
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const monthShort = ym => `${MONTHS[+ym.slice(5, 7) - 1]} ${ym.slice(0, 4)}`;
const monthLong = ym => `${MONTHS_LONG[+ym.slice(5, 7) - 1]} ${ym.slice(0, 4)}`;

// ---------------------------------------------------------------- vocabulary
const PATHWAYS = {
  PW0: ['Status quo', 'No change. The request list waits for whoever chooses to apply for money.'],
  PW1: ['HSIP first', 'Bundle APS with the signal-visibility upgrade (SG015) in the federal safety grant, HSIP Cycle 13. If not funded: repack for Cycle 14 with full signal upgrades and the pedestrian set-aside. If that fails: amend the county Prop L plan, then ask the Director or the General Fund.'],
  PW2: ['Local first', 'Amend the county Prop L signal plan to restore a dedicated APS line. If the SFCTA Board rejects or delays it: request General Fund money. If that fails: bundle APS into HSIP.'],
  PW3: ['Accountability first', 'Set a deadline, name an owner and report publicly. If no application is filed within the signpost period: structured negotiation with advocates. If there is still no money: advocates go to court.'],
  PW4: ['Route by intersection', 'Give each intersection its own funding route: fold it into a parent project already planned there, add it to corridor designs, and use a local line or an HSIP signal-hardware bundle for the rest. Reroute when a parent project slips.'],
  PW5: ['Design rule', 'Require APS whenever push buttons or signal hardware are replaced at a candidate intersection, paid from a capped yearly add-on budget. If too few listed intersections get it within two years: open a local APS line.'],
  PW6: ['Existing hardware line', 'Install APS through the existing signal-hardware replacement line (SG017). If that is blocked: amend Prop L, then request General Fund money, then repack for HSIP.'],
};
const MECHS = {
  'M-D': 'Combined (default): no owner after the dedicated money ran out, buck-passing, staff strain and rising costs all apply.',
  'M-A': 'No owner: after the dedicated APS money was spent nobody owns the task of applying, and requests are deflected ("no money", "ask SFCTA").',
  'M-B1': 'Staffing, narrow: hiring limits from July 2024 lower both applications and crew capacity.',
  'M-B2': 'Staffing, broad: staff strain already from January 2023.',
  'M-C1': 'Cost pressure: rising unit costs discourage applications and shrink batches.',
  'M-C2': 'Technical: a share of intersections cannot be done in-house at all.',
};
const LANES = [
  ['C', 'Candidate', 'can be done in-house, needs money'],
  ['N', 'Needs a full upgrade', 'needs a new signal, needs money'],
  ['Fi', 'Funded: city crews', ''],
  ['Fh', 'Funded: HSIP grant', ''],
  ['Fs', 'Waiting on a signal project', ''],
  ['I', 'Installed', ''],
];
const count = n => `${n} intersection${n === 1 ? '' : 's'}`;

// Horizontally scrollable tables must be reachable by keyboard (WCAG 2.1.1).
function scrollRegions(root = document) {
  root.querySelectorAll('.table-wrap').forEach(w => {
    if (w.hasAttribute('tabindex')) return;
    w.setAttribute('tabindex', '0'); w.setAttribute('role', 'region');
    const c = w.querySelector('caption');
    w.setAttribute('aria-label', c ? c.textContent.trim() : 'Table');
  });
}

// ---------------------------------------------------------------- data
const state = { schema: [], quantiles: null, runs: null, robust: null, meta: null, prim: null, reach: null, config: { withheld: {} }, version: null };
const withheld = pw => (state.config.withheld || {})[pw];
const caution = pw => (state.config.caution || {})[pw];
const notImpl = name => (state.config.not_implemented || []).includes(name);
const pwName = pw => `${pw} · ${PATHWAYS[pw][0]}`;
async function getJSON(url) { const r = await fetch(url); if (!r.ok) throw new Error(url); return r.json(); }

// ---------------------------------------------------------------- model worker
const worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });
let modelReady = false, reqId = 0, liveFP = null, liveRuntime = null;
// Many-run comparisons are shown only when the result set was produced by the very model file set that runs here.
// liveFP is computed by the worker from the bytes it actually loaded; nothing is compared before that.
const sameModel = () => !!(liveFP && state.meta && state.meta.model_fingerprint === liveFP);
const pending = new Map();
worker.onmessage = ev => { const p = pending.get(ev.data.id); if (p) { pending.delete(ev.data.id); p(ev.data); } };
const callWorker = (type, request) => new Promise(res => { const id = ++reqId; pending.set(id, res); worker.postMessage({ id, type, request }); });
callWorker('init').then(r => {
  const box = $('#model-status');
  if (r.ok) { modelReady = true; liveFP = r.fingerprint; liveRuntime = r.runtime; box.textContent = 'Model ready.'; box.classList.add('ok'); }
  else { box.textContent = 'The model could not load (' + r.error + '); Run plays recorded runs with default settings.'; box.classList.add('warn'); }
  if (state.meta) refreshComparisons();
});

// ---------------------------------------------------------------- controls
const KEY_PARAMS = ['p_deflect', 'b_own', 'oversight', 'lam_press', 'c_final', 'aps_share', 'a_line', 's_12in_C', 'k0', 'u0'];
const values = {};

function fmtVal(s, v) {
  if (s.kind === 'switch') return v ? 'on' : 'off';
  if (s.unit === 'USD' || s.unit.startsWith('USD')) return '$' + fmtInt(Math.round(v));
  const r = Math.abs(s.high - s.low) >= 20 ? 0 : Math.abs(s.high - s.low) >= 2 ? 1 : 2;
  return Number(v).toFixed(r) + (s.unit && !['switch', 'code', 'logit', '0-1', 'fraction', 'share', 'probability', 'BCR'].includes(s.unit) ? ' ' + s.unit : '');
}

function paramControl(s, host, prefix = 'p') {
  const id = prefix + '-' + s.name;
  const wrap = document.createElement('div');
  wrap.className = 'param';
  const only = s.applies_to.length < 6 ? ` <span class="only">only under ${s.applies_to.join(', ')}</span>` : '';
  if (s.kind === 'switch') {
    const ni = notImpl(s.name) ? ' <span class="only">(not yet implemented in the model)</span>' : '';
    wrap.innerHTML = `<label class="check"><input type="checkbox" id="${id}"${ni ? ' disabled' : ''}> ${s.label_en}${only}${ni}</label>`;
    const cb = $('input', wrap); cb.checked = !!values[s.name];
    cb.addEventListener('change', () => { values[s.name] = cb.checked ? 1 : 0; syncControls(s.name, wrap); });
  } else if (s.kind === 'discrete') {
    const choices = s.choices || [s.low, s.high];
    wrap.innerHTML = `<label for="${id}">${s.label_en}${only}</label><select id="${id}">${choices.map(c => `<option value="${c}">${c}</option>`).join('')}</select>`;
    const sel = $('select', wrap); sel.value = String(values[s.name]);
    sel.addEventListener('change', () => { values[s.name] = Number(sel.value); syncControls(s.name, wrap); });
  } else if (s.kind === 'uniform') {
    const step = (s.high - s.low) / 100;
    wrap.innerHTML = `<label for="${id}">${s.label_en}${only}</label>
      <div class="range"><input type="range" id="${id}" min="${s.low}" max="${s.high}" step="${step}" value="${values[s.name]}" aria-describedby="${id}-r">
      <output for="${id}" id="${id}-o"></output></div>
      <span class="hint" id="${id}-r">Range ${fmtVal(s, s.low)} to ${fmtVal(s, s.high)}</span>`;
    const inp = $('input', wrap), out = $('output', wrap);
    const show = () => { out.textContent = fmtVal(s, values[s.name]); inp.setAttribute('aria-valuetext', fmtVal(s, values[s.name])); };
    inp.addEventListener('input', () => { values[s.name] = Number(inp.value); show(); syncControls(s.name, wrap); });
    show();
  } else return;
  wrap.dataset.name = s.name;
  host.appendChild(wrap);
}

// The same parameter can appear twice (key panel and full list): keep both in step.
function syncControls(name, except) {
  document.querySelectorAll(`.param[data-name="${name}"]`).forEach(w => {
    if (w === except) return;
    const s = state.schema.find(x => x.name === name);
    const el = $('input,select', w);
    if (el.type === 'checkbox') el.checked = !!values[name];
    else el.value = values[name];
    const o = $('output', w); if (o) { o.textContent = fmtVal(s, values[name]); el.setAttribute('aria-valuetext', o.textContent); }
  });
}

function buildControls() {
  for (const s of state.schema) values[s.name] = s.default;
  for (const slot of ['A', 'B']) {
    const sel = $('#pw-' + slot);
    for (const [k, [name]] of Object.entries(PATHWAYS)) {
      const o = new Option(`${k} · ${name}${withheld(k) ? ' — ' + withheld(k) : caution(k) ? ' — ' + caution(k) : ''}`, k);
      o.disabled = !!withheld(k); sel.add(o);
    }
    sel.value = slot === 'A' ? 'PW0' : 'PW4';
    const desc = () => { $('#pw-' + slot + '-desc').textContent = PATHWAYS[sel.value][1] + (caution(sel.value) ? ' Note: ' + caution(sel.value) + '.' : ''); };
    sel.addEventListener('change', desc); desc();
  }
  const mech = $('#mech');
  for (const k of Object.keys(MECHS)) mech.add(new Option(k, k));
  const md = () => { $('#mech-desc').textContent = MECHS[mech.value]; };
  mech.addEventListener('change', md); md();

  const sw = $('#switches');
  for (const n of ['sw_si02', 'sw_si07', 'sw_line']) { const s = state.schema.find(x => x.name === n); if (s) paramControl(s, sw); }
  const kp = $('#key-params');
  for (const n of KEY_PARAMS) { const s = state.schema.find(x => x.name === n); if (s) paramControl(s, kp); }
  const all = $('#all-params');
  for (const s of state.schema) paramControl(s, all, 'all');
  $('#n-params').textContent = state.schema.length;

  $('#compare').addEventListener('change', e => { $('.pick[data-slot="B"]').hidden = !e.target.checked; $('#pw-B-desc').hidden = !e.target.checked; });
  $('#new-seed').addEventListener('click', () => { $('#seed').value = Math.floor(Math.random() * 1e6); });
  $('#reset-params').addEventListener('click', () => {
    for (const s of state.schema) { values[s.name] = s.default; syncControls(s.name, null); }
    $('#mech').value = 'M-D'; $('#mech').dispatchEvent(new Event('change')); $('#seed').value = 146;
  });
}

// ---------------------------------------------------------------- stage (network + lanes)
let stageSeq = 0;
class Stage {
  constructor(host, title, pathway) {
    this.uid = 'st' + (++stageSeq);
    this.pathway = pathway;
    this.root = document.createElement('section');
    this.root.className = 'stage';
    this.root.setAttribute('aria-label', title);
    this.root.innerHTML = `<h3>${title}</h3>
      <figure class="net-fig"><div class="net"></div>
        <figcaption>Select any box to see who it is and what it does. Hover or focus a box to name its links.
        Red dashed: the link that is usually missing — funding staff submitting an application.</figcaption></figure>
      <div class="card" hidden></div>
      <ul class="legend" aria-label="Kinds of links (focus one to highlight it)"></ul>
      <details class="rel-text"><summary>All links as a list</summary><ul class="rel-list"></ul></details>
      <figure class="lanes-fig"><div class="lanes"></div>
        <figcaption>Each dot is one requested intersection; ringed dots have the most injury crashes.</figcaption></figure>
      <div class="visually-hidden"><table class="counts"><caption>Intersections by status, <span class="cmonth">start</span></caption>
        <thead><tr><th scope="col">Status</th><th scope="col">Count</th></tr></thead><tbody></tbody></table></div>`;
    host.appendChild(this.root);
    this.drawNetwork();
    this.drawLegend();
    this.drawLanes();
    this.setPathway(pathway);
  }

  drawNetwork() {
    const s = svg('svg', { viewBox: '0 0 970 400', role: 'group', 'aria-label': 'Network of actors and funding sources. Each box is a button that opens a description.' }, $('.net', this.root));
    this.edgeLayer = svg('g', {}, s);
    this.reformLayer = svg('g', {}, s);
    this.labelLayer = svg('g', {}, s);
    const nodes = svg('g', {}, s);
    this.rels = {};
    for (const r of RELATIONS) this.rels[r.id] = this.path(r, this.edgeLayer, 'edge t-' + r.type + (r.broken ? ' broken' : ''));
    this.nodeEls = {};
    for (const [id, n] of Object.entries(NODES)) {
      const g = svg('g', { class: 'node ' + n.kind, transform: `translate(${n.x},${n.y})`, tabindex: '0', role: 'button',
        'aria-label': `${n.label}: show who this is and what it does` }, nodes);
      const r = svg('rect', { y: -16, height: 32, rx: n.kind === 'venue' ? 4 : 16 }, g);
      const t = svg('text', { 'text-anchor': 'middle', dy: '0.35em' }, g); t.textContent = n.label;
      this.sizeNode(r, t, n.label);
      this.nodeEls[id] = g;
      g.addEventListener('click', () => this.openCard(id));
      g.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); this.openCard(id); } });
      g.addEventListener('mouseenter', () => this.peek(id, true)); g.addEventListener('mouseleave', () => this.peek(id, false));
      g.addEventListener('focus', () => this.peek(id, true)); g.addEventListener('blur', () => this.peek(id, false));
    }
  }

  // Curved path between two nodes; bend picks the side so two links between the same pair do not overlap.
  path(r, layer, cls) {
    const A = NODES[r.from], B = NODES[r.to];
    const mx = (A.x + B.x) / 2, my = (A.y + B.y) / 2;
    const dx = B.x - A.x, dy = B.y - A.y, len = Math.hypot(dx, dy) || 1;
    const k = 22 * (r.bend || 0.6);
    const cx = mx - dy / len * k, cy = my + dx / len * k;
    const line = svg('path', { d: `M${A.x},${A.y} Q${cx},${cy} ${B.x},${B.y}`, class: cls }, layer);
    const label = svg('text', { x: cx, y: cy - 5, 'text-anchor': 'middle', class: 'elabel' }, this.labelLayer);
    return { line, label, rel: r, used: false };
  }

  sizeNode(r, t, label) {
    const fit = () => {
      let w = 0; try { w = t.getComputedTextLength(); } catch { /* not rendered yet */ }
      if (!w) w = label.length * 7.6;
      const W = Math.max(110, w + 28);
      r.setAttribute('x', -W / 2); r.setAttribute('width', W);
    };
    fit(); requestAnimationFrame(fit);
  }

  allLinks() { return [...Object.values(this.rels), ...(this.reformLinks || [])]; }

  // Hover / focus a node: name its links.
  peek(id, on) {
    for (const l of this.allLinks()) {
      const touches = l.rel.from === id || l.rel.to === id;
      l.line.classList.toggle('peek', on && touches);
      if (!this.running || reduceMotion()) l.label.textContent = on && touches ? l.rel.label : '';
    }
  }

  drawLegend() {
    const ul = $('.legend', this.root);
    for (const [type, name] of Object.entries(TYPES)) {
      const li = document.createElement('li');
      li.tabIndex = 0;
      li.innerHTML = `<span class="sw t-${type}${type === 'apply' ? ' broken' : ''}" aria-hidden="true"></span>${name}`;
      const hi = on => { for (const l of this.allLinks()) l.line.classList.toggle('peek', on && (l.rel.type === type)); };
      li.addEventListener('mouseenter', () => hi(true)); li.addEventListener('mouseleave', () => hi(false));
      li.addEventListener('focus', () => hi(true)); li.addEventListener('blur', () => hi(false));
      ul.appendChild(li);
    }
  }

  setPathway(pw) {
    this.pathway = pw;
    this.reformLayer.replaceChildren();
    for (const l of this.reformLinks || []) l.label.remove();
    this.reformLinks = (REFORMS[pw] || []).map(r => this.path({ ...r, type: 'reform' }, this.reformLayer, 'edge t-reform'));
    const ul = $('.rel-list', this.root); ul.replaceChildren();
    const item = (r, extra = '') => { const li = document.createElement('li'); li.textContent = `${nodeName(r.from)} → ${nodeName(r.to)}: ${r.label}${extra}`; ul.appendChild(li); };
    for (const r of RELATIONS) item(r, r.broken ? ' (allowed by the rules, but often does not happen — the missing link)' : '');
    for (const r of REFORMS[pw] || []) item(r, ' (added by this pathway)');
  }

  openCard(id) {
    const c = CARDS[id], n = NODES[id], card = $('.card', this.root);
    const links = RELATIONS.filter(r => c.rel.includes(r.id)).map(r => `<li>${nodeName(r.from)} → ${nodeName(r.to)}: ${r.label}${r.broken ? ' <em>(often missing)</em>' : ''}</li>`);
    const reform = (REFORMS[this.pathway] || []).filter(r => r.from === id || r.to === id).map(r => `<li class="reform">${nodeName(r.from)} → ${nodeName(r.to)}: ${r.label} <em>(added by ${this.pathway})</em></li>`);
    const hid = this.uid + '-card-h';
    card.setAttribute('role', 'region'); card.setAttribute('aria-labelledby', hid);
    card.innerHTML = `<div class="card-head"><h4 id="${hid}" tabindex="-1">${n.label}${n.kind === 'venue' ? ' <span class="kind">funding source or venue</span>' : ''}</h4>
      <button type="button" class="close" aria-label="Close description of ${n.label}">Close</button></div>
      <dl><dt>Who</dt><dd>${c.who}</dd><dt>In the model</dt><dd>${c.does}</dd><dt>Holds</dt><dd>${c.holds}</dd></dl>
      <p class="links-h">Links</p><ul>${links.join('')}${reform.join('')}</ul>`;
    card.hidden = false;
    for (const [k, g] of Object.entries(this.nodeEls)) g.classList.toggle('selected', k === id);
    this.cardFor = id;
    const close = () => { card.hidden = true; this.nodeEls[id].classList.remove('selected'); this.nodeEls[id].focus(); };
    $('.close', card).addEventListener('click', close);
    card.onkeydown = ev => { if (ev.key === 'Escape') close(); };
    $('h4', card).focus();
  }

  drawLanes() {
    const W = 960, rowH = 58, top = 6;
    const s = svg('svg', { viewBox: `0 0 ${W} ${top + rowH * LANES.length}`, role: 'img', 'aria-label': 'Intersections by status. Counts are in the table that follows.' }, $('.lanes', this.root));
    this.laneGeom = {};
    LANES.forEach(([id, name, sub], i) => {
      const y = top + i * rowH;
      svg('rect', { x: 0, y, width: W, height: rowH - 4, class: 'lane ' + (id === 'I' ? 'done' : '') }, s);
      const t = svg('text', { x: 10, y: y + 22, class: 'lane-name' }, s); t.textContent = name;
      if (sub) { const u = svg('text', { x: 10, y: y + 40, class: 'lane-sub' }, s); u.textContent = sub; }
      const c = svg('text', { x: W - 10, y: y + 22, 'text-anchor': 'end', class: 'lane-count' }, s);
      this.laneGeom[id] = { y, count: c };
    });
    this.dotLayer = svg('g', {}, s);
    this.dots = {};
  }

  // Before a run: show the starting list so the page is not empty.
  preview(initialStates, high) {
    this.high = new Set(high || []);
    this.dotLayer.replaceChildren(); this.dots = {};
    this.status = { ...initialStates };
    for (const k of Object.keys(this.status)) this.addDot(k);
    this.layout();
  }

  reset(run) {
    this.run = run; this.running = true;
    for (const l of this.allLinks()) { l.used = false; l.line.classList.remove('hot', 'used'); l.label.textContent = ''; }
    for (const g of Object.values(this.nodeEls)) g.classList.remove('hot');
    this.preview(run.initial_states, run._high);
  }

  addDot(k) {
    const c = svg('circle', { r: 5, class: 'dot' + (this.high.has(k) ? ' high' : '') + (k.startsWith('new-') ? ' new' : '') }, this.dotLayer);
    const t = svg('title', {}, c); t.textContent = k.startsWith('new-') ? 'New request' : k;
    this.dots[k] = c;
  }

  layout() {
    const per = {}; for (const [id] of LANES) per[id] = [];
    for (const [k, st] of Object.entries(this.status)) if (per[st]) per[st].push(k);
    const x0 = 250, x1 = 900, gap = 12;
    const cols = Math.floor((x1 - x0) / gap);
    for (const [id] of LANES) {
      const g = this.laneGeom[id];
      per[id].forEach((k, i) => {
        const col = i % cols, row = Math.floor(i / cols);
        this.dots[k].setAttribute('transform', `translate(${x0 + col * gap},${g.y + 12 + (row % 3) * 13})`);
      });
      g.count.textContent = per[id].length;
    }
    const tb = $('tbody', this.root); tb.replaceChildren();
    for (const [id, name] of LANES) {
      const tr = document.createElement('tr');
      tr.innerHTML = `<th scope="row">${name}</th><td>${per[id].length}</td>`;
      tb.appendChild(tr);
    }
  }

  applyMonth(events, month) {
    for (const l of this.allLinks()) { l.line.classList.remove('hot'); l.label.textContent = ''; }
    for (const g of Object.values(this.nodeEls)) g.classList.remove('hot');
    const shown = new Set();
    for (const e of events) {
      if (e.action === 'request') for (const k of e.intersections) if (!(k in this.status)) { this.status[k] = null; this.addDot(k); }
      for (const c of e.state_changes || []) this.status[c.key] = c.to;
      if (e.action === 'classify') for (const k of e.intersections) this.status[k] = e.detail;
      const rid = relationFor(e), l = rid && this.rels[rid];
      if (!l) continue;
      l.used = true; l.line.classList.add('hot', 'used');
      if (l.rel.broken) l.line.classList.add('mended');
      if (!['request', 'classify'].includes(e.action) && !shown.has(rid)) {   // routine filing lights the link without text
        shown.add(rid); l.label.textContent = shortVerb(e);
      }
      for (const id of [l.rel.from, l.rel.to]) this.nodeEls[id].classList.add('hot');
    }
    for (const k of Object.keys(this.status)) if (this.status[k] === null) delete this.status[k];
    this.layout();
    $('.cmonth', this.root).textContent = monthLong(month);
  }
}

// Short text shown next to a lit link.
function shortVerb(e) {
  if (e.action.startsWith('failure:')) return 'setback';
  return ({ press: 'pressure', deflect: '"no money"', start_prep: 'starts application', submit: /not submitted|below 5/.test(e.detail || '') ? 'package too weak' : 'submits',
    miss_deadline: 'misses deadline', approve: 'approved', reject: 'rejected', allocate: 'money', batch_fund: 'funded sites', handoff: 'to crews',
    install: 'installed', topup: 'top-up', enforce_up: 'escalates', rule_apply: 'APS with hardware', skip_rule: 'no budget left',
    eligibility_fail: 'ineligible', return_funds: 'funds returned', contract_out: 'contractor', red_flag: 'red flag', extend: 'extension',
    scope_add: 'added to project', reroute: 'rerouted', prep_abort: 'dropped' })[e.action] || e.action.replace(/_/g, ' ');
}

// ---------------------------------------------------------------- player
const player = { runs: [], stages: [], t: -1, timer: null, paused: false };

function byMonth(run) {
  const m = {}; for (const e of run.events) (m[e.month] = m[e.month] || []).push(e); return m;
}

function highSet(run) {
  // top quarter of the 76 listed intersections by injury-crash cost (same idea as the model's high-priority share)
  return run._high || [];
}

function logMonth(month, perRun) {
  const log = $('#log');
  const lines = [], spoken = [];
  const linkOf = e => { const r = RELATIONS.find(x => x.id === relationFor(e)); return r ? `${nodeName(r.from)} → ${nodeName(r.to)}` : ''; };
  perRun.forEach(({ tag, events }) => {
    const pre = tag ? tag + ': ' : '';
    const req = events.filter(e => e.action === 'request').length;
    if (req) lines.push([pre + `${req} new request${req > 1 ? 's' : ''} from residents joined the list.`, 'Residents who ask → SFMTA APS engineers']);
    const inst = {};
    for (const e of events) {
      if (['request', 'classify'].includes(e.action)) continue;
      if (e.action === 'install') { const k = e.actor === 'PARENT' ? 'ride' : 'crew'; inst[k] = (inst[k] || 0) + e.intersections.length; continue; }
      const txt = pre + humanize(e);
      lines.push([txt, linkOf(e)]);
      if (IMPORTANT.has(e.action) || e.action.startsWith('failure:')) spoken.push(txt);
    }
    if (inst.crew) { const t = pre + `City crews installed APS at ${count(inst.crew)}.`; lines.push([t, 'SFMTA funding staff → Signal Shop crews']); spoken.push(t); }
    if (inst.ride) { const t = pre + `${count(inst.ride)} got APS along with signal work.`; lines.push([t, 'Signal projects → Signal Shop crews']); spoken.push(t); }
  });
  if (!lines.length) return;
  const li = document.createElement('li');
  li.innerHTML = `<span class="lm">${monthLong(month)}</span>`;
  const ul = document.createElement('ul');
  for (const [l, link] of lines) {
    const x = document.createElement('li'); x.textContent = l;
    if (link) { const s = document.createElement('span'); s.className = 'loglink'; s.textContent = ' Link: ' + link; x.appendChild(s); }
    ul.appendChild(x);
  }
  li.appendChild(ul);
  log.prepend(li);
  if (spoken.length) $('#announcer').textContent = `${monthLong(month)}: ` + spoken.join(' ');
}

function tick() {
  const months = player.runs[0].months;
  player.t += 1;
  if (player.t >= months.length) { stop(true); return; }
  const mo = months[player.t];
  const per = player.runs.map((r, i) => ({ tag: player.runs.length > 1 ? (i ? 'B' : 'A') : '', events: r._byMonth[mo] || [] }));
  player.stages.forEach((s, i) => s.applyMonth(per[i].events, mo));
  logMonth(mo, per);
  $('#clock').textContent = monthLong(mo);
  drawTimeline(player.t);
}

function schedule() {
  clearTimeout(player.timer);
  if (player.paused) return;
  const sp = Number($('#speed').value);
  player.timer = setTimeout(() => { tick(); if (player.t < player.runs[0].months.length - 1) schedule(); else stop(true); }, 700 / sp);
}

function stop(done) {
  clearTimeout(player.timer);
  if (done) {
    $('#pause').disabled = true; $('#step').disabled = true;
    $('#announcer').textContent = 'Run finished. ' + summaryText(player.runs[0], player.runs.length > 1 ? 'A' : '') +
      (player.runs[1] ? ' ' + summaryText(player.runs[1], 'B') : '');
    showSummary();
  }
}

function startPlayback(runs) {
  player.runs = runs;
  for (const r of runs) r._byMonth = byMonth(r);
  const host = $('#stages'); host.replaceChildren();
  host.classList.toggle('two', runs.length > 1);
  const rec = r => r._source === 'recorded' ? ' (recorded run, default settings)' : '';
  player.stages = runs.map((r, i) => new Stage(host, (runs.length > 1 ? `Scenario ${i ? 'B' : 'A'}: ` : '') + `${r.request.pathway} · ${PATHWAYS[r.request.pathway][0]}${rec(r)}`, r.request.pathway));
  player.stages.forEach((s, i) => s.reset(runs[i]));
  $('#log').replaceChildren();
  player.t = -1; player.paused = false;
  $('#pause').disabled = false; $('#pause').textContent = 'Pause'; $('#pause').setAttribute('aria-pressed', 'false');
  $('#step').disabled = false; $('#restart').disabled = false;
  $('#run-summary').textContent = 'Running…';
  drawTimeline(-1); drawHist();
  schedule();
}

function summaryText(r, tag) {
  const s = r.summary;
  return `${tag ? 'Scenario ' + tag + ' ' : ''}(${r.request.pathway}): ${s.installed_5y} installed within five years, ${s.coverage_10y} within ten; ` +
    (s.money_flows_5y ? 'request-list money arrived within five years.' : 'no request-list money within five years.');
}

function sourceText(r) {
  const q = r.request, changed = state.schema.filter(s => q.params[s.name] !== s.default).length;
  const set = `mechanism ${q.mechanism}, seed ${q.seed}, ${changed ? changed + ' parameter' + (changed > 1 ? 's' : '') + ' changed from default' : 'default parameters'}`;
  if (r._source === 'recorded')
    return `Recorded run (${set}), played because the model was still loading` + (isDefault(r._asked) ? '.' : ' — your settings were not used. Press Run again now that the model is ready.');
  return `Run in this browser with your settings: ${set}.`;
}

function showSummary() {
  const box = $('#run-summary'); box.replaceChildren();
  for (const [i, r] of player.runs.entries()) {
    const s = r.summary, tag = player.runs.length > 1 ? (i ? 'B' : 'A') : '';
    const pct = percentileOf(r);
    const div = document.createElement('div');
    div.innerHTML = `<h4>${tag ? 'Scenario ' + tag + ': ' : ''}${r.request.pathway} · ${PATHWAYS[r.request.pathway][0]}</h4>
      <p class="source ${r._source === 'recorded' ? 'warn' : ''}">${sourceText(r)}</p>
      <dl class="kv">
        <dt>Installed within 5 years</dt><dd>${s.installed_5y}${pct !== null ? ` <span class="hint">(higher than ${pct}% of the result set for this pathway and mechanism)</span>` : ''}</dd>
        <dt>Installed within 10 years</dt><dd>${s.coverage_10y}</dd>
        <dt>Request-list money within 5 years</dt><dd>${s.money_flows_5y ? 'Yes' : 'No'}</dd>
        <dt>Pathway steps reached</dt><dd>${(r.path_nodes_reached || []).map(x => x.split(':')[1].replace(/_/g, ' ')).join(' → ')}</dd>
      </dl>`;
    box.appendChild(div);
  }
}

function setValues(r) {
  if (!state.runs) return [];
  return state.runs.rows.filter(x => x[0] === r.request.pathway && x[1] === r.request.mechanism && x[3] !== null).map(x => x[3]);
}
function percentileOf(r) {
  if (withheld(r.request.pathway) || !sameModel()) return null;
  const v = setValues(r);
  if (!v.length) return null;
  return Math.round(100 * v.filter(x => x < r.summary.installed_5y).length / v.length);
}

// ---------------------------------------------------------------- charts (plain SVG + data tables)
function drawTimeline(upto) {
  const host = $('#timeline'); host.replaceChildren();
  if (!player.runs.length || !state.quantiles) return;
  const W = 760, H = 260, L = 48, R = 16, T = 14, B = 34;
  const months = player.runs[0].months, n = months.length;
  const r0 = player.runs[0];
  const q = state.quantiles.by_pathway_mechanism[`${r0.request.pathway}|${r0.request.mechanism}`];
  const band = q && !withheld(r0.request.pathway) && sameModel() ? q.I_cum : null;
  const ys = [...(band ? band[90] : []), ...player.runs.flatMap(r => r.stocks.I_cum)];
  const ymax = Math.max(10, ...ys) * 1.05;
  const X = i => L + (W - L - R) * i / (n - 1), Y = v => T + (H - T - B) * (1 - v / ymax);
  const s = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img' }, host);
  for (let v = 0; v <= ymax; v += Math.ceil(ymax / 5 / 10) * 10) {
    svg('line', { x1: L, x2: W - R, y1: Y(v), y2: Y(v), class: 'grid' }, s);
    const t = svg('text', { x: L - 6, y: Y(v), 'text-anchor': 'end', dy: '0.35em', class: 'tick' }, s); t.textContent = v;
  }
  for (let i = 0; i < n; i += 24) { const t = svg('text', { x: X(i), y: H - 12, 'text-anchor': 'middle', class: 'tick' }, s); t.textContent = months[i].slice(0, 4); }
  const yl = svg('text', { x: 12, y: T + 4, class: 'tick' }, s); yl.textContent = 'installed';
  if (band) {
    const top = band[90].map((v, i) => `${X(i)},${Y(v)}`), bot = band[10].map((v, i) => `${X(i)},${Y(v)}`).reverse();
    svg('polygon', { points: [...top, ...bot].join(' '), class: 'band' }, s);
    svg('polyline', { points: band[50].map((v, i) => `${X(i)},${Y(v)}`).join(' '), class: 'median' }, s);
  }
  player.runs.forEach((r, k) => {
    const last = upto < 0 ? n - 1 : upto;
    const pts = r.stocks.I_cum.slice(0, last + 1).map((v, i) => `${X(i)},${Y(v)}`).join(' ');
    svg('polyline', { points: pts, class: 'run' + (k ? ' b' : '') }, s);
  });
  if (upto >= 0) svg('line', { x1: X(upto), x2: X(upto), y1: T, y2: H - B, class: 'now' }, s);
  const yrs = [12, 24, 36, 48, 60, 84, 119].filter(i => i < n);
  const desc = player.runs.map((r, k) => `${player.runs.length > 1 ? (k ? 'B' : 'A') + ' ' : ''}this run: ` + yrs.map(i => `${months[i].slice(0, 4)} ${r.stocks.I_cum[i]}`).join(', ')).join('; ');
  s.setAttribute('aria-label', `Cumulative intersections installed by month. ${desc}.` + (band ? ` Result-set middle: ${yrs.map(i => band[50][i]).join(', ')} at the same dates.` : ''));
  $('#timeline-cap').textContent = `Cumulative installs. Line${player.runs.length > 1 ? 's' : ''}: this run${player.runs.length > 1 ? ' (A solid, B dashed)' : ''}. ` +
    (band ? `Band: 10th–90th percentile of the result set for ${r0.request.pathway} under ${r0.request.mechanism} (same model version); dashed: its middle.` : sameModel() ? 'No result-set band for this pathway.' : 'No comparison shown: the result set was produced by a different model version than the one running here.');
  if (upto < 0 || upto === n - 1) fillTimelineTable(yrs, band);   // update data only; keep the disclosure open and focus in place
}

function fillTimelineTable(yrs, band) {
  const months = player.runs[0].months, t = $('#timeline-data table');
  $('thead', t).innerHTML = '<tr><th scope="col">Month</th>' + player.runs.map((_, k) => `<th scope="col">This run${player.runs.length > 1 ? (k ? ' B' : ' A') : ''}</th>`).join('') +
    (band ? '<th scope="col">Result set: 10th</th><th scope="col">middle</th><th scope="col">90th</th>' : '') + '</tr>';
  $('tbody', t).innerHTML = yrs.map(i => `<tr><th scope="row">${monthShort(months[i])}</th>` + player.runs.map(r => `<td>${r.stocks.I_cum[i]}</td>`).join('') +
    (band ? `<td>${band[10][i]}</td><td>${band[50][i]}</td><td>${band[90][i]}</td>` : '') + '</tr>').join('');
}

function drawHist() {
  const host = $('#hist'); host.replaceChildren();
  if (!state.runs || !player.runs.length) return;
  const r0 = player.runs[0];
  $('#hist-data tbody').replaceChildren();
  if (!sameModel()) { $('#hist-cap').textContent = 'No comparison shown: the result set was produced by a different model version than the one running here.'; return; }
  if (withheld(r0.request.pathway)) { $('#hist-cap').textContent = ''; return; }
  const v = setValues(r0).map(Math.round);
  if (!v.length) return;
  const lo = Math.min(...v), hi = Math.max(...v), bins = {};
  for (const x of v) bins[x] = (bins[x] || 0) + 1;
  const W = 760, H = 200, L = 48, R = 16, T = 10, B = 34, cmax = Math.max(...Object.values(bins));
  const X = x => L + (W - L - R) * (x - lo + 0.5) / (hi - lo + 1), bw = (W - L - R) / (hi - lo + 1);
  const s = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img' }, host);
  for (const [x, c] of Object.entries(bins)) svg('rect', { x: X(+x) - bw / 2 + 0.5, width: Math.max(1, bw - 1), y: T + (H - T - B) * (1 - c / cmax), height: (H - T - B) * c / cmax, class: 'bar' }, s);
  $('#hist-data tbody').innerHTML = Object.entries(bins).sort((a, b) => a[0] - b[0]).map(([x, c]) => `<tr><th scope="row">${x}</th><td>${c}</td></tr>`).join('');
  const step = Math.max(1, Math.ceil((hi - lo) / 10));
  for (let x = lo; x <= hi; x += step) { const t = svg('text', { x: X(x), y: H - 12, 'text-anchor': 'middle', class: 'tick' }, s); t.textContent = x; }
  const marks = player.runs.filter(r => r.request.pathway === r0.request.pathway);
  for (const r of marks) {
    const x = X(r.summary.installed_5y);
    svg('line', { x1: x, x2: x, y1: T, y2: H - B, class: 'now' }, s);
  }
  const pct = percentileOf(r0);
  const sorted = [...v].sort((a, b) => a - b), q = p => sorted[Math.floor(p * (sorted.length - 1))];
  s.setAttribute('aria-label', `Histogram of intersections installed within five years across ${v.length} runs of ${r0.request.pathway}: 10th percentile ${q(0.1)}, middle ${q(0.5)}, 90th percentile ${q(0.9)}. This run: ${r0.summary.installed_5y}, higher than ${pct}% of runs.`);
  $('#hist-cap').textContent = `Installed within five years for each of the ${v.length} parameter sets of ${r0.request.pathway} under ${r0.request.mechanism} in the preliminary result set (mean of ${state.meta.replicates} replicates, rounded). The vertical line is this run. Middle: ${q(0.5)}; 10th–90th percentile: ${q(0.1)}–${q(0.9)}.`;
}

// ---------------------------------------------------------------- batch results tables
const HIDDEN_MSG = () => liveFP ? 'Hidden: this result set was produced by a different model version than the one loaded here.' : 'Shown once the model has loaded and its version is checked.';

function drawRobust() {
  const mech = $('#mech-view').value, tb = $('#robust tbody'); tb.replaceChildren();
  if (!sameModel()) { tb.innerHTML = `<tr><td colspan="5">${HIDDEN_MSG()}</td></tr>`; return; }
  const pct = x => (x === null || x === undefined) ? '—' : Math.round(100 * x) + '%';
  const r1 = x => Math.round(x);
  for (const pw of Object.keys(PATHWAYS)) {
    const r = state.robust.table.find(x => x.pathway === pw && x.mechanism === mech);
    if (!r) continue;
    const tr = document.createElement('tr');
    if (withheld(pw)) {
      tr.innerHTML = `<th scope="row">${pw} · ${PATHWAYS[pw][0]}</th><td colspan="4">${withheld(pw)}</td>`;
    } else {
      tr.innerHTML = `<th scope="row">${pwName(pw)}${caution(pw) ? `<br><span class="hint">${caution(pw)}</span>` : ''}</th>
        <td>${r1(r.coverage_10y_p50)} (${r1(r.coverage_10y_p10)}–${r1(r.coverage_10y_p90)})</td>
        <td>${pct(r.P_money_flows_5y_mean)}</td>
        <td>${pw === 'PW0' ? '—' : pct(r.share_better_than_PW0)}</td>
        <td>${r1(r.max_regret)}</td>`;
    }
    tb.appendChild(tr);
  }
}

function drawReach() {
  const host = $('#reach'); host.replaceChildren();
  if (!sameModel()) { host.innerHTML = `<p class="hint">${HIDDEN_MSG()}</p>`; return; }
  const pr = state.reach.path_reach;
  let h = '<table><caption>Share of runs that reached each step of the pathway (all mechanisms pooled)</caption><thead><tr><th scope="col">Pathway</th><th scope="col">Steps reached</th></tr></thead><tbody>';
  for (const pw of Object.keys(PATHWAYS)) {
    if (!pr[pw]) continue;
    if (withheld(pw)) { h += `<tr><th scope="row">${pw} · ${PATHWAYS[pw][0]}</th><td>${withheld(pw)}</td></tr>`; continue; }
    const nodes = Object.entries(pr[pw].nodes).sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `${k.split(':')[1].replace(/_/g, ' ')}: ${Math.round(100 * v)}%`).join(' → ');
    h += `<tr><th scope="row">${pwName(pw)}${caution(pw) ? `<br><span class="hint">${caution(pw)}</span>` : ''}</th><td>${nodes}</td></tr>`;
  }
  host.innerHTML = h + '</tbody></table>';
  scrollRegions();
}

function drawPrim() {
  const host = $('#prim');
  const st = state.prim.status || '';
  host.innerHTML = state.prim.boxes ? '<p>(rule boxes available; display pending)</p>'
    : `<p class="hint">Not yet available: ${st || 'not computed'}. Rule-finding (PRIM, checked on held-out runs) is part of the full analysis and will appear here.</p>`;
}

function showConsistency() {
  const c = state.consistency, el = $('#consistency');
  if (!c || !el) return;
  if (!liveFP) { el.textContent = 'not yet verified (model still loading)'; return; }
  if (c.model_fingerprint !== liveFP) { el.textContent = 'not yet verified for the model files loaded here'; return; }
  const rt = c.browser_runtime || {};
  if (!liveRuntime || ['pyodide', 'python', 'numpy'].some(k => rt[k] !== liveRuntime[k])) {
    el.textContent = `not yet verified for this browser runtime (tested ${JSON.stringify(rt)}, loaded ${JSON.stringify(liveRuntime)})`; return;
  }
  el.textContent = c.mismatches === 0
    ? `passed for the model files and runtime loaded here (fingerprint ${liveFP.slice(0, 12)}; Pyodide ${liveRuntime.pyodide}, Python ${liveRuntime.python}, numpy ${liveRuntime.numpy}) — ${c.cases} fixed cases, ${fmtInt(c.events)} events; integers and text equal, decimals within 1e-12 relative / 1e-9 absolute; compared with ${c.runtimes[0]}`
    : `${c.mismatches} differences found for these model files`;
}

// Everything that compares against the result set is redrawn from one place, using the loaded fingerprint.
function refreshComparisons() {
  const m = state.meta, v = state.version;
  $('#set-desc').textContent = (sameModel() ? '' : HIDDEN_MSG() + ' ') + `${fmtInt(m.n_param_sets)} parameter sets × ${m.replicates} replicates for every pathway and mechanism (${fmtInt(m.total_runs)} runs), drawn from the base prior ranges. Run on ${m.run_date} with design version ${m.design_version}.`;
  $('#version-line').textContent = `Model loaded here: fingerprint ${liveFP ? liveFP.slice(0, 12) : 'not yet computed'} (files synced ${v.synced}). Result set: design ${m.design_version}, run ${m.run_date}, fingerprint ${(m.model_fingerprint || 'not recorded').slice(0, 12)}` +
    (sameModel() ? ' — same model.' : liveFP ? ' — different model, so many-run comparisons are hidden.' : '.');
  drawRobust(); drawReach(); showConsistency();
  if (player.runs.length) { drawTimeline(player.t >= player.runs[0].months.length - 1 ? -1 : player.t); drawHist(); showSummary(); }
}

// ---------------------------------------------------------------- run button
function currentRequest(pw) {
  const p = {}; for (const s of state.schema) p[s.name] = values[s.name];
  return { params: p, pathway: pw, mechanism: $('#mech').value, seed: Number($('#seed').value) || 0 };
}
const isDefault = req => req.mechanism === 'M-D' && req.seed === 146 && state.schema.every(s => req.params[s.name] === s.default);

async function getRun(req) {
  if (modelReady) {
    const r = await callWorker('run', req);
    if (r.ok) { r.result._source = 'live'; return r.result; }
    throw new Error(r.error);
  }
  const demo = await getJSON(`results/demo/${req.pathway}.json`);
  demo._source = 'recorded'; demo._asked = req;
  return demo;
}

function attachHigh(run, inputsHigh) { run._high = inputsHigh; return run; }

let highKeys = [];
// Before any run: draw the relationship map and the starting list for the chosen pathway(s).
function showPreview() {
  const host = $('#stages'); host.replaceChildren();
  const pws = [$('#pw-A').value]; if ($('#compare').checked) pws.push($('#pw-B').value);
  host.classList.toggle('two', pws.length > 1);
  player.stages = pws.map((pw, i) => {
    const st = new Stage(host, (pws.length > 1 ? `Scenario ${i ? 'B' : 'A'}: ` : '') + `${pw} · ${PATHWAYS[pw][0]} — before running`, pw);
    st.preview(state.initialStates || {}, highKeys);
    return st;
  });
}
async function onRun() {
  const btn = $('#run'); btn.disabled = true; btn.textContent = 'Running…';
  try {
    const reqs = [currentRequest($('#pw-A').value)];
    if ($('#compare').checked) reqs.push(currentRequest($('#pw-B').value));
    const runs = [];
    for (const q of reqs) runs.push(attachHigh(await getRun(q), highKeys));
    startPlayback(runs);
  } catch (e) {
    $('#model-status').textContent = 'The run failed: ' + e.message;
  } finally { btn.disabled = false; btn.textContent = 'Run'; }
}

// ---------------------------------------------------------------- boot
async function boot() {
  [state.schema, state.meta, state.quantiles, state.robust, state.prim, state.reach, state.version] = await Promise.all(
    ['model/abm/params-schema.json', 'results/meta.json', 'results/quantiles.json', 'results/robustness.json',
      'results/prim.json', 'results/pathways.json', 'model/abm/version.json'].map(getJSON));
  try { state.config = await getJSON('config.json'); } catch { /* no flags */ }
  getJSON('results/runs-lite.json').then(r => { state.runs = r; if (player.runs.length) { drawHist(); showSummary(); } });
  // top quarter of listed intersections by injury-crash cost: ring on the dot
  try {
    const inp = await getJSON('model/abm/inputs.json');
    const CC = { KA: 2379000, B: 213000, C: 121000 };
    const sev = r => { const c = r.crashes || {}; let v = 0; for (const g of ['pb', 'nonpb']) for (const k of ['KA', 'B', 'C']) v += (c[`${g}_${k}_w5`] || 0) * CC[k]; return v; };
    const sorted = [...inp.pending76].sort((a, b) => sev(b) - sev(a) || a.key.localeCompare(b.key));
    highKeys = sorted.slice(0, Math.ceil(sorted.length / 4)).map(r => r.key);
    state.initialStates = Object.fromEntries(inp.pending76.map(r => [r.key, r.state]));
  } catch { /* rings are optional */ }
  buildControls();
  showPreview();
  for (const id of ['#pw-A', '#pw-B', '#compare']) $(id).addEventListener('change', () => {
    clearTimeout(player.timer); player.runs = [];           // a new choice goes back to the map until Run is pressed
    $('#pause').disabled = true; $('#step').disabled = true; $('#restart').disabled = true; $('#clock').textContent = '';
    showPreview();
  });
  const mv = $('#mech-view');
  for (const k of state.meta.mechanisms) mv.add(new Option(k + ' · ' + MECHS[k].split(':')[0], k));
  mv.value = 'M-D';
  drawPrim(); scrollRegions();
  mv.addEventListener('change', drawRobust);
  $('#set-label').textContent = state.meta.label;
  getJSON('results/consistency.json').then(c => { state.consistency = c; showConsistency(); }).catch(() => {});
  refreshComparisons();

  $('#run').addEventListener('click', onRun);
  $('#pause').addEventListener('click', () => {
    player.paused = !player.paused;
    $('#pause').textContent = player.paused ? 'Resume' : 'Pause';
    $('#pause').setAttribute('aria-pressed', String(player.paused));
    if (!player.paused) schedule(); else clearTimeout(player.timer);
  });
  $('#step').addEventListener('click', () => {
    player.paused = true; clearTimeout(player.timer);
    $('#pause').textContent = 'Resume'; $('#pause').setAttribute('aria-pressed', 'true');
    tick();
  });
  $('#restart').addEventListener('click', () => startPlayback(player.runs));
  $('#speed').addEventListener('change', () => { if (!player.paused && player.runs.length) schedule(); });
}
boot().catch(e => { $('#model-status').textContent = 'Could not load the page data: ' + e.message; });
