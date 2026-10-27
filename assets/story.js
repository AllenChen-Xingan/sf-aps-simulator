// Who is who, who relates to whom, and how each model event reads in plain English.
// Content follows the model's actor and relationship description (ABM design, actors and venues);
// no results are stated here.

export const NODES = {
  C3: { label: 'Residents who ask', x: 85, y: 70, kind: 'actor' },
  C2: { label: 'Advocates', x: 85, y: 200, kind: 'actor' },
  D1: { label: 'Enforcement', x: 85, y: 330, kind: 'actor' },
  A1: { label: 'SFMTA APS engineers', x: 290, y: 70, kind: 'actor' },
  MDC: { label: "Mayor's Disability Council", x: 290, y: 200, kind: 'venue' },
  A2: { label: 'SFMTA funding staff', x: 480, y: 200, kind: 'actor' },
  DIR: { label: 'SFMTA Director', x: 480, y: 330, kind: 'actor' },
  HSIP: { label: 'HSIP (federal)', x: 680, y: 50, kind: 'venue' },
  PROPL: { label: 'Prop L (county)', x: 680, y: 150, kind: 'venue' },
  GF: { label: 'General Fund', x: 680, y: 250, kind: 'venue' },
  SS4A: { label: 'SS4A (federal)', x: 680, y: 340, kind: 'venue' },
  CT: { label: 'Caltrans', x: 885, y: 50, kind: 'actor' },
  SFCTA: { label: 'SFCTA Board', x: 885, y: 150, kind: 'actor' },
  A3: { label: 'Signal Shop crews', x: 885, y: 260, kind: 'actor' },
  PARENT: { label: 'Signal projects', x: 885, y: 350, kind: 'venue' },
};
export const ALIAS = { LOCAL: 'GF' };
export const nodeName = id => (NODES[ALIAS[id] || id] || { label: id }).label;

// Cards: who · what it does in the model · what it holds · who it relates to.
export const CARDS = {
  C3: { who: 'Blind and low-vision residents who ask SFMTA for an APS at a specific intersection.',
    does: 'New requests arrive at about the historical pace. Each one joins the request list.',
    holds: 'Information: where the need is.', rel: ['request'] },
  A1: { who: 'The SFMTA engineers who run the APS program.',
    does: 'Score and sort each request: can it be done with the existing pole and wiring, or does the signal need a full upgrade? They follow rules; they do not decide whether to apply for money.',
    holds: 'Information: the scored request list.', rel: ['request', 'list'] },
  A2: { who: 'SFMTA staff who handle the capital budget and grant applications.',
    does: 'The only actor in the model that makes a choice: whether, this round, to prepare an APS application for a funding source. The chance goes up with a named owner, a written deadline, real oversight, advocacy pressure and outside enforcement, and down with staff strain and cost pressure. Under pressure they may answer "no money, too expensive" and not start.',
    holds: 'Authority: the right to apply and a say over the budget.', rel: ['list', 'apply-hsip', 'apply-propl', 'apply-gf', 'fund-hsip', 'fund-propl', 'fund-gf', 'build', 'press-mdc', 'report', 'deflect', 'enforce', 'dir'] },
  A3: { who: 'SFMTA\'s in-house signal crews.',
    does: 'Install APS at funded intersections. They can only do so many a month, fewer when hiring is frozen; unfinished work carries over.',
    holds: 'Organisation: the ability to build.', rel: ['build', 'ride'] },
  C2: { who: 'Advocacy groups for blind and low-vision people, using the Mayor\'s Disability Council as one channel.',
    does: 'Raise the APS backlog from time to time. Pressure raises the chance that an application is started, then fades.',
    holds: 'Information, legitimacy and the possibility of a disability-rights lawsuit, but no budget.', rel: ['press', 'deflect', 'report'] },
  MDC: { who: 'The Mayor\'s Disability Council, a public meeting where SFMTA reports and the public speaks.',
    does: 'A place, not a decision-maker: advocacy pressure reaches SFMTA here, and SFMTA reports here twice a year.',
    holds: 'A public record.', rel: ['press', 'press-mdc', 'report'] },
  D1: { who: 'Outside enforcement: structured negotiation, a lawsuit or a court order.',
    does: 'Moves up in steps (none, uncertain, negotiation, lawsuit, court order). The higher the step, the harder it is to delay.',
    holds: 'Authority.', rel: ['enforce'] },
  DIR: { who: 'The head of SFMTA.',
    does: 'In PW1, the last fallback is asking the Director to move money to APS. In the model, whether that happens and how much are both assumptions.',
    holds: 'Authority over reallocations.', rel: ['dir'] },
  HSIP: { who: 'The federal Highway Safety Improvement Program, run in California by Caltrans.',
    does: 'A rule, not an actor. A call every two years. Projects need a benefit–cost ratio of at least 5 and must beat that round\'s cut-off; APS cannot be funded alone and must ride on a safety measure such as a signal-hardware upgrade. Each agency is capped; funded projects face design and construction deadlines.',
    holds: 'Federal safety money.', rel: ['apply-hsip', 'fund-hsip', 'runs-hsip'] },
  PROPL: { who: 'Prop L, San Francisco\'s transportation sales tax, with a five-year plan for signals.',
    does: 'A rule, not an actor. The plan can be amended, but only with the SFCTA Board\'s approval.',
    holds: 'Local money.', rel: ['apply-propl', 'fund-propl', 'runs-propl'] },
  GF: { who: 'The city\'s General Fund and capital plan.',
    does: 'A rule, not an actor. Requests are decided once a year.',
    holds: 'Local money.', rel: ['apply-gf', 'fund-gf'] },
  SS4A: { who: 'Safe Streets and Roads for All, another federal grant.',
    does: 'A rule, not an actor. It has funded APS before as part of corridor projects; whether it continues is uncertain.',
    holds: 'Federal money.', rel: ['apply-ss4a'] },
  CT: { who: 'Caltrans, the state transportation department.',
    does: 'Reviews HSIP applications, checks eligibility, approves funding and authorises construction.',
    holds: 'Authority over federal safety money.', rel: ['runs-hsip', 'fund-hsip'] },
  SFCTA: { who: 'The San Francisco County Transportation Authority Board.',
    does: 'Approves Prop L allocations and any amendment to the five-year signal plan.',
    holds: 'Authority over county money.', rel: ['runs-propl', 'fund-propl'] },
  PARENT: { who: 'Signal and street projects already planned at some intersections.',
    does: 'When one of them rebuilds a signal it can install APS along the way, without any APS application.',
    holds: 'Their own budgets.', rel: ['ride'] },
};

