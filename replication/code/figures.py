"""Draw the three report figures from saved result files (no simulation).

    python -I figures.py [--out DIR]     # default: ../results/figures
Inputs: results/e3-pathways/posthoc.json (run posthoc.py first), results/e3-pathways/runs.csv.gz,
        results/e4-sensitivity/sobol.json.  Labels are English (appendix use).
"""
import argparse, csv, gzip, json, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
RES = HERE.parent / 'results'
BLUE, ORANGE = '#2a78d6', '#eb6834'
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
NAMES = {'PW1': 'PW1 HSIP first', 'PW2': 'PW2 Local line first', 'PW3': 'PW3 Accountability first',
         'PW4': 'PW4 Per-intersection routes', 'PW5': 'PW5 Design rule', 'PW6': 'PW6 Use SG017 line'}
LABEL = 'Uncalibrated scenario projections, not forecasts'


def style(ax):
    ax.set_facecolor(SURF)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(INK2)
    ax.tick_params(colors=INK2, length=0)
    ax.grid(axis='x', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def fig_robustness(out):
    """Main table: parameter sets with no standing local line at start (sw_line = 0, today's status quo)."""
    t = json.loads((RES / 'e3-pathways' / 'posthoc.json').read_text())['by_sw_line']['line0_status_quo']
    names = dict(NAMES)
    vf = RES / 'e3-variant' / 'summary.json'
    if vf.exists():                       # approval variant: PW4/PW5 line must pass PW2's approval chain
        for k, v in json.loads(vf.read_text())['table'].items():
            pw, ctl = k.split('|')
            t[f'{pw}a|{ctl}'] = {'share_better': v['share_better_than_PW0']}
            names[f'{pw}a'] = NAMES[pw] + ' + approval'
    order = sorted(names, key=lambda pw: -sum(t[f'{pw}|positive']['share_better']))
    fig, ax = plt.subplots(figsize=(7.2, 4.6), facecolor=SURF)
    style(ax)
    for i, pw in enumerate(order):
        for ctl, col, dy in (('positive', BLUE, -0.14), ('zero_direct', ORANGE, 0.14)):
            lo, hi = (100 * x for x in t[f'{pw}|{ctl}']['share_better'])
            ax.plot([lo, hi], [i + dy] * 2, color=col, linewidth=2, solid_capstyle='round')
            ax.plot([lo, hi], [i + dy] * 2, 'o', color=col, markersize=8, markeredgecolor=SURF, markeredgewidth=2)
    ax.set_yticks(range(len(order)), [names[p] for p in order], color=INK)
    ax.invert_yaxis()
    ax.set_xlim(30, 100)
    ax.set_xlabel('Share of parameter sets with more intersections covered\nat 10 years than under the status quo (%)', color=INK2, fontsize=8.5)
    ax.plot([], [], 'o-', color=BLUE, label='Direct start effects as sampled')
    ax.plot([], [], 'o-', color=ORANGE, label='Direct start effects set to zero')
    ax.legend(loc='upper left', frameon=False, fontsize=8, labelcolor=INK2)
    fig.suptitle('No standing local APS line at start (as today); ranges span six mechanism settings.\n'
                 'As designed, PW4 and PW5 get a local line with no approval step;\n'
                 '"+ approval" rows put that line through PW2\'s approval chain.\n' + LABEL,
                 fontsize=7.5, color=INK2, x=0.02, ha='left')
    fig.tight_layout()
    fig.savefig(out / 'fig1-pathway-robustness.png', dpi=200)
    plt.close(fig)


def fig_pw3_line(out):
    rows = list(csv.DictReader(gzip.open(RES / 'e3-pathways' / 'runs.csv.gz', 'rt')))
    rows = [r for r in rows if r['control'] == 'positive']
    pw0 = {(r['mechanism'], r['set']): float(r['coverage_10y']) for r in rows if r['pathway'] == 'PW0'}
    fig, ax = plt.subplots(figsize=(7.2, 3.3), facecolor=SURF)
    style(ax)
    pws = ['PW3', 'PW2']
    for j, (line, col) in enumerate(((0, BLUE), (1, ORANGE))):
        for i, pw in enumerate(pws):
            s = [r for r in rows if r['pathway'] == pw and int(float(r['sw_line'])) == line]
            v = 100 * st.mean(float(r['coverage_10y']) > pw0[(r['mechanism'], r['set'])] for r in s)
            y = i + (j - 0.5) * 0.36
            ax.barh(y, v, height=0.32, color=col, edgecolor=SURF, linewidth=2)
            ax.text(v + 1, y, f'{v:.0f}%', va='center', fontsize=8, color=INK)
    ax.set_yticks(range(len(pws)), [NAMES[p] for p in pws], color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel('Share of parameter sets better than status quo at 10 years (%)', color=INK2, fontsize=8.5)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label='No standing local APS line'),
                       Patch(color=ORANGE, label='Standing local APS line already exists')],
              loc='upper center', bbox_to_anchor=(0.5, -0.28), ncol=2, frameon=False, fontsize=8, labelcolor=INK2)
    ax.set_title('Pooled over six mechanism settings\n' + LABEL, fontsize=7.5, color=INK2, loc='left')
    fig.tight_layout()
    fig.savefig(out / 'fig2-accountability-by-standing-line.png', dpi=200)
    plt.close(fig)


