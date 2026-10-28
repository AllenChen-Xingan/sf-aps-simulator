"""Replay check: initial_states + event state_changes must reproduce stocks every month.
Run: python -I code/replay_check.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import model, params

inp = model.load_inputs(Path(__file__).resolve().parent / 'data' / 'inputs.json')
rng_seeds = range(5)
bad = 0
for start, horizon in (('2026-07', 120), ('2022-07', 48)):
    for pw in model.PATHWAYS:
        for mech in model.MECHANISMS:
            for seed in rng_seeds:
                r = model.run(params.default_params(), pw, mech, seed, start=start, horizon_months=horizon,
                              emit_events=True, inputs=inp)
                st = dict(r['initial_states'])
                by_month = {}
                for e in r['events']:
                    by_month.setdefault(e['month'], []).append(e)
                base = r['stocks']['I_cum'][0] - sum(1 for v in st.values() if v == 'I')
                for i, m in enumerate(r['months']):
                    for e in by_month.get(m, []):
                        for c in e.get('state_changes', []):
                            st[c['key']] = c['to']
                    cnt = {k: sum(1 for v in st.values() if v == k) for k in ('C', 'N', 'Fi', 'Fs', 'Fh', 'I')}
                    want = {k: r['stocks'][k][i] for k in ('C', 'N', 'Fi', 'Fs', 'Fh')}
                    got = {k: cnt[k] for k in want}
                    if got != want:
                        bad += 1
                        print('MISMATCH', start, pw, mech, seed, m, got, want)
                        break
print('replay mismatches:', bad)

# Reconciliation: new installs counted in the summary == growth of I_cum over the run
rec_bad = 0
for pw in model.PATHWAYS:
    for mech in ('M-A', 'M-D'):
        for seed in range(10):
            r = model.run(params.default_params(), pw, mech, seed, horizon_months=120, inputs=inp)
            pre = sum(1 for v in r['initial_states'].values() if v == 'I')
            grow = r['stocks']['I_cum'][-1] - pre
            if grow != r['summary']['coverage_10y']:
                rec_bad += 1
                print('RECON', pw, mech, seed, grow, r['summary']['coverage_10y'])
print('install reconciliation mismatches:', rec_bad)
bad += rec_bad

# PW4: a delayed fold-in parent must trigger rerouting (Ellis/Powell's parent was due 2026-06)
reroutes = 0
for seed in range(20):
    pr = dict(params.default_params(), pi_scope=1.0, h_fs=0.08, th_parent=6.0)
    r = model.run(pr, 'PW4', 'M-A', seed, inputs=inp, emit_events=True)
    reroutes += sum(1 for e in r['events'] if e['action'] == 'reroute')
print('PW4 reroute events in 20 runs:', reroutes)

# $10M cap: with other SF requests near the cap, applications must still fit (model asserts it)
import numpy as np
for i, pset in enumerate(params.sample(200, np.random.default_rng(11))):
    pset.update(r_other=float(np.random.default_rng(i).uniform(5e6, 9.9e6)), k_cont=0.15)
    for pw in ('PW1', 'PW2', 'PW4', 'PW6'):
        model.run(pset, pw, 'M-A', i, inputs=inp)
print('cap test: 800 runs with r_other 5-9.9M, no application over the remaining cap')

# Dilution: a low-crash site must not be added when it would pull the bundle below 5.0
sim = model.Sim(dict(params.default_params(), k_cont=0.15, r_other=0.0), 'PW1', 'M-A', 1, '2026-07', 120, False, inp)
sim.now = sim.t0
hi = max((x for x in sim.sites if x['state'] == 'C' and x['crashes']), key=lambda x: x['crashes']['pb_KA_w5'])
lo = min((x for x in sim.sites if x['state'] == 'C' and x['crashes'] and x is not hi), key=lambda x: sum(x['crashes'].values()))
for x in sim.sites:
    x['in_app'] = x not in (hi, lo)
for x in (hi, lo):
    x['c12'], x['state'] = True, 'C'
chosen, bcr, cost = sim._build_app('repack', 'C14', 'C', 10_000_000)
print('dilution test: kept', len(chosen), 'site(s), BCR', round(bcr, 2), '(low-crash site excluded)' if lo not in chosen else '(low-crash site kept)')
bad += 0 if (lo not in chosen or bcr >= 5.0) else 1

# Red-flag boundary: a flag cleared in the review month counts as cleared before the 11-30 review;
# a flag cleared the month after does not
sim = model.Sim(dict(params.default_params(), rho_flag=0.0), 'PW0', 'M-A', 1, '2026-07', 120, False, inp)
sim.now = model.mi('2026-11')
sim.projects = [{'flag_from': model.mi('2026-01'), 'flag_to': model.mi('2026-11'), 'con_at': 0, 'cs': 0}]
before = sim._agency_flagged()
sim.projects = [{'flag_from': model.mi('2026-01'), 'flag_to': model.mi('2026-12'), 'con_at': 0, 'cs': 0}]
after = sim._agency_flagged()
print('red-flag boundary: cleared in review month ->', 'eligible' if not before else 'INELIGIBLE', '; cleared next month ->', 'ineligible' if after else 'ELIGIBLE')
bad += 0 if (not before and after) else 1

# f_aff with fixed inputs: SI02 only -> exactly half; SI02 + SI22PB -> pedestrian part not halved
def ben(f, lpi):
    sm = model.Sim(dict(params.default_params(), f_aff=f, l_rule=0, y_win=5), 'PW1', 'M-A', 1, '2026-07', 120, False, inp)
    sm.now = sm.t0
    x = next(x for x in sm.sites if x['state'] == 'C' and x['crashes'])
    x['crashes'] = {k: 0 for k in x['crashes']}
    x['crashes'].update(pb_KA_w5=1, pb_B_w5=2, nonpb_C_w5=3)
    x['c12'], x['cbp'], x['clpi'], x['ccd'] = True, False, lpi, False
    return sm._site_bcr_parts(x, 'repack', 'C13')[0]
h, f1 = ben(0.5, False), ben(1.0, False)
m_h, m_f = ben(0.5, True), ben(1.0, True)
print(f'f_aff test: SI02 only {h:,.2f} vs half of {f1:,.2f}; SI02+LPI {m_h:,.0f} vs {m_f:,.0f}')
bad += 0 if abs(h - f1 / 2) < 1e-6 else 1
bad += 0 if m_h > m_f / 2 + 1 else 1

# LRSP: an expired plan blocks review until an update finishes; a successful update restores eligibility
sm = model.Sim(dict(params.default_params(), lrsp_until=-6.0, t_lrsp=12.0, q_lrsp=1.0, rho_flag=0.0), 'PW0', 'M-A', 1, '2026-07', 120, False, inp)
sm.now = model.mi('2026-11'); a1 = sm._lrsp_valid()
sm.now = model.mi('2027-04'); a2 = sm._lrsp_valid()
print('LRSP test: expired at 2026-11 ->', 'invalid' if not a1 else 'VALID', '; after update 2027-04 ->', 'valid' if a2 else 'INVALID')
bad += 0 if (not a1 and a2) else 1

# Local window boundary: preparation finishing in the deadline month is submitted; one month later is missed
sm = model.Sim(dict(params.default_params(), d_prep=3.0), 'PW0', 'M-A', 1, '2026-07', 120, False, inp)
tk = sm.tasks['LOCAL']
sm.now = model.mi('2027-03'); tk.update(state='PREPARING', ready=model.mi('2027-06'), started=sm.now)
sm.now = model.mi('2027-06'); sm._task_step('LOCAL'); ok_on = getattr(sm, 'local_submitted', False)
sm = model.Sim(dict(params.default_params(), d_prep=3.0), 'PW0', 'M-A', 1, '2026-07', 120, False, inp)
tk = sm.tasks['LOCAL']
sm.now = model.mi('2027-04'); tk.update(state='PREPARING', ready=model.mi('2027-07'), started=sm.now)
sm.now = model.mi('2027-06'); sm._task_step('LOCAL'); ok_late = getattr(sm, 'local_submitted', False)
print('local deadline test: ready in June ->', 'submitted' if ok_on else 'MISSED', '; ready in July ->', 'missed' if not ok_late else 'SUBMITTED')
bad += 0 if (ok_on and not ok_late) else 1

# Set-aside: APS extra work never above 20% of the actual project total (asserted in the model)
for i, pset in enumerate(params.sample(100, np.random.default_rng(21))):
    model.run(pset, 'PW1', 'M-A', i, inputs=inp)
print('set-aside test: 100 runs, APS <= 20% of the summed project total everywhere')

# Fractional capacity: 0.5/month with heavy strain must still install over 10 years
low = dict(params.default_params(), k0=0.5, phi=0.9, strain_ramp=1.0, strain_end=24.0, sw_line=1, a_line=2000000, aps_share=0.5)
inst = sum(model.run(low, 'PW2', 'M-B1', s_, inputs=inp)['summary']['coverage_10y'] for s_ in range(10))
print('low-capacity installs over 10 runs:', inst)
bad += 0 if inst > 0 else 1
bad += 0 if reroutes > 0 else 1

# Termination test: no TERMINATED project may deliver (model.move raises AssertionError if it does)
import numpy as np
ps = params.sample(150, np.random.default_rng(3))
terms = 0
for i, pset in enumerate(ps):
    for pw in model.PATHWAYS:
        r = model.run(pset, pw, 'M-D', i, inputs=inp, emit_events=True)
        terms += sum(1 for e in r['events'] if e['action'] in ('overrun_revert', 'return_funds', 'partner_delay'))
print('termination test: 0 deliveries from terminated projects;', terms, 'terminations exercised')
sys.exit(1 if bad else 0)