// Relationship types (legend). Colours are CSS variables in styles.css.
export const TYPES = {
  request: 'Ask for an APS', list: 'Pass on the request list', pressure: 'Advocacy pressure', report: 'Report back',
  deflect: '"No money, too expensive"', apply: 'Submit an application (missing link)', fund: 'Approve and fund',
  build: 'Hand over for construction', ride: 'Install along the way', rule: 'Runs the program', enforce: 'Legal pressure',
  reform: 'Added by the chosen pathway',
};

// Every relationship in the model, documented or broken. `broken`: allowed by the rules but rarely happens.
export const RELATIONS = [
  { id: 'request', from: 'C3', to: 'A1', type: 'request', label: 'ask for an APS at an intersection' },
  { id: 'list', from: 'A1', to: 'A2', type: 'list', label: 'pass on the scored request list' },
  { id: 'press', from: 'C2', to: 'MDC', type: 'pressure', label: 'raise the backlog in public' },
  { id: 'press-mdc', from: 'MDC', to: 'A2', type: 'pressure', label: 'pressure reaches SFMTA', bend: -1 },
  { id: 'report', from: 'A2', to: 'MDC', type: 'report', label: 'report progress twice a year', bend: 1 },
  { id: 'deflect', from: 'A2', to: 'C2', type: 'deflect', label: 'reply "no money, too expensive"' },
  { id: 'apply-hsip', from: 'A2', to: 'HSIP', type: 'apply', broken: true, label: 'submit an application', bend: 1 },
  { id: 'apply-propl', from: 'A2', to: 'PROPL', type: 'apply', broken: true, label: 'submit an application', bend: 1 },
  { id: 'apply-gf', from: 'A2', to: 'GF', type: 'apply', broken: true, label: 'submit a request', bend: 1 },
  { id: 'apply-ss4a', from: 'A2', to: 'SS4A', type: 'apply', broken: true, label: 'submit an application', bend: 1 },
  { id: 'fund-hsip', from: 'HSIP', to: 'A2', type: 'fund', label: 'approve and fund', bend: 1 },
  { id: 'fund-propl', from: 'PROPL', to: 'A2', type: 'fund', label: 'allocate', bend: 1 },
  { id: 'fund-gf', from: 'GF', to: 'A2', type: 'fund', label: 'allocate', bend: 1 },
  { id: 'runs-hsip', from: 'CT', to: 'HSIP', type: 'rule', label: 'runs the HSIP call' },
  { id: 'runs-propl', from: 'SFCTA', to: 'PROPL', type: 'rule', label: 'approves Prop L money' },
  { id: 'build', from: 'A2', to: 'A3', type: 'build', label: 'hand over funded sites' },
  { id: 'ride', from: 'PARENT', to: 'A3', type: 'ride', label: 'install APS with signal work, no application' },
  { id: 'enforce', from: 'D1', to: 'A2', type: 'enforce', label: 'negotiation, lawsuit or court order' },
  { id: 'dir', from: 'DIR', to: 'A2', type: 'fund', label: 'moves money (assumed fallback)' },
];