def fig_sobol(out):
    d = json.loads((RES / 'e4-sensitivity' / 'sobol.json').read_text())
    cells = [k for k in d['cells'] if k.endswith('|default')]
    st_ = {n: st.mean(d['cells'][k]['N512']['ST'][n] for k in cells) for n in d['inputs']}
    cf = {n: st.mean(d['cells'][k]['N512']['ST_conf'][n] for k in cells) for n in d['inputs']}
    lab = {'aps_share': 'APS share of local line', 'q_pipe': 'Conduit work needed (costly sites)',
           'sw_line': 'Standing local line exists', 'q_ramp': 'Curb-ramp work needed (costly sites)',
           'a_line': 'Local line size ($/yr)', 'lam_arr': 'New requests per year',
           'h_fs': 'Install pace via signal projects', 'u0': 'Button-level unit cost',
           'fs5_parent': 'Parent project done in 5 yrs', 'pi_scope': 'Corridor design picks up APS',
           'q_topup': 'Overrun top-up approved', 'k_cont': 'Contingency share'}
    order = sorted(st_, key=lambda n: -st_[n])
    fig, ax = plt.subplots(figsize=(7.2, 3.9), facecolor=SURF)
    style(ax)
    ax.barh(range(len(order)), [st_[n] for n in order], height=0.6, color=BLUE, edgecolor=SURF, linewidth=2)
    ax.errorbar([st_[n] for n in order], range(len(order)), xerr=[cf[n] for n in order], fmt='none',
                ecolor=INK2, elinewidth=1, capsize=0)
    for i, n in enumerate(order[:5]):
        ax.text(st_[n] + cf[n] + 0.01, i, f'{st_[n]:.2f}', va='center', fontsize=8, color=INK)
    ax.set_yticks(range(len(order)), [lab[n] for n in order], color=INK, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel('Total-effect Sobol index on intersections covered at 10 years\n(mean of 14 cells, N = 512; whiskers = mean 95% interval)',
                  color=INK2, fontsize=8)
    ax.set_title('Conditional: other 86 parameters fixed at defaults\n' + LABEL, fontsize=7.5, color=INK2, loc='left')
    fig.tight_layout()
    fig.savefig(out / 'fig3-sobol-total-effects.png', dpi=200)
    plt.close(fig)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(RES / 'figures'))
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    fig_robustness(out); fig_pw3_line(out); fig_sobol(out)
    print('figures written to', out)
