"""SF APS request channel: scenario model (design 02, version 4). STATUS: dev, priors not calibrated.

Standard library + numpy only; no file reads at import. Entry point:

    run(params, pathway, mechanism, seed, start="2026-07", horizon_months=120,
        emit_events=False, inputs=None) -> dict

`inputs` is the dict in model/data/inputs.json (see load_inputs). One numpy
Generator is created inside run() from `seed`; nothing else is random.
Scenario exploration under stated rules, not a forecast.
"""
import json
import math

import numpy as np

from params import default_params, param_schema  # noqa: F401  (re-exported for callers)

PATHWAYS = ['PW0', 'PW1', 'PW2', 'PW3', 'PW4', 'PW5', 'PW6']
MECHANISMS = ['M-A', 'M-B1', 'M-B2', 'M-C1', 'M-C2', 'M-D']
RANK = {'high': 0, 'medium': 1, 'low': 2}
CC = {'KA': 2379000.0, 'B': 213000.0, 'C': 121000.0}       # LRSM 2026 App. D, signalized
SG105_END = '2024-06'                                     # dedicated money exhausted (ledger 4.1)
HSIP_CYCLES = {'C13': 2026, 'C14': 2028, 'C15': 2030, 'C16': 2032, 'C17': 2034}


# ---------------------------------------------------------------- time helpers
def mi(s):
    y, m = s[:7].split('-')
    return (int(y) - 2020) * 12 + int(m) - 1


def ms(i):
    return f'{2020 + i // 12:04d}-{i % 12 + 1:02d}'


def load_inputs(path):
    """Read inputs.json (CPython helper; the browser passes the parsed dict)."""
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------- mechanism switches (design D3.2)
def switches(mech):
    return {
        'owner_drop': mech in ('M-A', 'M-D'),
        'deflect': mech in ('M-A', 'M-D'),
        'strain': mech in ('M-B1', 'M-B2', 'M-D'),
        'strain_start': '2023-01' if mech == 'M-B2' else '2024-07',
        'cost': mech in ('M-C1', 'M-D'),
        'block': mech in ('M-C2', 'M-D'),
    }