// Links each pathway adds (drawn in the accent colour).
export const REFORMS = {
  PW0: [],
  PW1: [{ from: 'A2', to: 'HSIP', label: 'bundle APS with the signal-visibility upgrade', bend: -1 }],
  PW2: [{ from: 'A2', to: 'PROPL', label: 'amend Prop L to restore an APS line', bend: -1 }],
  PW3: [{ from: 'A2', to: 'HSIP', label: 'named owner + deadline: applying becomes someone\'s job', bend: -1 },
    { from: 'A2', to: 'MDC', label: 'apply or explain, in public', bend: -1 },
    { from: 'A2', to: 'SFCTA', label: 'repeated non-application goes to the Board', bend: -1 }],
  PW4: [{ from: 'A2', to: 'PARENT', label: 'route each intersection to a planned project', bend: -1 }],
  PW5: [{ from: 'PARENT', to: 'A3', label: 'hardware change must include APS', bend: -1 }],
  PW6: [{ from: 'A2', to: 'A3', label: 'use the existing hardware-replacement line', bend: -1 }],
};

// Which relationship an event travels along.
export function relationFor(e) {
  const a = ALIAS[e.actor] || e.actor, t = ALIAS[e.target] || e.target;
  const venueOf = x => ({ HSIP: 'hsip', PROPL: 'propl', GF: 'gf', SS4A: 'ss4a' })[x];
  switch (e.action) {
    case 'request': case 'classify': return 'request';
    case 'press': return 'press';
    case 'deflect': return 'deflect';
    case 'start_prep': case 'submit': case 'miss_deadline': case 'prep_abort':
      return venueOf(t) ? 'apply-' + venueOf(t) : null;
    case 'approve': case 'reject': case 'eligibility_fail': case 'red_flag': case 'contract_out': case 'extend': case 'return_funds':
      return a === 'CT' ? 'fund-hsip' : a === 'SFCTA' ? 'fund-propl' : a === 'GF' ? 'fund-gf' : null;
    case 'allocate': case 'topup':
      return a === 'DIR' ? 'dir' : a === 'SFCTA' ? 'fund-propl' : a === 'GF' ? 'fund-gf' : null;
    case 'batch_fund': case 'handoff': return 'build';
    case 'install': return a === 'PARENT' ? 'ride' : 'build';
    case 'rule_apply': case 'skip_rule': case 'scope_add': case 'reroute': return 'ride';
    case 'enforce_up': return 'enforce';
    default:
      if (e.action.startsWith('failure:')) {
        if (a === 'CT' || t === 'HSIP') return 'fund-hsip';
        if (a === 'SFCTA') return 'fund-propl';
        if (a === 'DIR') return 'dir';
        if (a === 'C2') return 'press';
      }
      return null;
  }
}

const count = n => `${n} intersection${n === 1 ? '' : 's'}`;
const SETBACK = {
  'F-a': 'the package did not reach the minimum benefit–cost ratio of 5, so it could not be filed',
  'F-b': 'the application fell below this round\'s cut-off',
  'F-c': 'an unresolved red flag on another project made SFMTA ineligible this round',
  'F-d': 'a delivery deadline was missed',
  'F-e': 'Caltrans did not allow in-house work, so the job goes to a contractor (slower, dearer)',
  'F-f': 'costs ran over and the extra money was not found',
  'F-g': 'the partner project slipped or was cancelled',
  'F-h': 'the person responsible for APS funding left',
  'F-j': 'the Prop L amendment was rejected or delayed',
  'F-k': 'the Director\'s reallocation did not go to APS',
  'F-m': 'advocacy went quiet for a while',
};
const VENUE = { HSIP: 'the federal safety grant (HSIP)', PROPL: 'Prop L', GF: 'the General Fund', LOCAL: 'local money', SS4A: 'SS4A' };
const cycle = d => { const m = /\bC(\d{2})\b/.exec(d || ''); return m ? ` (cycle ${+m[1]})` : ''; };

