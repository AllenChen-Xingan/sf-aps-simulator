// SF APS Funding Simulator — page logic. No framework, no build step.
// The model itself runs in assets/worker.js (Pyodide); this file only draws and plays its output.

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
const NODES = {
  C3: { label: 'Residents who ask', x: 80, y: 70, kind: 'actor' },
  C2: { label: 'Advocates', x: 80, y: 200, kind: 'actor' },
  D1: { label: 'Enforcement', x: 80, y: 330, kind: 'actor' },
  A1: { label: 'SFMTA APS engineers', x: 270, y: 70, kind: 'actor' },
  MDC: { label: 'Disability Council', x: 270, y: 200, kind: 'venue' },
  A2: { label: 'SFMTA grants staff', x: 470, y: 200, kind: 'actor' },
  DIR: { label: 'SFMTA Director', x: 470, y: 330, kind: 'actor' },
  HSIP: { label: 'HSIP (federal)', x: 670, y: 50, kind: 'venue' },
  PROPL: { label: 'Prop L (county)', x: 670, y: 140, kind: 'venue' },
  GF: { label: 'General Fund', x: 670, y: 230, kind: 'venue' },
  SS4A: { label: 'SS4A (federal)', x: 670, y: 320, kind: 'venue' },
  CT: { label: 'Caltrans', x: 880, y: 50, kind: 'actor' },
  SFCTA: { label: 'SFCTA Board', x: 880, y: 140, kind: 'actor' },
  A3: { label: 'Signal Shop crews', x: 880, y: 250, kind: 'actor' },
  PARENT: { label: 'Signal projects', x: 880, y: 350, kind: 'venue' },
};
const ALIAS = { LOCAL: 'GF' };
// Links the rules allow, drawn faintly from the start. The key one is dashed until it happens.
const STATIC_EDGES = [['C3', 'A1'], ['C2', 'MDC'], ['A2', 'C2'], ['A2', 'HSIP'], ['A2', 'PROPL'], ['A2', 'GF'],
  ['HSIP', 'CT'], ['PROPL', 'SFCTA'], ['CT', 'A2'], ['SFCTA', 'A2'], ['A2', 'A3'], ['PARENT', 'A2'], ['D1', 'A2'], ['A3', 'A2']];
const KEY_EDGE = ['A1', 'A2'];
const VERB = {
  request: 'request', classify: 'files', press: 'raise the backlog', deflect: 'deflects', start_prep: 'starts application',
  submit: 'submits', miss_deadline: 'misses deadline', approve: 'approves', reject: 'rejects', allocate: 'allocates',
  batch_fund: 'funds sites', install: 'installs', topup: 'tops up', handoff: 'hands off', enforce_up: 'escalates',
  owner_quit: 'owner leaves', owner_filled: 'owner hired', eligibility_fail: 'ineligible', red_flag: 'red flag',
  contract_out: 'contracts out', return_funds: 'funds returned', extend: 'extension', scope_add: 'adds to scope',
  reroute: 'reroutes', overrun_revert: 'overrun', partner_delay: 'partner delay', prep_abort: 'drops application',
  pathway_switch: 'switches route', rule_apply: 'applies design rule', skip_rule: 'skips design rule', pause: 'pauses',
};
const FAIL = {
  'F-a': 'a package did not reach the minimum benefit–cost ratio of 5.0', 'F-b': 'an application fell below the cycle cut-off',
  'F-c': 'an unresolved red flag made SFMTA ineligible', 'F-d': 'a delivery milestone was missed',
  'F-e': 'Caltrans denied in-house work, so the job is contracted out', 'F-f': 'a cost overrun was not covered',
  'F-g': 'the partner project slipped or was cancelled', 'F-h': 'the named owner left',
  'F-j': 'the Prop L amendment was rejected or delayed', 'F-k': 'the Director’s reallocation did not go to APS',
  'F-m': 'advocacy went quiet',
};
const LANES = [
  ['C', 'Candidate', 'can be done in-house, needs money'],
  ['N', 'Needs a full upgrade', 'needs a new signal, needs money'],
  ['Fi', 'Funded: city crews', ''],
  ['Fh', 'Funded: HSIP grant', ''],
  ['Fs', 'Waiting on a signal project', ''],
  ['I', 'Installed', ''],
];
const IMPORTANT = new Set(['approve', 'reject', 'allocate', 'submit', 'miss_deadline', 'deflect', 'pathway_switch',
  'enforce_up', 'owner_quit', 'return_funds', 'start_prep', 'eligibility_fail', 'contract_out', 'red_flag']);

const nodeName = id => (NODES[ALIAS[id] || id] || { label: id }).label;
const count = n => `${n} intersection${n === 1 ? '' : 's'}`;

