"""Parameter table (design 02 section D10), machine-readable.

Standard library only. `param_schema()` is the single source for the batch
sampler and the web control panel. Status: dev, priors not calibrated.
kind: uniform (low..high) | switch (0/1) | discrete (choices) | level (fixed by
mechanism/pathway, not sampled). phase: fit | projection | all.
"""

ALL = ['M-A', 'M-B1', 'M-B2', 'M-C1', 'M-C2', 'M-D']
MECHS = list(ALL)

_S = [
    # name, label_en, unit, kind, low, high, default, applies_to, phase
    ('oversight', 'Actual oversight strength', '0-1', 'uniform', 0.05, 0.6, 0.3, ALL, 'all'),
    ('b0', 'Baseline start propensity (logit per month)', 'logit', 'uniform', -6.9, -2.9, -4.9, ALL, 'all'),
    ('b_own', 'Effect of a named owner', 'logit', 'uniform', 0.0, 3.0, 1.5, ALL, 'all'),
    ('b_spec', 'Effect of a written deadline', 'logit', 'uniform', 0.0, 2.0, 1.0, ALL, 'all'),
    ('b_ov', 'Effect of oversight', 'logit/unit', 'uniform', 0.0, 2.0, 1.0, ALL, 'all'),
    ('b_pr', 'Effect of advocacy pressure', 'logit/unit', 'uniform', 0.0, 2.0, 1.0, ALL, 'all'),
    ('b_enf', 'Effect of external enforcement', 'logit/level', 'uniform', 0.0, 3.0, 1.5, ALL, 'all'),
    ('lam_press', 'Advocacy pressure events', 'per year', 'uniform', 0.0, 0.5, 0.25, ALL, 'all'),
    ('k_decay', 'Pressure decay time', 'months', 'uniform', 1.0, 12.0, 6.0, ALL, 'all'),
    ('p_deflect', 'Buck-passing probability', 'probability', 'uniform', 0.5, 0.95, 0.75, ['M-A', 'M-D'], 'all'),
    ('r_back', 'Months before a deflected task can restart', 'months', 'uniform', 1.0, 12.0, 6.0, ['M-A', 'M-D'], 'all'),
    ('d_prep', 'Months to prepare an application', 'months', 'uniform', 1.0, 6.0, 3.0, ALL, 'all'),
    ('m_b', 'Staff strain dampens starts', 'logit/unit', 'uniform', 0.0, 3.0, 1.5, ['M-B1', 'M-B2', 'M-D'], 'all'),
    ('strain_ramp', 'Months for strain to reach full', 'months', 'uniform', 1.0, 12.0, 6.0, ['M-B1', 'M-B2', 'M-D'], 'all'),
    ('strain_end', 'Hiring freeze ends (months after 2026-12)', 'months', 'uniform', 0.0, 24.0, 12.0, ['M-B1', 'M-B2', 'M-D'], 'all'),
    ('phi', 'Strain reduces crew capacity', 'fraction', 'uniform', 0.0, 0.9, 0.45, ['M-B1', 'M-B2', 'M-D'], 'all'),
    ('k0', 'In-house crew capacity', 'sites per month', 'uniform', 0.5, 3.0, 1.5, ALL, 'all'),
    ('h_in', 'Funded in-house site install rate', 'per year', 'uniform', 0.59, 1.41, 0.94, ALL, 'all'),
    ('h_fs', 'Signal-project site install rate', 'per year', 'uniform', 0.08, 0.31, 0.16, ALL, 'all'),
    ('m_c', 'Cost pressure dampens starts', 'logit/unit', 'uniform', 0.0, 3.0, 1.5, ['M-C1', 'M-D'], 'all'),
    ('g_cost', 'Base unit cost growth', 'per year', 'uniform', 0.0, 0.15, 0.08, ['M-C1', 'M-D'], 'all'),
    ('tau', 'Share of candidate sites technically blocked', 'fraction', 'uniform', 0.0, 0.8, 0.4, ['M-C2', 'M-D'], 'all'),
    ('u0', 'Base APS cost per site', 'USD', 'uniform', 22000, 50000, 36000, ALL, 'all'),
    ('q_pipe', 'Chance conduit work is needed (+$200k)', 'probability', 'uniform', 0.0, 1.0, 0.3, ALL, 'all'),
    ('q_ramp', 'Chance new curb ramps are needed (+$200k)', 'probability', 'uniform', 0.0, 1.0, 0.3, ALL, 'all'),
    ('a_local', 'Local money for APS per year (status quo)', 'USD/year', 'uniform', 0, 570000, 250000, ALL, 'all'),
    ('a_line', 'Dedicated line size when on', 'USD/year', 'uniform', 500000, 2000000, 1000000, ALL, 'projection'),
    ('aps_share', 'APS share of a standing line', 'fraction', 'uniform', 0.0, 0.5, 0.25, ALL, 'projection'),
    ('y_win', 'Crash window', 'years', 'discrete', 3, 5, 5, ALL, 'projection'),
    ('l_rule', 'Service life rule (0 shortest, 1 weighted)', 'code', 'discrete', 0, 1, 0, ALL, 'projection'),
    ('c_final', 'HSIP final BCR cutoff', 'BCR', 'uniform', 3.5, 18.0, 8.0, ALL, 'projection'),
    ('r_other', 'Other SF HSIP requests using the $10M cap', 'USD', 'uniform', 0, 10000000, 4000000, ALL, 'projection'),
    ('rho_flag', 'Other SF HSIP project red-flagged per cycle', 'probability', 'uniform', 0.0, 0.3, 0.1, ALL, 'projection'),
    ('q_fail', 'Residual random failure after passing cutoff', 'probability', 'uniform', 0.0, 0.2, 0.0, ALL, 'projection'),
    ('p_sa', 'SF wins a pedestrian-crossing set-aside', 'probability', 'uniform', 0.0, 0.9, 0.4, ALL, 'projection'),
    ('s_12in_C', 'Share of candidate (C) sites still with 8-inch heads', 'fraction', 'uniform', 0.25, 0.7, 0.47, ALL, 'projection'),
    ('s_bp', 'Share of sites that can take backplates', 'fraction', 'uniform', 0.85, 1.0, 0.92, ALL, 'projection'),
    ('s_mast', 'Share of full-upgrade sites now pedestal-mounted', 'fraction', 'uniform', 0.0, 1.0, 0.5, ALL, 'projection'),
    ('s_lpi', 'Share of sites where a new LPI is possible', 'fraction', 'uniform', 0.0, 0.5, 0.2, ALL, 'projection'),
    ('c_12in', 'Cost of 12-inch head upgrade', 'USD/site', 'uniform', 8000, 20000, 14000, ALL, 'projection'),
    ('c_bp', 'Cost of backplates', 'USD/site', 'uniform', 2000, 8000, 5000, ALL, 'projection'),
    ('c_lpi', 'Cost of a new LPI', 'USD/site', 'uniform', 1000, 5000, 3000, ALL, 'projection'),
    ('c_full', 'Full signal upgrade cost (incl. APS hardware)', 'USD/site', 'uniform', 200000, 600000, 400000, ALL, 'projection'),
    ('sw_pe', 'HSIP pays for design (PE milestone applies)', 'switch', 'switch', 0, 1, 0, ALL, 'projection'),
    ('t_pe', 'Months to design E-76', 'months', 'uniform', 3.0, 15.0, 8.0, ALL, 'projection'),
    ('t_pif', 'Months for public interest finding', 'months', 'uniform', 1.0, 12.0, 4.0, ALL, 'projection'),
    ('q_pif_deny', 'PIF denied (switch to contractor)', 'probability', 'uniform', 0.0, 0.3, 0.1, ALL, 'projection'),
    ('sw_consult', 'Consultant design (42-month CON limit)', 'switch', 'switch', 0, 1, 0, ALL, 'projection'),
    ('t_con_med', 'Median months, cycle start to construction E-76 (SF award-based data shifted by t_lag)', 'months', 'uniform', 8.0, 16.0, 12.0, ALL, 'projection'),
    ('t_lag', 'Months from award notice to cycle start', 'months', 'uniform', 8.0, 10.0, 9.0, ALL, 'projection'),
    ('d_split', 'Extra months per additional application instance', 'months', 'uniform', 0.0, 2.0, 1.0, ALL, 'projection'),
    ('t_des', 'Months from local award to design complete (overrun found)', 'months', 'uniform', 2.0, 6.0, 4.0, ALL, 'all'),
    ('t_dsg', 'Months from design start (PE E-76 or cycle start) to design complete', 'months', 'uniform', 4.0, 14.0, 8.0, ALL, 'projection'),
    ('t_pause', 'Months paused when a contracting cost gap is not funded', 'months', 'uniform', 3.0, 12.0, 6.0, ALL, 'projection'),
    ('k_cont', 'Budgeted contingency share of planned cost', 'fraction', 'uniform', 0.05, 0.15, 0.1, ALL, 'all'),
    ('t_ext', 'Length of the one allowed 5-year extension', 'months', 'uniform', 6.0, 24.0, 12.0, ALL, 'projection'),
    ('lam_hw', 'Push-button / signal-hardware change events per candidate site', 'per year', 'uniform', 0.01, 0.08, 0.04, ALL, 'projection'),
    ('b_hw', 'Maintenance budget for APS add-ons under the design rule', 'USD/year', 'uniform', 0, 300000, 150000, ALL, 'projection'),
    ('q_sg017_block', 'SG017 allocation excludes new APS', 'probability', 'uniform', 0.2, 0.9, 0.55, ALL, 'projection'),
    ('a_sg017', 'SG017 money usable for APS per year (FY27, FY28)', 'USD/year', 'uniform', 0, 250000, 125000, ALL, 'projection'),
    ('s_cd', 'Share of unknown sites missing countdown heads', 'fraction', 'uniform', 0.0, 0.2, 0.05, ALL, 'projection'),
    ('c_cd', 'Cost of new countdown heads', 'USD/site', 'uniform', 10000, 40000, 25000, ALL, 'projection'),
    ('sigma_over', 'Cost overrun log-scale', 'log', 'uniform', 0.2, 0.8, 0.5, ALL, 'all'),
    ('lam_quiet', 'Advocacy quiet spells start', 'per year', 'uniform', 0.05, 0.3, 0.1, ALL, 'all'),
    ('t_fix', 'Months to clear a red flag', 'months', 'uniform', 1.0, 12.0, 4.0, ALL, 'projection'),
    ('t_contract', 'Months to procure a contractor', 'months', 'uniform', 6.0, 24.0, 12.0, ALL, 'projection'),
    ('k_contract', 'Contractor cost markup', 'multiple', 'uniform', 1.1, 1.6, 1.3, ALL, 'projection'),
    ('q_topup', 'Overrun gets a top-up allocation', 'probability', 'uniform', 0.0, 0.7, 0.35, ALL, 'projection'),
    ('t_partner', 'Partner project delay', 'months', 'uniform', 0.0, 24.0, 6.0, ALL, 'projection'),
    ('q_partner_cancel', 'Partner project cancelled', 'probability', 'uniform', 0.0, 0.3, 0.1, ALL, 'projection'),
    ('lam_quit', 'Owner leaves per year', 'per year', 'uniform', 0.05, 0.3, 0.15, ALL, 'all'),
    ('t_vac', 'Months the post stays vacant', 'months', 'uniform', 3.0, 18.0, 8.0, ALL, 'all'),
    ('q_drop', 'Preparation dropped when owner leaves', 'probability', 'uniform', 0.0, 1.0, 0.5, ALL, 'all'),
    ('q_veto', 'SFCTA board rejects Prop L amendment', 'probability', 'uniform', 0.0, 0.5, 0.2, ALL, 'projection'),
    ('t_defer', 'Months a Prop L amendment is deferred', 'months', 'uniform', 1.0, 12.0, 4.0, ALL, 'projection'),
    ('q_gf', 'General Fund request is included in budget', 'probability', 'uniform', 0.0, 0.5, 0.2, ALL, 'projection'),
    ('q_dir', 'Director reallocation used for APS', 'probability', 'uniform', 0.0, 0.8, 0.3, ALL, 'projection'),
    ('t_quiet', 'Months advocacy goes quiet', 'months', 'uniform', 6.0, 36.0, 18.0, ALL, 'all'),
    ('th_defer', 'Signpost: deferral months before switching', 'months', 'uniform', 3.0, 12.0, 6.0, ALL, 'projection'),
    ('th_idle', 'Signpost: months with no application before escalating', 'months', 'uniform', 6.0, 24.0, 12.0, ALL, 'projection'),
    ('th_parent', 'Signpost: parent project delay before switching', 'months', 'uniform', 6.0, 24.0, 12.0, ALL, 'projection'),
    ('th_rule', 'Signpost: installs via design rule in 2 years', 'sites', 'uniform', 2.0, 10.0, 5.0, ALL, 'projection'),
    ('t_build', 'Months from construction E-76 to install', 'months', 'uniform', 3.0, 24.0, 10.0, ALL, 'projection'),
    ('e_ext', 'Extension granted at 5 years', 'probability', 'uniform', 0.0, 1.0, 0.5, ALL, 'projection'),
    ('t_parent', 'Parent project delay', 'months', 'uniform', 0.0, 24.0, 8.0, ALL, 'all'),
    ('pi_scope', 'Likely/unverified fold-in still in scope', 'probability', 'uniform', 0.0, 1.0, 0.5, ALL, 'projection'),
    ('done3_real', 'Three finished-parent sites truly undelivered', 'switch', 'switch', 0, 1, 1, ALL, 'all'),
    ('fs5_parent', 'Five Fs sites without a found parent do have one', 'switch', 'switch', 0, 1, 1, ALL, 'projection'),
    ('lam_arr', 'New requests', 'per year', 'uniform', 6.0, 17.0, 10.0, ALL, 'projection'),
    ('eps_enf', 'External enforcement steps up', 'per year', 'uniform', 0.0, 0.1, 0.03, ALL, 'all'),
    ('sw_si02', 'Signal-hardware carrier accepted', 'switch', 'switch', 0, 1, 1, ALL, 'projection'),
    ('sw_line', 'Dedicated local line on', 'switch', 'switch', 0, 1, 0, ALL, 'projection'),
]

FIELDS = ('name', 'label_en', 'unit', 'kind', 'low', 'high', 'default', 'applies_to', 'phase')


def param_schema():
    return [dict(zip(FIELDS, row)) for row in _S]


def default_params():
    return {row[0]: row[6] for row in _S}


def sample(n, rng, width=1.0, names=None):
    """Latin hypercube over the uniform rows; switches/discrete uniform over choices.
    width: 1.0 base prior, 0.5 narrowed, 2.0 widened (clipped to the legal range of
    probabilities/fractions)."""
    rows = [r for r in _S if names is None or r[0] in names]
    out = [dict(default_params()) for _ in range(n)]
    for (name, _, unit, kind, lo, hi, *_rest) in rows:
        if kind == 'uniform':
            mid, half = (lo + hi) / 2, (hi - lo) / 2 * width
            a, b = mid - half, mid + half
            if unit in ('probability', 'fraction', '0-1'):
                a, b = max(a, 0.0), min(b, 1.0)
            perm = rng.permutation(n)
            u = (perm + rng.random(n)) / n
            vals = a + u * (b - a)
        else:
            vals = rng.choice([lo, hi], size=n)
        for i in range(n):
            out[i][name] = float(vals[i]) if kind == 'uniform' else int(vals[i])
    return out