// One plain-English sentence per event.
export function humanize(e) {
  const n = (e.intersections || []).length, d = e.detail || '';
  if (e.action === 'failure:F-j' && /SG017/.test(d)) return 'Setback: the existing signal-hardware line (SG017) could not be used for new APS.';
  if (e.action.startsWith('failure:')) return `Setback: ${SETBACK[e.action.slice(8)] || 'something went wrong'}.`;
  switch (e.action) {
    case 'press': return 'Advocates raised the APS backlog at the Mayor\'s Disability Council.';
    case 'deflect': return 'SFMTA\'s funding staff answered "no money, too expensive" and did not start an application.';
    case 'start_prep': return `SFMTA's funding staff started preparing an APS application for ${VENUE[e.target] || e.target}.`;
    case 'submit':
      if (/not submitted|below 5/.test(d)) return `SFMTA's funding staff put together an APS package for ${VENUE[e.target] || e.target}${cycle(d)}, but it did not reach the minimum benefit–cost ratio, so nothing was filed.`;
      return n ? `SFMTA's funding staff submitted an application to ${VENUE[e.target] || e.target}${cycle(d)} covering ${count(n)}.`
        : `SFMTA's funding staff submitted a request to ${VENUE[e.target] || e.target}.`;
    case 'miss_deadline': return `The ${VENUE[e.target] || e.target} deadline passed with no APS application ready.`;
    case 'prep_abort': return 'A half-written APS application was dropped.';
    case 'approve':
      if (e.actor === 'CT') return `Caltrans approved HSIP funding${cycle(d)} for ${count(n)}.`;
      if (e.actor === 'SFCTA' && /SG017/.test(d)) return 'SFCTA approved money from the existing signal-hardware line (SG017) that now includes new APS.';
      if (e.actor === 'SFCTA') return 'The SFCTA Board approved a Prop L amendment that restores an APS line.';
      if (e.actor === 'GF') return 'The city approved a General Fund line for APS.';
      return `${nodeName(e.actor)} approved funding.`;
    case 'reject': return `Caltrans did not fund the application${cycle(d)}${n ? ` covering ${count(n)}` : ''}.`;
    case 'eligibility_fail': return 'Caltrans found SFMTA ineligible this round.';
    case 'allocate':
      if (e.actor === 'DIR') return 'The SFMTA Director moved money to APS (an assumed fallback in the model).';
      return `${e.actor === 'SFCTA' ? 'Prop L' : 'The General Fund'} allocated ${d ? d + ' ' : ''}for ${n ? count(n) : 'APS'}.`;
    case 'batch_fund': return `${count(n)} now funded and handed to the crews.`;
    case 'handoff': return `${count(n)} finished design and went to the city crews.`;
    case 'install': return e.actor === 'PARENT' ? `${count(n)} got APS along with signal work.` : `City crews installed APS at ${count(n)}.`;
    case 'topup': return 'Extra money covered a cost overrun.';
    case 'enforce_up': return 'Outside pressure went up a step (for example, structured negotiation or a lawsuit).';
    case 'owner_quit': return 'The person responsible for APS funding left; the post is empty.';
    case 'owner_filled': return 'A new person responsible for APS funding started.';
    case 'pathway_switch': return 'The plan\'s warning sign was reached, so the pathway moved to its next step.';
    case 'rule_apply': return `Signal hardware was replaced at ${count(n)}; under the design rule, APS there is now funded and waits for the city crews.`;
    case 'skip_rule': return `Signal hardware was replaced at ${count(n)}, but the yearly APS add-on budget was used up.`;
    case 'scope_add': return `${count(n)} added to planned projects.`;
    case 'reroute': return `${count(n)} rerouted after a planned project slipped.`;
    case 'overrun_revert': return `${count(n)} went back to the waiting list after a cost overrun.`;
    case 'return_funds': return `HSIP money was returned for ${count(n)}; they are back on the waiting list.`;
    case 'red_flag': return 'Caltrans flagged a missed milestone.';
    case 'contract_out': return 'The work was contracted out.';
    case 'extend': return 'Caltrans granted an extension.';
    case 'partner_delay': return 'The partner project slipped; APS waits with it.';
    case 'pause': return 'Work paused.';
    default: return `${nodeName(e.actor)} → ${nodeName(e.target)}: ${e.action.replace(/_/g, ' ')}.`;
  }
}

export const IMPORTANT = new Set(['approve', 'reject', 'allocate', 'submit', 'miss_deadline', 'deflect', 'pathway_switch',
  'enforce_up', 'owner_quit', 'return_funds', 'start_prep', 'eligibility_fail', 'contract_out', 'red_flag', 'rule_apply']);