function describe(e) {
  const n = e.intersections ? e.intersections.length : 0;
  const a = nodeName(e.actor), t = nodeName(e.target), d = e.detail ? ` (${e.detail})` : '';
  if (e.action.startsWith('failure:')) return `Setback: ${FAIL[e.action.slice(8)] || e.action.slice(8)}${d}.`;
  switch (e.action) {
    case 'press': return 'Advocates raise the APS backlog at the Disability Council.';
    case 'deflect': return `${a} reply that there is no money for APS${d}.`;
    case 'start_prep': return `${a} start preparing an APS application to ${t}.`;
    case 'submit': return n ? `${a} submit an application to ${t} covering ${count(n)}${d}.` : `${a}: application to ${t}${d}.`;
    case 'miss_deadline': return `${a} miss the ${t} deadline; no application filed.`;
    case 'approve': return n ? `${a} approve funding for ${count(n)}${d}.` : `${a} approve${d}.`;
    case 'reject': return `${a} reject the application${n ? ` covering ${count(n)}` : ''}${d}.`;
    case 'allocate': return `${a} allocate money for ${n ? count(n) : 'APS'}${d}.`;
    case 'batch_fund': return `${count(n)} move to funded.`;
    case 'handoff': return `${count(n)} handed to city crews after the HSIP design phase.`;
    case 'install': return `${count(n)} installed${e.detail ? ` (${e.detail})` : ''}.`;
    case 'topup': return `${a} cover a cost overrun${d}.`;
    case 'enforce_up': return `External pressure escalates${d}.`;
    case 'owner_quit': return 'The named owner of APS funding leaves; the post is vacant.';
    case 'owner_filled': return 'A new owner of APS funding is in post.';
    case 'pathway_switch': return `Signpost crossed: the pathway switches to its next step${d}.`;
    case 'rule_apply': return `Design rule applied: APS added to hardware work at ${count(n)}${d}.`;
    case 'skip_rule': return `Hardware work done without APS at ${count(n)}${d}.`;
    case 'pause': return `${a} pause${d}.`;
    case 'scope_add': return `${count(n)} added to the scope of planned projects.`;
    case 'reroute': return `${count(n)} rerouted after a parent project slipped.`;
    case 'overrun_revert': return `${count(n)} back to the waiting list after a cost overrun.`;
    case 'return_funds': return `HSIP funds returned for ${count(n)}; back to the waiting list.`;
    default: return `${a} → ${t}: ${VERB[e.action] || e.action}${n ? `, ${count(n)}` : ''}${d}.`;
  }
}

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
let modelReady = false, reqId = 0;
const pending = new Map();
worker.onmessage = ev => { const p = pending.get(ev.data.id); if (p) { pending.delete(ev.data.id); p(ev.data); } };
const callWorker = (type, request) => new Promise(res => { const id = ++reqId; pending.set(id, res); worker.postMessage({ id, type, request }); });
callWorker('init').then(r => {
  const box = $('#model-status');
  if (r.ok) { modelReady = true; box.textContent = 'Model ready.'; box.classList.add('ok'); }
  else { box.textContent = 'The model could not load (' + r.error + '); Run plays recorded runs with default settings.'; box.classList.add('warn'); }
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
    wrap.innerHTML = `<label for="${id}">${s.label_en}${only}</label><select id="${id}"><option value="${s.low}">${s.low}</option><option value="${s.high}">${s.high}</option></select>`;
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
  for (const n of ['sw_si02', 'sw_line', 'sw_relax', 'sw_ss4a']) { const s = state.schema.find(x => x.name === n); if (s) paramControl(s, sw); }
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
class Stage {
  constructor(host, title) {
    this.root = document.createElement('section');
    this.root.className = 'stage';
    this.root.setAttribute('aria-label', title);
    this.root.innerHTML = `<h3>${title}</h3>
      <figure class="net-fig"><div class="net"></div>
        <figcaption>Red: what happens this month. Dashed: grants staff taking up the request list — not yet.</figcaption></figure>
      <figure class="lanes-fig"><div class="lanes"></div>
        <figcaption>Each dot is one requested intersection; ringed dots have the most injury crashes.</figcaption></figure>
      <div class="visually-hidden"><table class="counts"><caption>Intersections by status, <span class="cmonth">start</span></caption>
        <thead><tr><th scope="col">Status</th><th scope="col">Count</th></tr></thead><tbody></tbody></table></div>`;
    host.appendChild(this.root);
    scrollRegions(this.root);
    this.drawNetwork();
    this.drawLanes();
  }

  drawNetwork() {
    const s = svg('svg', { viewBox: '0 0 960 400', role: 'img', 'aria-label': 'Network of actors and funding venues. Changes are described in the event log below.' }, $('.net', this.root));
    this.edgeLayer = svg('g', {}, s);
    this.labelLayer = svg('g', {}, s);
    const nodes = svg('g', {}, s);
    this.edges = {};
    for (const [a, b] of STATIC_EDGES) this.edge(a, b);
    const k = this.edge(...KEY_EDGE); k.line.classList.add('key'); k.line.setAttribute('stroke-dasharray', '6 5');
    this.nodeEls = {};
    for (const [id, n] of Object.entries(NODES)) {
      const g = svg('g', { class: 'node ' + n.kind, transform: `translate(${n.x},${n.y})` }, nodes);
      if (n.kind === 'venue') svg('rect', { x: -62, y: -16, width: 124, height: 32, rx: 4 }, g);
      else svg('rect', { x: -66, y: -16, width: 132, height: 32, rx: 16 }, g);
      const t = svg('text', { 'text-anchor': 'middle', dy: '0.35em' }, g); t.textContent = n.label;
      this.nodeEls[id] = g;
    }
  }

  edge(a, b) {
    a = ALIAS[a] || a; b = ALIAS[b] || b;
    if (!NODES[a] || !NODES[b] || a === b) return null;
    const key = [a, b].sort().join('|');
    if (this.edges[key]) return this.edges[key];
    const A = NODES[a], B = NODES[b];
    const mx = (A.x + B.x) / 2, my = (A.y + B.y) / 2;
    const dx = B.x - A.x, dy = B.y - A.y, len = Math.hypot(dx, dy) || 1;
    const cx = mx - dy / len * 18, cy = my + dx / len * 18;
    const line = svg('path', { d: `M${A.x},${A.y} Q${cx},${cy} ${B.x},${B.y}`, class: 'edge' }, this.edgeLayer);
    const label = svg('text', { x: cx, y: cy - 4, 'text-anchor': 'middle', class: 'elabel' }, this.labelLayer);
    return (this.edges[key] = { line, label, used: false });
  }

  drawLanes() {
    const W = 960, rowH = 58, top = 6;
    const s = svg('svg', { viewBox: `0 0 ${W} ${top + rowH * LANES.length}`, role: 'img', 'aria-label': 'Intersections by status. Counts are in the table below.' }, $('.lanes', this.root));
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

  reset(run) {
    this.run = run;
    for (const e of Object.values(this.edges)) { e.used = false; e.line.classList.remove('hot', 'used'); e.label.textContent = ''; }
    for (const g of Object.values(this.nodeEls)) g.classList.remove('hot');
    this.dotLayer.replaceChildren(); this.dots = {};
    this.status = { ...run.initial_states };
    this.high = new Set(run._high || []);
    for (const k of Object.keys(this.status)) this.addDot(k);
    this.layout();
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
        const x = x0 + col * gap, y = g.y + 12 + (row % 3) * 13;
        this.dots[k].setAttribute('transform', `translate(${x},${y})`);
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
    for (const e of Object.values(this.edges)) { e.line.classList.remove('hot'); if (!reduceMotion()) e.label.textContent = ''; }
    for (const g of Object.values(this.nodeEls)) g.classList.remove('hot');
    const labels = {};
    for (const e of events) {
      if (e.action === 'request') for (const k of e.intersections) if (!(k in this.status)) { this.status[k] = null; this.addDot(k); }
      for (const c of e.state_changes || []) this.status[c.key] = c.to;
      if (e.action === 'classify') for (const k of e.intersections) this.status[k] = e.detail;
      const ed = this.edge(e.actor, e.target);
      if (ed) {
        ed.used = true; ed.line.classList.add('hot', 'used');
        const key = [ALIAS[e.actor] || e.actor, ALIAS[e.target] || e.target].sort().join('|');
        if (!['request', 'classify'].includes(e.action))   // routine monthly filing: light the link, no label
          (labels[key] = labels[key] || new Set()).add(VERB[e.action] || (e.action.startsWith('failure') ? 'setback' : e.action));
        for (const id of [e.actor, e.target]) { const g = this.nodeEls[ALIAS[id] || id]; if (g) g.classList.add('hot'); }
      }
      if (e.action === 'start_prep') {
        const k = this.edges[[...KEY_EDGE].sort().join('|')];
        k.used = true; k.line.classList.add('hot', 'used'); k.line.removeAttribute('stroke-dasharray');
        k.label.textContent = 'list → application';
      }
    }
    for (const [key, set] of Object.entries(labels)) this.edges[key].label.textContent = [...set].slice(0, 2).join(', ');
    for (const k of Object.keys(this.status)) if (this.status[k] === null) delete this.status[k];
    this.layout();
    $('.cmonth', this.root).textContent = monthLong(month);
  }
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
  perRun.forEach(({ tag, events }) => {
    const req = events.filter(e => e.action === 'request').length;
    const inst = events.filter(e => e.action === 'install').reduce((a, e) => a + e.intersections.length, 0);
    const pre = tag ? tag + ': ' : '';
    if (req) lines.push(pre + `${req} new request${req > 1 ? 's' : ''} filed by residents.`);
    for (const e of events) {
      if (['request', 'classify', 'install', 'batch_fund'].includes(e.action)) continue;
      const txt = pre + describe(e);
      lines.push(txt);
      if (IMPORTANT.has(e.action) || e.action.startsWith('failure:')) spoken.push(txt);
    }
    if (inst) { const t = pre + `${count(inst)} installed.`; lines.push(t); spoken.push(t); }
  });
  if (!lines.length) return;
  const li = document.createElement('li');
  li.innerHTML = `<span class="lm">${monthShort(month)}</span> `;
  const ul = document.createElement('ul');
  for (const l of lines) { const x = document.createElement('li'); x.textContent = l; ul.appendChild(x); }
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
  player.stages = runs.map((r, i) => new Stage(host, runs.length > 1 ? `Scenario ${i ? 'B' : 'A'}: ${r.request.pathway} · ${PATHWAYS[r.request.pathway][0]}` : `${r.request.pathway} · ${PATHWAYS[r.request.pathway][0]}`));
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

function showSummary() {
  const box = $('#run-summary'); box.replaceChildren();
  for (const [i, r] of player.runs.entries()) {
    const s = r.summary, tag = player.runs.length > 1 ? (i ? 'B' : 'A') : '';
    const pct = percentileOf(r);
    const div = document.createElement('div');
    div.innerHTML = `<h4>${tag ? 'Scenario ' + tag + ': ' : ''}${r.request.pathway} · ${PATHWAYS[r.request.pathway][0]}</h4>
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
  if (withheld(r.request.pathway)) return null;
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
  const band = q && !withheld(r0.request.pathway) ? q.I_cum : null;
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
    (band ? `Band: 10th–90th percentile of the result set for ${r0.request.pathway} under ${r0.request.mechanism}; dashed: its middle.` : 'No result-set band for this pathway.');
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
function drawRobust() {
  const mech = $('#mech-view').value, tb = $('#robust tbody'); tb.replaceChildren();
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

// ---------------------------------------------------------------- run button
function currentRequest(pw) {
  const p = {}; for (const s of state.schema) p[s.name] = values[s.name];
  return { params: p, pathway: pw, mechanism: $('#mech').value, seed: Number($('#seed').value) || 0 };
}
const isDefault = req => req.mechanism === 'M-D' && req.seed === 146 && state.schema.every(s => req.params[s.name] === s.default);

async function getRun(req) {
  if (modelReady) {
    const r = await callWorker('run', req);
    if (r.ok) return r.result;
    throw new Error(r.error);
  }
  const demo = await getJSON(`results/demo/${req.pathway}.json`);
  if (!isDefault(req)) $('#model-status').textContent = 'Still loading: this is a recorded run with default settings.';
  return demo;
}

function attachHigh(run, inputsHigh) { run._high = inputsHigh; return run; }

let highKeys = [];
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
  } catch { /* rings are optional */ }
  buildControls();
  const mv = $('#mech-view');
  for (const k of state.meta.mechanisms) mv.add(new Option(k + ' · ' + MECHS[k].split(':')[0], k));
  mv.value = 'M-D';
  drawRobust(); drawReach(); drawPrim(); scrollRegions();
  mv.addEventListener('change', drawRobust);
  const m = state.meta, v = state.version;
  $('#set-desc').textContent = `${fmtInt(m.n_param_sets)} parameter sets × ${m.replicates} replicates for every pathway and mechanism (${fmtInt(m.total_runs)} runs), drawn from the base prior ranges. Run on ${m.run_date} with design version ${m.design_version}.`;
  $('#set-label').textContent = m.label;
  getJSON('results/consistency.json').then(c => {
    // only claim a pass for the exact model file that is loaded
    if (c.model_sha256_12 === v.model_sha256_12 && c.mismatches === 0)
      $('#consistency').textContent = `passed for this model version — ${c.cases} fixed cases, ${fmtInt(c.events)} events, no differences (${c.runtimes.join(' vs ')})`;
    else if (c.model_sha256_12 === v.model_sha256_12) $('#consistency').textContent = `${c.mismatches} differences found for this model version`;
  }).catch(() => {});
  $('#version-line').textContent = `In-browser model ${v.model_sha256_12} (synced ${v.synced}). Result set: design ${m.design_version}, run ${m.run_date}.`;

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