class Sim:
    def __init__(self, params, pathway, mechanism, seed, start, horizon, emit, inputs):
        if pathway not in PATHWAYS or mechanism not in MECHANISMS:
            raise ValueError('unknown pathway or mechanism')
        p = dict(default_params())
        p.update(params or {})
        self.p, self.pw, self.mech, self.sw = p, pathway, mechanism, switches(mechanism)
        self.rng = np.random.default_rng(seed)
        self.t0, self.T = mi(start), horizon
        self.emit = emit
        self.events, self.nodes = [], []
        self.history = self.t0 <= mi('2022-07')
        self.inputs = inputs
        self.sites = []
        self.press = []                 # months of pressure events that stuck
        self.quiet_until = -1
        self.vacant_until = -1
        self.enf = 1                    # 0 none, 1 unknown shadow, 2 negotiation, 3 suit, 4 order
        self.specified, self.oversight = 0, p['oversight']
        self.lam_press = p['lam_press']
        self.line_on = bool(p['sw_line']) and not self.history
        self.line_amount = p['a_line'] * p['aps_share']
        self.tasks = {'LOCAL': self._task(), 'HSIP': self._task()}
        self.projects = []              # HSIP-funded projects
        self.apps = []                  # submitted HSIP applications awaiting review/approval
        self.fund_months = []           # months with a request-channel batch award
        self.fail_months = []
        self.overrun_checks = []
        self.hsip_awards = []           # months with an HSIP award (signpost for PW1)
        self.i_base = 0
        self.cost = {'SFMTA': 0.0, 'SFCTA': 0.0, 'Caltrans/HSIP': 0.0, 'refunds': 0.0}
        self.bank = 0.0                 # in-house crew capacity bank
        self.last_submit = self.t0
        self.pw_state = {'node': 0, 't_node': self.t0}
        self.rule_installs = 0
        self.init_moves = []
        self._init_sites()
        self.initial_states = {x['key']: x['state'] for x in self.sites}
        self._init_pathway()

    # ------------------------------------------------------------ setup
    @staticmethod
    def _task():
        return {'state': 'IDLE', 'ready': None, 'deflect_until': -1, 'commit': None}

    def _site(self, key, state, rank, extra=None):
        s = {'key': key, 'state': state, 'rank': rank, 'installed': None, 'listed': None,
             'route': 'unidentified', 'fold': None, 'missing_ped': False, 'crashes': None,
             'hazard_fs': True, 'blocked': False, 'via': None}
        if extra:
            s.update(extra)
        s['blocked'] = self.sw['block'] and state == 'C' and self.rng.random() < self.p['tau']
        # known work quantities, fixed when the site is listed (counted once in planned cost)
        s['adders'] = (200000.0 if self.rng.random() < self.p['q_pipe'] else 0.0) + \
                      (200000.0 if self.rng.random() < self.p['q_ramp'] else 0.0)
        return s

    def _init_sites(self):
        if self.history:
            for r in self.inputs['history']['initial_2022_07']:
                self.sites.append(self._site(r['key'], r['state'], r['rank']))
            self.i_base = self.inputs['history']['observed_stocks'][self.inputs['history']['snapshots'][0]]['I']
            self.arr_hist = {}
            for a in self.inputs['history']['arrivals']:
                self.arr_hist.setdefault(mi(a['snapshot']), []).append(a)
            return
        self.pool = self.inputs['pending76']
        for r in self.pool:
            s = self._site(r['key'], r['state'], r['rank'],
                           {'route': r['route'], 'fold': r['fold'], 'missing_ped': r['missing_ped_heads'],
                            'crashes': r['crashes'] if r['crash_matched'] else self._impute(),
                            'sg015': r.get('sg015_corridor', False)})
            if r.get('parent_finish'):
                s['parent_nominal'] = mi(r['parent_finish'])
            elif r['fold'] in ('likely', 'unverified', 'yes'):
                s['parent_nominal'] = self.t0 + 18      # undated parent (Tenderloin SS4A): assume 18 months
            self._draw_carriers(s)
            f = r['fold']
            if f == 'no_parent_done':
                if self.p['done3_real']:
                    s['state'] = 'Fi'                       # needs in-house hand-off wiring
                else:
                    s['state'], s['installed'] = 'I', self.t0 - 1  # record lag only: installed before the start
            elif f == 'no_unfunded':
                s['hazard_fs'] = False
            elif f in ('likely', 'unverified') and self.rng.random() >= self.p['pi_scope']:
                s['state'] = 'C'                            # APS fell out of the parent scope
            if r['route'] == 'unidentified' and s['state'] == 'Fs' and not self.p['fs5_parent']:
                s['hazard_fs'] = False
            self.sites.append(s)

    def _impute(self):
        """Explicit treatment of unmatched sites' crashes (never a silent zero):
        0 exclude from HSIP (None), 1 per-field median, 2 per-field 90th percentile of matched sites."""
        mode = int(self.p['crash_impute'])
        if mode == 0:
            return None
        m = [r['crashes'] for r in self.inputs['pending76'] if r['crash_matched']]
        q = 50 if mode == 1 else 90
        return {k: int(np.percentile([c[k] for c in m], q)) for k in m[0]}

    def _draw_carriers(self, s):
        p, rng = self.p, self.rng
        s['c12'] = rng.random() < p['s_12in_C']
        s['cbp'] = rng.random() < p['s_bp']
        s['clpi'] = rng.random() < p['s_lpi']
        s['cmast'] = rng.random() < p['s_mast']
        s['ccd'] = bool(s['missing_ped']) or rng.random() < p['s_cd']

    def _init_pathway(self):
        if self.history:
            return
        self._node('start')
        pw = self.pw
        if pw == 'PW1':
            self.tasks['HSIP']['commit'] = ('C13', 'sg015')
        elif pw == 'PW2':
            self._propl_amendment(self.t0)
        elif pw == 'PW3':
            self._accountability_on()
        elif pw == 'PW4':
            self.line_on = True
            self.tasks['HSIP']['commit'] = ('C13', 'sg015')
            for s in self.sites:
                if s['route'] == 'corridor' and s['state'] in ('C', 'N') and self.rng.random() < self.p['pi_scope']:
                    s['via'] = 'corridor_design'
                    s['parent_ready'] = self.t0 + int(self.p['t_parent'])
                    self.init_moves.append((s, 'Fs', 'corridor design adds APS'))
        elif pw == 'PW6':
            self.sg017_try = [mi('2026-07'), mi('2027-07')]
        elif pw == 'PW5':
            self.design_rule = True

    def _node(self, name):
        tag = f'{self.pw}:{name}'
        self.nodes.append(tag)
        self.pw_state['t_node'] = self.now if hasattr(self, 'now') else self.t0
        if len(self.nodes) > 1:
            self.ev('A2', self.pw, 'pathway_switch', detail=tag)

    def _accountability_on(self):
        self.p_owner_forced = True
        self.specified = 1
        self.oversight = min(1.0, self.oversight + 0.3)
        self.lam_press *= 2

    # ------------------------------------------------------------ helpers
    def ev(self, actor, target, action, sites=(), changes=None, detail=''):
        if self.emit:
            e = {'month': ms(self.now), 'actor': actor, 'target': target, 'action': action,
                 'intersections': [s['key'] for s in sites], 'detail': detail}
            if changes:
                e['state_changes'] = changes
            self.events.append(e)

    def move(self, s, to):
        frm = s['state']
        if to == 'I' and s.get('installed') is not None:
            raise AssertionError('site installed twice')
        if to == 'I' and frm == 'Fi' and self.now < s.get('ready_at', -1):
            raise AssertionError('install before design complete')
        if to in ('I', 'Fi') and frm == 'Fh' and s.get('proj') is not None and self.projects[s['proj']]['terminated']:
            raise AssertionError('terminated project tried to deliver')
        s['state'] = to
        if to == 'I':
            s['installed'] = self.now
        return {'key': s['key'], 'from': frm, 'to': to}

    def fail(self, code, actor='A2', target='', detail=''):
        self.fail_months.append(self.now)
        self.ev(actor, target, f'failure:{code}', detail=detail)

    def owner(self):
        if getattr(self, 'p_owner_forced', False):
            base = 1
        elif self.history:
            base = 1 if self.now < mi(SG105_END) or not self.sw['owner_drop'] else 0
        else:
            base = 0 if self.sw['owner_drop'] else 1
        return 0 if self.now < self.vacant_until else base

    def strain(self):
        if not self.sw['strain']:
            return 0.0
        a = mi(self.sw['strain_start'])
        end = mi('2026-12') + int(self.p['strain_end'])
        if self.now < a or self.now >= end:
            return 0.0
        return min(1.0, (self.now - a + 1) / max(1.0, self.p['strain_ramp']))

    def unit_cost(self):
        yrs = max(0.0, (self.now - mi('2022-07')) / 12)
        g = self.p['g_cost'] if self.sw['cost'] else 0.0
        return self.p['u0'] * (1 + g) ** yrs

    def costpress(self):
        return (self.unit_cost() - 20000.0) / 20000.0 if self.sw['cost'] else 0.0

    def pressure(self):
        k = self.p['k_decay']
        return sum(math.exp(-(self.now - m) / k) for m in self.press if m <= self.now)

    def p_start(self):
        p = self.p
        z = (p['b0'] + p['b_own'] * self.owner() + p['b_spec'] * self.specified + p['b_ov'] * self.oversight
             + p['b_pr'] * self.pressure() + p['b_enf'] * max(0, self.enf - 1)
             - (p['m_b'] * self.strain() if self.sw['strain'] else 0.0)
             - (p['m_c'] * self.costpress() if self.sw['cost'] else 0.0))
        return 1.0 / (1.0 + math.exp(-z))

    # ------------------------------------------------------------ windows
    def window(self, venue):
        y, m = 2020 + self.now // 12, self.now % 12 + 1
        if venue == 'LOCAL':
            return 1 <= m <= 6, mi(f'{y}-06')                     # decided at the July budget
        cyc = next((c for c, yr in HSIP_CYCLES.items() if yr == y), None)
        if cyc is None or self.history:
            return False, None
        return 7 <= m <= 10, mi(f'{y}-11')

    def cycle_name(self):
        y = 2020 + self.now // 12
        return next((c for c, yr in HSIP_CYCLES.items() if yr == y), None)

    # ------------------------------------------------------------ monthly step
    def step(self):
        p, rng, t = self.p, self.rng, self.now
        if self.init_moves:
            for s, to, why in self.init_moves:
                ch = self.move(s, to)
                self.ev('A2', 'PARENT', 'scope_add', [s], [ch], why)
            self.init_moves = []
        self._arrivals()
        # owner leaves (F-h)
        if t >= self.vacant_until and rng.random() < 1 - math.exp(-p['lam_quit'] / 12):
            self.vacant_until = t + int(round(p['t_vac']))
            self.fail('F-h', 'A2', 'A2', 'owner left; post vacant')
            self.ev('A2', 'A2', 'owner_quit')
            for v, tk in self.tasks.items():
                if tk['state'] == 'PREPARING' and rng.random() < p['q_drop']:
                    tk['state'] = 'IDLE'
                    self.ev('A2', v, 'prep_abort')
        if t == self.vacant_until:
            self.ev('A2', 'A2', 'owner_filled')
        # advocacy (F-m quiet spells)
        if t >= self.quiet_until and rng.random() < 1 - math.exp(-p['lam_quiet'] / 12):
            self.quiet_until = t + int(p['t_quiet'])
            self.fail('F-m', 'C2', 'MDC', 'advocacy went quiet')
        if t >= self.quiet_until and rng.random() < 1 - math.exp(-self.lam_press / 12):
            self.ev('C2', 'MDC', 'press')
            if self.sw['deflect'] and rng.random() < p['p_deflect']:
                tgt = ['SFCTA', 'GF', 'CT'][int(rng.integers(3))]
                self.ev('A2', 'C2', 'deflect', detail=f'cost / no money; pointed to {tgt}')
                for tk in self.tasks.values():
                    if tk['state'] == 'IDLE':
                        tk['deflect_until'] = t + int(p['r_back'])
            else:
                self.press.append(t)
        if rng.random() < p['eps_enf'] / 12 and self.enf < 4:
            self.enf += 1
            self.ev('D1', 'A2', 'enforce_up', detail=f'level {self.enf}')
        # tasks
        for v in ('LOCAL', 'HSIP'):
            self._task_step(v)
        self._hsip_events()
        if t % 12 == 6:
            self._local_decision()
        self._pathway_signposts()
        self._design_rule()
        self._deliver()

    def _arrivals(self):
        if self.history:
            for a in self.arr_hist.get(self.now, []):
                s = self._site(a['key'], a['state'], a['rank'])
                s['listed'] = self.now
                self.sites.append(s)
                self.ev('C3', 'A1', 'request', [s], [{'key': s['key'], 'from': None, 'to': s['state']}])
            return
        n = self.rng.poisson(self.p['lam_arr'] / 12)
        for _ in range(n):
            r = self.pool[int(self.rng.integers(len(self.pool)))]
            st = ['C', 'Fs', 'N'][int(self.rng.choice(3, p=[32 / 41, 6 / 41, 3 / 41]))]
            s = self._site(f'new-{self.now}-{len(self.sites)}', st, r['rank'],
                           {'route': 'unidentified', 'missing_ped': r['missing_ped_heads'],
                            'crashes': r['crashes'] if r['crash_matched'] else self._impute()})
            s['listed'] = self.now
            self._draw_carriers(s)
            self.sites.append(s)
            self.ev('C3', 'A1', 'request', [s], [{'key': s['key'], 'from': None, 'to': s['state']}])
            self.ev('A1', 'C3', 'classify', [s], detail=st)

    def _task_step(self, v):
        tk, t = self.tasks[v], self.now
        open_, deadline = self.window(v)
        if tk['state'] == 'IDLE' and open_ and t >= tk['deflect_until']:
            committed = tk['commit'] is not None and (v == 'LOCAL' or tk['commit'][0] == self.cycle_name())
            if committed or self.rng.random() < self.p_start():
                tk['state'], tk['ready'] = 'PREPARING', t + int(round(self.p['d_prep']))
                tk['started'] = t
                self.ev('A2', 'HSIP' if v == 'HSIP' else 'GF', 'start_prep')
        if tk['state'] == 'PREPARING' and deadline is not None and t == deadline:
            if tk['ready'] <= t:
                tk['state'] = 'IDLE'
                self.last_submit = t
                if v == 'HSIP':
                    self._submit_hsip(tk)
                else:
                    self.local_submitted = True
                    self.ev('A2', 'GF', 'submit')
            else:
                tk['state'] = 'IDLE'
                self.ev('A2', v, 'miss_deadline')
        if tk['state'] == 'PREPARING' and not open_ and deadline is None:
            tk['state'] = 'IDLE'

    # ------------------------------------------------------------ local venue (Prop L EP17 / General Fund)
    def _local_decision(self):
        if not getattr(self, 'local_submitted', False) and not self.line_on:
            return
        self.local_submitted = False
        amount = self.line_amount if self.line_on else self.p['a_local']
        if getattr(self, 'one_time', 0) > 0:
            amount += self.one_time
            self.one_time = 0
        cands = sorted([s for s in self.sites if s['state'] == 'C' and not s['blocked']],
                       key=lambda s: (RANK.get(s['rank'], 1), s['key']))
        u = self.unit_cost()
        batch, spent = [], 0.0
        for s in cands:
            c = (u + s['adders']) * (1 + self.p['k_cont'])   # contingency budgeted up front
            if spent + c > amount:
                continue
            batch.append(s)
            spent += c
        if not batch:
            return
        ch = [self.move(s, 'Fi') for s in batch]
        for s in batch:
            s['via'] = 'local'
        payer = 'SFCTA' if self.line_on else 'SFMTA'
        self.cost[payer] += spent / (1 + self.p['k_cont'])   # contingency drawn only if needed
        self.fund_months.append(self.now)
        self.ev('SFCTA' if self.line_on else 'GF', 'A2', 'allocate', batch, ch, f'${spent:,.0f}')
        self.ev('A2', 'A3', 'batch_fund', batch)
        # cost overrun is discovered when design completes, t_des months after award (F-f)
        d = self.now + int(round(self.p['t_des']))
        for s in batch:
            s['ready_at'] = d
            self.overrun_checks.append((d, s, u + s['adders'], payer))

    def _propl_amendment(self, t):
        p = self.p
        if self.rng.random() < p['q_veto']:
            self.pending_propl = (t + 3, 'veto')
        else:
            d = int(round(p['t_defer']))
            self.pending_propl = (t + 3 + d, 'defer' if d > p['th_defer'] else 'pass')

    # ------------------------------------------------------------ HSIP (design D3.3)
    def _site_bcr_parts(self, s, mode, cycle):
        """Return (annual benefit, cost, life, ok) for one site in one bundle mode."""
        p = self.p
        if s['crashes'] is None:
            return 0.0, 0.0, 10, False
        cms = []
        if s['state'] == 'C':
            if not p['sw_si02']:
                return 0.0, 0.0, 10, False
            if s['c12']:
                cms.append(('SI02', 0.15, 10, 'all', p['c_12in']))
            elif s['cbp'] and mode == 'repack':
                cms.append(('SI02', 0.15, 10, 'all', p['c_bp']))
            else:
                return 0.0, 0.0, 10, False
            if s['clpi']:
                cms.append(('SI22PB', 0.60, 10, 'pb', p['c_lpi']))
            if s['ccd'] and mode == 'repack':
                cms.append(('SI18PB', 0.25, 20, 'pb', p['c_cd']))
            cost = sum(c[4] for c in cms) + self.unit_cost() + s['adders']
        elif s['state'] == 'N' and mode == 'repack':
            if s['cmast'] and p['sw_si07']:
                cms.append(('SI07', 0.30, 20, 'all', 0.0))
            if s['ccd']:
                cms.append(('SI18PB', 0.25, 20, 'pb', 0.0))
            if s['clpi']:
                cms.append(('SI22PB', 0.60, 10, 'pb', 0.0))
            if not cms:
                return 0.0, 0.0, 10, False
            cost = p['c_full']
        else:
            return 0.0, 0.0, 10, False
        s['_cms'] = {c[0] for c in cms}
        # crashes on the upgraded approaches (share f_aff) get every countermeasure; the rest get only
        # the pedestrian/bicycle crossing measures (SI18PB, SI22PB); LRSM SI02 note, l.2021
        f = p['f_aff']
        crf_pb_in = 1 - np.prod([1 - c[1] for c in cms])
        crf_pb_out = 1 - np.prod([1 - c[1] for c in cms if c[3] == 'pb'] or [1.0])
        crf_np_in = 1 - np.prod([1 - c[1] for c in cms if c[3] == 'all'] or [1.0])
        crf_pb = f * crf_pb_in + (1 - f) * crf_pb_out
        crf_np = f * crf_np_in
        y = int(p['y_win'])
        cr = s['crashes']
        ben = 0.0
        for sev in ('KA', 'B', 'C'):
            if cycle == 'C13':
                npb, nnp = cr[f'pb_{sev}_w{y}'], cr[f'nonpb_{sev}_w{y}']
            else:
                npb = self.rng.poisson(cr[f'pb_{sev}_w5'] / 5 * y)
                nnp = self.rng.poisson(cr[f'nonpb_{sev}_w5'] / 5 * y)
            ben += (crf_pb * npb + crf_np * nnp) / y * CC[sev]
        lives = [c[2] for c in cms]
        life = min(lives) if int(p['l_rule']) == 0 else sum(lives) / len(lives)
        return ben, cost, life, True

    def _build_app(self, mode, cycle, group, cap):
        """One application instance for one site group ('C' or 'N'); the union of
        countermeasures in a group never exceeds 3 signalized-intersection types."""
        parts = []
        for s in self.sites:
            if s['state'] != group or s.get('in_app'):
                continue
            if mode == 'sg015' and not s.get('sg015'):
                continue
            ben, cost, life, ok = self._site_bcr_parts(s, mode, cycle)
            if ok and cost > 0:
                parts.append((ben * life / cost, ben * life, cost, s))
        parts.sort(key=lambda x: -x[0])
        chosen, B, Cst, union = [], 0.0, 0.0, set()
        kc = 1 + self.p['k_cont']
        for r, b, c, s in parts:
            if (Cst + c) * kc > cap or len(union | s['_cms']) > 3:   # cap check includes contingency
                continue
            if chosen and (B + b) / ((Cst + c) * kc) < 5.0:   # screen on the full cost incl. contingency
                break
            chosen.append(s)
            union |= s['_cms']
            B, Cst = B + b, Cst + c
        Cst *= kc                                        # application cost includes contingency
        if Cst > cap + 1e-6:
            raise AssertionError('application exceeds remaining $10M cap')
        bcr = B / Cst if Cst else 0.0
        if len(chosen) > 1 and bcr < 5.0:
            raise AssertionError('kept bundle fails the 5.0 floor')
        return chosen, bcr, Cst

    def _submit_hsip(self, tk):
        cyc = self.cycle_name()
        mode = tk['commit'][1] if tk['commit'] else 'as_planned'
        tk['commit'] = None
        if mode == 'as_planned':
            # SG142 as written: APS-only -> ineligible; no CRF -> BCR 0
            self.ev('A2', 'HSIP', 'submit', detail=f'{cyc} APS-only (SG142 as planned)')
            self.fail('F-a', 'CT', 'A2', 'APS-only or BCR below 5.0')
            return
        cap = max(0.0, 10_000_000 - self.p['r_other'])
        groups = ['C'] if mode == 'sg015' else ['C', 'N']
        any_ok = False
        # preparation workload: instance i is ready at start + d_prep + i * d_split
        n_ready = 1 + int(max(0, (self.now - tk.get('started', self.now) - self.p['d_prep'])) // max(self.p['d_split'], 1e-9)) if self.p['d_split'] > 0 else 99
        groups = groups[:max(1, n_ready)]
        for g in groups:
            sites, bcr, cost = self._build_app(mode, cyc, g, cap)
            if not sites or bcr < 5.0:
                self.ev('A2', 'HSIP', 'submit', detail=f'{cyc} {mode}/{g}: BCR {bcr:.1f} below 5.0, not submitted')
                self.fail('F-a', 'A2', 'HSIP', f'{g} bundle BCR below 5.0')
                continue
            cap -= cost
            any_ok = True
            aps_extra = len(sites) * self.unit_cost() if g == 'C' else 0.0   # APS hardware is inside c_full
            for s in sites:
                s['in_app'] = True
            self.apps.append({'cycle': cyc, 'sites': sites, 'bcr': bcr, 'cost': cost, 'aps_extra': aps_extra,
                              'mode': mode, 'review': mi(f'{HSIP_CYCLES[cyc]}-11'),
                              'approve': mi(f'{HSIP_CYCLES[cyc] + 1}-0{3 + int(self.rng.integers(2))}')})
            self.ev('A2', 'HSIP', 'submit', sites, detail=f'{cyc} {mode}/{g}, BCR {bcr:.1f}, ${cost:,.0f}')
        if mode == 'repack' and n_ready > len(groups):
            self._setaside(cyc)

    def _setaside(self, cyc):
        """Pedestrian-crossing set-aside, total built from components (codex 02 round 13 #1):
        per site the eligible crossing items (new countdown heads SI18PB if missing, new LPI SI22PB if
        possible, otherwise a signalized crossing upgrade SI19PB) plus APS as extra work. APS must stay
        <= 20% of the summed project total; the total must stay <= $400k (HSIP <= $360k at 90%)."""
        p = self.p
        u = self.unit_cost()
        cands = sorted([s for s in self.sites if s['state'] == 'C' and not s.get('in_app')],
                       key=lambda s: (RANK.get(s['rank'], 1), s['key']))
        chosen, items, aps = [], 0.0, 0.0
        for s in cands:
            x = (p['c_cd'] if s.get('ccd') else 0.0) + (p['c_lpi'] if s.get('clpi') else 0.0)
            if x == 0.0:
                x = p['c_xing']                      # SI19PB: install / upgrade signalized crossing
            a = u + s['adders']
            ni, na = items + x, aps + a
            if ni + na > 400000.0 or na > 0.2 * (ni + na):
                continue
            chosen.append(s)
            items, aps = ni, na
        if not chosen:
            self.ev('A2', 'HSIP', 'submit', detail=f'{cyc} set-aside not formed: APS would exceed 20% of the project')
            return
        total = items + aps
        assert aps <= 0.2 * total + 1e-6 and total <= 400000.0 + 1e-6
        for s in chosen:
            s['in_app'] = True
        self.apps.append({'cycle': cyc, 'sites': chosen, 'bcr': None, 'cost': total, 'mode': 'setaside',
                          'review': mi(f'{HSIP_CYCLES[cyc]}-11'), 'approve': mi(f'{HSIP_CYCLES[cyc] + 1}-04')})
        self.ev('A2', 'HSIP', 'submit', chosen, detail=f'{cyc} pedestrian-crossing set-aside: items ${items:,.0f} + APS ${aps:,.0f}')

    def _lrsp_valid(self):
        """Plan valid until lrsp_until; when it lapses an update starts, finishes t_lrsp months later
        and succeeds with q_lrsp; a success makes the plan valid for another 60 months. The deadline for
        finishing an update is an assumption: it must be done by the review date (not verified)."""
        p, t = self.p, self.now
        if not hasattr(self, 'lrsp_until'):
            self.lrsp_until = self.t0 + int(round(p['lrsp_until']))
            self.lrsp_upd = None
        while True:
            if t <= self.lrsp_until:
                return True
            if self.lrsp_upd is None:                     # update starts the month the plan lapses
                ok = self.rng.random() < p['q_lrsp']
                self.lrsp_upd = (self.lrsp_until + int(round(p['t_lrsp'])), ok)
            done, ok = self.lrsp_upd
            if t < done:
                return False
            self.lrsp_upd = None
            if not ok:
                self.lrsp_until = done                    # failed: try again from that month
                continue
            self.lrsp_until = done + 60

    def _agency_flagged(self):
        if not self._lrsp_valid():
            return True                      # local road safety plan not valid at review
        if self.rng.random() < self.p['rho_flag']:
            return True
        for pr in self.projects:
            if pr.get('flag_from') is not None and pr['flag_from'] <= self.now < pr.get('flag_to', 10 ** 6):
                return True
            if pr['con_at'] - pr['cs'] > 60 and self.now >= pr['cs'] + 60:
                return True
        return False

    def _hsip_events(self):
        t, p = self.now, self.p
        for a in list(self.apps):
            if a['review'] == t and not a.get('reviewed'):
                a['reviewed'] = True
                if self._agency_flagged():
                    self.apps.remove(a)
                    for s in a['sites']:
                        s['in_app'] = False
                    self.ev('CT', 'A2', 'eligibility_fail', a['sites'])
                    self.fail('F-c', 'CT', 'A2', 'red flag not cleared by review')
            elif a['approve'] == t:
                self.apps.remove(a)
                for s in a['sites']:
                    s['in_app'] = False
                if a['mode'] == 'setaside':
                    ok = self.rng.random() < p['p_sa']
                else:
                    ok = a['bcr'] >= max(5.0, p['c_final']) and self.rng.random() >= p['q_fail']
                if not ok:
                    self.ev('CT', 'A2', 'reject', a['sites'], detail=a['cycle'])
                    self.fail('F-b', 'CT', 'A2', 'below cutoff or not selected')
                    continue
                for s in a['sites']:
                    s['pre_fh'] = s['state']
                ch = [self.move(s, 'Fh') for s in a['sites']]
                cs = mi(f'{2020 + t // 12 + 1}-01')
                self._new_project(a, cs)
                self.fund_months.append(t)
                self.hsip_awards.append(t)
                self.cost['Caltrans/HSIP'] += 0.9 * a['cost']
                self.cost['SFMTA'] += 0.1 * a['cost']
                self.cost['aps_extra_budget'] = self.cost.get('aps_extra_budget', 0.0) + a.get('aps_extra', 0.0)
                self.ev('CT', 'A2', 'approve', a['sites'], ch, f"{a['cycle']} {a['mode']}")
                self.ev('A2', 'A3', 'batch_fund', a['sites'])
        for pr in self.projects:
            self._project_step(pr)

    def _new_project(self, a, cs):
        """Delivery nodes generated in order: PE -> PIF -> CON E-76 -> partner -> build."""
        p, rng = self.p, self.rng
        node = cs
        pe_at = None
        if p['sw_pe']:
            pe_at = cs + int(round(p['t_pe']))
            node = pe_at
        design_done = (pe_at if pe_at is not None else cs) + int(round(p['t_dsg']))  # design complete != PE E-76
        pif_done = (pe_at if pe_at is not None else cs) + int(round(p['t_pif']))     # PIF runs alongside design
        contract = rng.random() < p['q_pif_deny']         # PIF denied: does not delay CON E-76
        con = max(design_done, pif_done, cs + int(round(p['t_con_med'] * math.exp(0.40 * rng.standard_normal()))))
        des_done = design_done
        if a['mode'] == 'sg015':
            con += int(round(p['t_partner']))
        limit = 42 if p['sw_consult'] else 36
        pr = {'id': len(self.projects), 'terminated': False,
              'des_at': des_done,
              'sites': a['sites'], 'cs': cs, 'con_at': con, 'contract': contract, 'mode': a['mode'],
              'cancel': a['mode'] == 'sg015' and rng.random() < p['q_partner_cancel'],
              'limit': limit, 'cost': a['cost'], 'done': False,
              'build_at': (con + int(round(p['t_contract'])) + int(round(p['t_build']))) if contract else con}
        flags = []
        if pe_at is not None and pe_at - cs > 9:
            flags.append((cs + 9, pe_at + int(p['t_fix'])))
        if con - cs > limit:
            flags.append((cs + limit, con + int(p['t_fix'])))
        if flags:
            pr['flag_from'], pr['flag_to'] = min(f[0] for f in flags), max(f[1] for f in flags)
        for s in a['sites']:
            s['proj'] = pr['id']
        self.projects.append(pr)

    def _terminate(self, pr, why, to=None):
        pr['done'] = pr['terminated'] = True
        ch = []
        for s in pr['sites']:
            if s['state'] in ('Fh', 'Fi'):
                ch.append(self.move(s, to or s.get('pre_fh', 'C')))
        return ch

    def _project_step(self, pr):
        t, p = self.now, self.p
        if pr['done']:
            return
        if t == pr['des_at']:
            ratio = math.exp(p['sigma_over'] * self.rng.standard_normal())
            gap = max(0.0, ratio - 1 - p['k_cont']) * pr['cost']
            if gap > 0 and self.rng.random() < p['q_topup']:
                self.cost['SFMTA'] += gap
                self.ev('SFCTA', 'A2', 'topup', pr['sites'], detail=f'design overrun +${gap:,.0f} beyond contingency')
            elif gap > 0:
                ch = self._terminate(pr, 'overrun')
                self.ev('A2', 'HSIP', 'overrun_revert', pr['sites'], ch, 'overrun found at design; no top-up')
                self.fail('F-f', 'A2', 'HSIP', 'overrun at design, project terminated')
                return
        if pr.get('flag_from') == t:
            self.ev('CT', 'A2', 'red_flag', pr['sites'])
            self.fail('F-d', 'CT', 'A2', 'milestone missed')
        if pr['contract'] and t == pr['con_at']:
            self.ev('CT', 'A2', 'contract_out', pr['sites'])
            self.fail('F-e', 'CT', 'A2', 'PIF denied; contracting out')
            gap = (p['k_contract'] - 1) * pr['cost']
            if self.rng.random() < p['q_topup']:
                self.cost['SFMTA'] += gap
                self.ev('SFCTA', 'A2', 'topup', pr['sites'], detail=f'contracting gap +${gap:,.0f}')
            else:
                pr['gap_retry'] = t + int(round(p['t_pause']))
                pr['build_at'] += int(round(p['t_pause']))
                self.ev('A2', 'HSIP', 'pause', pr['sites'], detail=f'contracting gap ${gap:,.0f} unfunded; paused')
        if pr.get('gap_retry') == t:
            gap = (p['k_contract'] - 1) * pr['cost']
            if self.rng.random() < p['q_topup']:
                self.cost['SFMTA'] += gap
                self.ev('SFCTA', 'A2', 'topup', pr['sites'], detail=f'contracting gap +${gap:,.0f} (retry)')
            else:
                ch = self._terminate(pr, 'gap')
                self.ev('A2', 'HSIP', 'overrun_revert', pr['sites'], ch, 'contracting gap never funded; terminated')
                self.fail('F-e', 'A2', 'HSIP', 'contracting gap unfunded twice; project terminated')
                return
        if pr['cancel'] and t == pr['cs'] + 6:
            ch = self._terminate(pr, 'partner')
            self.ev('A2', 'HSIP', 'partner_delay', pr['sites'], ch, 'partner project cancelled; APS loses carrier')
            self.fail('F-g', 'A2', 'HSIP', 'partner cancelled')
            return
        if t == pr.get('ext_end') and pr['con_at'] > t:
            ch = self._terminate(pr, 'removed', 'C')
            self.cost['refunds'] += 0.1 * pr['cost']
            self.ev('A2', 'CT', 'return_funds', pr['sites'], ch, 'extension ran out')
            self.fail('F-d', 'CT', 'A2', 'extension expired without construction; removed')
            return
        if t == pr['cs'] + 60 and pr['con_at'] - pr['cs'] > 60:
            if self.rng.random() < p['e_ext']:
                pr['ext_end'] = t + int(round(p['t_ext']))   # one extension only
                self.ev('CT', 'A2', 'extend', pr['sites'], detail=f"until {ms(pr['ext_end'])}")
            else:
                ch = self._terminate(pr, 'removed', 'C')
                self.cost['refunds'] += 0.1 * pr['cost']
                self.ev('A2', 'CT', 'return_funds', pr['sites'], ch)
                self.fail('F-d', 'CT', 'A2', 'removed at 5 years; funds returned')
                return
        if t == pr['build_at']:
            pr['done'] = True
            for s in pr['sites']:
                if pr['contract']:
                    ch = self.move(s, 'I')         # contractor: construction finished
                    self.ev('PARENT', 'A2', 'install', [s], [ch], 'contractor')
                else:
                    ch = self.move(s, 'Fi')        # in-house: one chain, queue -> install
                    s['via'], s['ready_at'] = 'hsip', t
                    self.ev('A2', 'A3', 'handoff', [s], [ch], 'construction authorized; joins in-house queue')

    # ------------------------------------------------------------ pathway signposts (design D3.6)
    def _pathway_signposts(self):
        if self.history:
            return
        t, p, pw, node = self.now, self.p, self.pw, self.pw_state['node']
        funded = any(m >= self.t0 for m in self.fund_months)
        hsip_won = any(m >= self.t0 for m in self.hsip_awards)
        res = self._propl_due()
        if pw == 'PW1':
            if node == 0 and t == mi('2027-05') and not hsip_won:
                self.pw_state['node'] = 1
                self._node('C14_repack')
                self.tasks['HSIP']['commit'] = ('C14', 'repack')
            elif node == 1 and t == mi('2029-05') and not hsip_won:
                self.pw_state['node'] = 2
                self._node('PropL_amendment')
                self._propl_amendment(t)
        if pw == 'PW2' and node == 0 and res == 'fail':
            self.pw_state['node'] = 1
            self._node('GF_request')
            self.gf_try = t + (18 - t % 12) % 12 or 12
        if pw in ('PW1', 'PW2') and res is not None:
            if res == 'pass':
                self.line_on = True
                self.ev('SFCTA', 'A2', 'approve', detail='Prop L amendment adds APS line')
            else:
                self.fail('F-j', 'SFCTA', 'A2', 'Prop L amendment rejected or deferred')
                if pw == 'PW1' and self.pw_state['node'] == 2:
                    self.pw_state['node'] = 3
                    self._node('Director_or_GF')
                    if self.rng.random() < p['q_dir']:
                        self.one_time = p['a_line']
                        self.local_submitted = True
                        self.ev('DIR', 'A2', 'allocate', detail='Director 10% / SG000 reserve')
                    else:
                        self.fail('F-k', 'DIR', 'A2', 'reallocation not used for APS')
        if pw == 'PW2' and getattr(self, 'gf_try', None) == t:
            self.gf_try = None
            if self.rng.random() < p['q_gf']:
                self.line_on = True
                self.ev('GF', 'A2', 'approve', detail='General Fund line')
            else:
                self.pw_state['node'] = 2
                self._node('HSIP_repack')
                nxt = next(c for c, y in HSIP_CYCLES.items() if mi(f'{y}-07') > t)
                self.tasks['HSIP']['commit'] = (nxt, 'repack')
        if pw == 'PW3':
            idle = t - max(self.last_submit, self.pw_state['t_node'])
            if node == 0 and idle >= p['th_idle']:
                self.pw_state['node'] = 1
                self._node('structured_negotiation')
                self.enf = max(self.enf, 2)
            elif node == 1 and not funded and t - self.pw_state['t_node'] >= p['th_idle']:
                self.pw_state['node'] = 2
                self._node('lawsuit')
                self.enf = max(self.enf, 3)
        if pw == 'PW4' and node == 0:
            for s in self.sites:
                if (s['state'] == 'Fs' and s['route'] == 'fold' and s.get('parent_nominal') is not None
                        and t > max(s['parent_nominal'], self.t0) + p['th_parent']):
                    ch = self.move(s, 'C')
                    self.ev('A2', 'GF', 'reroute', [s], [ch], 'parent delayed; moved to local queue')
                    self.fail('F-g', 'PARENT', 'A2', 'parent delayed; moved to local queue')
        if pw == 'PW6':
            if getattr(self, 'sg017_try', None) and t in self.sg017_try:
                self.ev('A2', 'SFCTA', 'submit', detail='SG017 allocation request including new APS')
                if self.rng.random() < p['q_sg017_block']:
                    self.fail('F-j', 'SFCTA', 'A2', 'SG017 allocation limited to replacement / used by outages')
                    if node == 0:
                        self.sg017_try = []
                        self.pw_state['node'] = 1
                        self._node('PropL_amendment')
                        self._propl_amendment(t)
                else:
                    self.one_time = getattr(self, 'one_time', 0) + p['a_sg017']
                    self.local_submitted = True
                    self.ev('SFCTA', 'A2', 'approve', detail='SG017 allocation includes new APS (existing poles/conduit)')
            if node == 1 and res == 'pass':
                self.line_on = True
            elif node == 1 and res == 'fail':
                self.fail('F-j', 'SFCTA', 'A2', 'Prop L amendment rejected or deferred')
                self.pw_state['node'] = 2
                self._node('GF_request')
                self.gf_try = t + (18 - t % 12) % 12 or 12
            if node == 2 and getattr(self, 'gf_try', None) == t:
                self.gf_try = None
                if self.rng.random() < p['q_gf']:
                    self.line_on = True
                    self.ev('GF', 'A2', 'approve', detail='General Fund line')
                else:
                    self.pw_state['node'] = 3
                    self._node('HSIP_repack')
                    nxt = next(c for c, y in HSIP_CYCLES.items() if mi(f'{y}-07') > t)
                    self.tasks['HSIP']['commit'] = (nxt, 'repack')
        if pw == 'PW5' and node == 0 and t == self.t0 + 24 and self.rule_installs < p['th_rule']:
            self.pw_state['node'] = 1
            self._node('local_line')
            self.line_on = True

    def _design_rule(self):
        """PW5: push-button / hardware change events at candidate sites carry APS, paid from a
        capped maintenance budget, installed by the in-house crew queue."""
        if not getattr(self, 'design_rule', False):
            return
        p, t = self.p, self.now
        if t % 12 == 6 or not hasattr(self, 'hw_budget'):
            self.hw_budget = p['b_hw']
        h = 1 - math.exp(-p['lam_hw'] / 12)
        for s in self.sites:
            if s['state'] != 'C' or s['blocked'] or self.rng.random() >= h:
                continue
            c = self.unit_cost() + s['adders']
            if c > self.hw_budget:
                self.ev('A3', 'A2', 'skip_rule', [s], detail='hardware change without APS: add-on budget used up')
                continue
            self.hw_budget -= c
            self.cost['SFMTA'] += c
            ch = self.move(s, 'Fi')
            s['via'], s['ready_at'] = 'design_rule', t
            self.fund_months.append(t)
            self.ev('A3', 'A2', 'rule_apply', [s], [ch], 'hardware change carries APS (design rule)')

    def _propl_due(self):
        pp = getattr(self, 'pending_propl', None)
        if pp and pp[0] == self.now:
            del self.pending_propl
            return 'pass' if pp[1] == 'pass' else 'fail'
        return None

    # ------------------------------------------------------------ delivery (design D3.4)
    def _overruns(self):
        p = self.p
        keep = []
        for d, s, plan, payer in self.overrun_checks:
            if d != self.now:
                keep.append((d, s, plan, payer))
                continue
            if s['state'] != 'Fi':
                continue
            actual = min(1_500_000.0, plan * math.exp(p['sigma_over'] * self.rng.standard_normal()))
            cont = p['k_cont'] * plan                 # budgeted contingency (already counted in cost)
            self.cost[payer] += min(max(0.0, actual - plan), cont)
            gap = max(0.0, actual - plan - cont)       # funding gap: any amount beyond contingency
            if gap > 0:
                if self.rng.random() < p['q_topup']:
                    self.cost[payer] += gap
                    self.ev('SFCTA', 'A2', 'topup', [s], detail=f'+${gap:,.0f} beyond contingency')
                else:
                    ch = self.move(s, 'C')
                    self.ev('A2', 'GF', 'overrun_revert', [s], [ch], 'no top-up')
                    self.fail('F-f', 'A2', 'GF', 'overrun, no top-up; site back to candidate')
        self.overrun_checks = keep

    def _deliver(self):
        p, rng, t = self.p, self.rng, self.now
        self._overruns()
        cap = p['k0'] * (1 - p['phi'] * self.strain()) if self.sw['strain'] else p['k0']
        self.bank = min(self.bank + cap, max(cap * 3, 1.0))   # cumulative workload; never caps below one site
        h_in = 1 - math.exp(-p['h_in'] / 12)
        due = [s for s in self.sites if s['state'] == 'Fi' and not s['blocked'] and t >= s.get('ready_at', -1)
               and rng.random() < h_in]
        for s in due:
            if self.bank < 1:
                break
            self.bank -= 1
            ch = self.move(s, 'I')
            if s['via'] == 'design_rule':
                self.rule_installs += 1
            self.ev('A3', 'A2', 'install', [s], [ch], 'in-house')
        h_fs = 1 - math.exp(-p['h_fs'] / 12)
        for s in self.sites:
            if s['state'] != 'Fs' or not s['hazard_fs']:
                continue
            if s.get('parent_ready') is not None and t < s['parent_ready']:
                continue
            if rng.random() < h_fs:
                ch = self.move(s, 'I')
                if s['via'] == 'design_rule':
                    self.rule_installs += 1
                self.ev('PARENT', 'A2', 'install', [s], [ch], 'with signal project')
        if self.history:
            # exogenous moves into signal projects (training-period Gamma means)
            for s in self.sites:
                if s['state'] == 'C' and rng.random() < 1 - math.exp(-0.0127 / 12):
                    ch = self.move(s, 'Fs')
                    self.ev('PARENT', 'A2', 'scope_add', [s], [ch], 'absorbed by a signal project')
                elif s['state'] == 'N' and rng.random() < 1 - math.exp(-0.033 / 12):
                    ch = self.move(s, 'Fs')
                    self.ev('PARENT', 'A2', 'scope_add', [s], [ch], 'absorbed by a signal project')

    # ------------------------------------------------------------ run
    def stocks(self):
        c = {'C': 0, 'N': 0, 'Fi': 0, 'Fs': 0, 'Fh': 0}
        for s in self.sites:
            if s['state'] in c:
                c[s['state']] += 1
        c['I_cum'] = self.i_base + sum(1 for s in self.sites if s['state'] == 'I')
        return c

    def run(self):
        months, series = [], {k: [] for k in ('C', 'N', 'Fi', 'Fs', 'Fh', 'I_cum')}
        snaps = {}
        for k in range(self.T):
            self.now = self.t0 + k
            self.step()
            st = self.stocks()
            months.append(ms(self.now))
            for key in series:
                series[key].append(st[key])
            snaps[ms(self.now)] = st
        return self._summary(months, series, snaps)

    def _summary(self, months, series, snaps):
        t5, t10 = self.t0 + 60, self.t0 + 120
        inst = [s for s in self.sites if s['installed'] is not None and s['installed'] >= self.t0]   # includes month 1
        hp = [s for s in self.sites if s['rank'] == 'high']
        rec = None
        if self.fail_months:
            f0 = min(self.fail_months)
            nxt = [m for m in self.fund_months if m > f0]
            rec = (nxt[0] - f0) if nxt else None
        out = {
            'meta': {'status': 'dev', 'pathway': self.pw, 'mechanism': self.mech, 'start': ms(self.t0),
                     'horizon_months': self.T},
            'months': months, 'stocks': series,
            'path_nodes_reached': self.nodes,
            'initial_states': self.initial_states,
            'summary': {
                'money_flows_5y': int(any(self.t0 <= m < t5 for m in self.fund_months)),
                'installed_5y': sum(1 for s in inst if s['installed'] < t5),
                'high_priority_5y': (sum(1 for s in hp if s['installed'] is not None and self.t0 <= s['installed'] < t5) / len(hp)) if hp else None,
                'coverage_10y': sum(1 for s in inst if s['installed'] < t10),
                'recovery_time': rec,
                'n_failures': len(self.fail_months),
                'cost_by_actor': {k: round(v, 0) for k, v in self.cost.items()},
            },
        }
        if self.history:
            out['snapshot_stocks'] = {d: snaps.get(d[:7]) for d in self.inputs['history']['snapshots']}
        if self.emit:
            out['events'] = self.events
        return out


def run(params, pathway, mechanism, seed, start='2026-07', horizon_months=120, emit_events=False, inputs=None):
    if inputs is None:
        raise ValueError('pass inputs (dict from inputs.json; use load_inputs(path) in CPython)')
    return Sim(params, pathway, mechanism, int(seed), start, int(horizon_months), bool(emit_events), inputs).run()
