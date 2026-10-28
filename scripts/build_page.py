#!/usr/bin/env python3
"""Rebuild the data constants inside index.html from the saved daily files (aggregates only). Run from the repo root:
    python3 scripts/build_page.py
Reads data/daily/day-NN.json (+ locations-day-NN.json) and the latest data/mail/abs-*.json. Everything else in the page is untouched.
Updates: DATA2026, TURNOUT_BY_PRECINCT, GEO, HIST_EARLY, HIST_METHOD (early parts), HIST_CROSS (early part), PRECINCT_HISTORY, NP_METHOD, NP_BY_PRECINCT, PROFILE, STILL_TO_VOTE, NP_BY_DAY, HIST_EARLY_BY_DAY, POLL_BY_DAY, NP_TREND, RETURNING, CATEGORY_BY_DAY, POLL_VOTES, MAIL26.
"""
import glob, json, os, re
from datetime import date

PAGE = 'index.html'
html = open(PAGE).read()
def const_span(name):
    s = html.index(f'const {name} = ') + len(f'const {name} = '); return s, html.index(';\n', s)
def get(name): s, e = const_span(name); return json.loads(html[s:e])
def put(name, js):
    global html; s, e = const_span(name); html = html[:s] + js + html[e:]
dump = lambda o: json.dumps(o, separators=(',', ':'))
MONTH = lambda iso: date.fromisoformat(iso).strftime('%b ') + str(date.fromisoformat(iso).day)

PRE = get('PRECINCTS'); REG = {int(k): v for k, v in get('REGISTERED').items()}; LEAN = {int(k): v for k, v in get('PARTISAN').items()}
meta = {p['p']: p for p in PRE}
days = [json.load(open(f)) for f in sorted(glob.glob('data/daily/day-*.json'))]
if not days: raise SystemExit('no data/daily/day-*.json files yet')
latest = days[-1]

def tilt(precincts):
    reg = regl = v = vl = 0
    for p in meta:
        l, r = LEAN.get(p), REG.get(p)
        if l is None or not r: continue
        reg += r; regl += r * l; t = precincts.get(str(p), 0); v += t; vl += t * l
    return round(((2 * (vl / v) - 1) - (2 * (regl / reg) - 1)) * 100, 1)

# --- DATA2026 (one entry per processed day)
entries = []
for d in days:
    h = d.get('history_summary', {})
    e = dict(date=MONTH(d['snapshot_date']), day=d['day'], mail_daily=d['mail_new'], mail_cumulative=d['mail_cumulative'],
             inperson_daily=d['in_person_new'], inperson_cumulative=d['in_person_cumulative'], tilt=tilt(d['precincts']))
    if h: e.update(hist_e=h['early_r_share'], hist_d=h['divergence_pts'])
    entries.append(e)
fmt = lambda e: '  { ' + ', '.join(f'{k}:{json.dumps(v)}' for k, v in e.items()) + ' }'
html = re.sub(r'const DATA2026 = \[.*?\n\];', 'const DATA2026 = [\n' + ',\n'.join(fmt(e) for e in entries) + '\n];', html, count=1, flags=re.S)

# --- per-precinct turnout, history, geography
put('TURNOUT_BY_PRECINCT', dump({int(k): v for k, v in latest['precincts'].items()}))
put('HIST_EARLY', dump(latest.get('history_early', {})))
import sys
hm = get('HIST_METHOD'); lm = latest.get('history_method', {}); base_tot = hm['base']
if '--refresh-base' in sys.argv:   # after a new/changed primary-history list: python3 scripts/build_page.py --refresh-base
    hb = {k: v for k, v in json.load(open('data/history_base.json')).items() if int(k) in meta}
    put('HIST_BASE', dump(hb)); base_tot = [sum(v[0] for v in hb.values()), round(sum(v[1] for v in hb.values()), 3)] + [sum(v[2 + i] for v in hb.values()) for i in range(5)]
put('HIST_METHOD', dump({'base': base_tot, 'inperson': lm.get('inperson'), 'mail': lm.get('mail')}))
hc = get('HIST_CROSS'); cross_base = json.load(open('data/history_base_cross.json'))['base'] if '--refresh-base' in sys.argv else hc['base']
put('HIST_CROSS', dump({'base': cross_base, 'early': latest.get('history_cross', {}).get('early', [0] * 8)}))
npm = latest.get('history_nonprimary')
if npm: put('NP_METHOD', dump({'inperson': npm['inperson'], 'mail': npm['mail']})); put('NP_BY_PRECINCT', dump(npm['by_precinct']))
def _cat(d):   # per day, cumulative early voters by primary history as [Democratic-leaning, Republican-leaning, no primary history (incl. redacted IDs)]
    hm = d['history_method']; n = d['history_nonprimary']
    one = lambda m: [hm[m][5] + hm[m][6], hm[m][2] + hm[m][3], n[m][1] + n[m][2]]
    i, m = one('inperson'), one('mail')
    return {'day': d['day'], 'label': MONTH(d['snapshot_date']), 't': [x + y for x, y in zip(i, m)], 'i': i, 'm': m}
if all('history_nonprimary' in d and d.get('history_method', {}).get('inperson') for d in days): put('CATEGORY_BY_DAY', dump([_cat(d) for d in days]))
if all('history_nonprimary' in d and d.get('history_early') for d in days):   # precinct-lean tilt of no-primary vs primary early voters, by day
    HBi = {int(k): v for k, v in get('HIST_BASE').items()}; okp = [p for p in meta if p in LEAN and REG.get(p)]; mrg = lambda x: (2 * x - 1) * 100
    reg_np = {p: max(0, REG[p] - HBi.get(p, [0])[0]) for p in okp}
    b_np = mrg(sum(reg_np[p] * LEAN[p] for p in okp) / sum(reg_np.values())); b_pr = mrg(sum(HBi.get(p, [0])[0] * LEAN[p] for p in okp) / sum(HBi.get(p, [0])[0] for p in okp))
    trend = []
    for d in days:
        P = {int(k): v for k, v in d['history_nonprimary']['by_precinct'].items()}; HEd = {int(k): v for k, v in d['history_early'].items()}
        ln = mrg(sum(P.get(p, [0])[0] * LEAN[p] for p in okp) / sum(P.get(p, [0])[0] for p in okp)); lp = mrg(sum(HEd.get(p, [0])[0] * LEAN[p] for p in okp) / sum(HEd.get(p, [0])[0] for p in okp))
        trend.append({'day': d['day'], 'label': MONTH(d['snapshot_date']), 'npl': round(ln, 1), 'npt': round(ln - b_np, 1), 'prl': round(lp, 1), 'prt': round(lp - b_pr, 1)})
    put('NP_TREND', dump(trend))
rd_files = sorted(glob.glob('data/returning/day-*.json'))
if rd_files:   # returning voters: retention series by day + the latest full result (aggregates only)
    lab = {d['day']: MONTH(d['snapshot_date']) for d in days}; series = []
    for f in rd_files:
        r = json.load(open(f)); rt = r['retention_2026']
        series.append({'day': r['day'], 'label': lab.get(r['day'], ''), 'matched': r['early_voters_matched'], 'e24': rt['early_2024']['share'], 'e22': rt['early_2022']['share'], 'ed24': rt['election_day_2024']['share']})
    _latest = json.load(open(rd_files[-1])); _rs = {x['day']: x for x in _latest.get('retention_series', [])}   # same-definition curve for every day (pools = past voters still registered)
    for _row in series:
        if _row['day'] in _rs: _row.update({k: _rs[_row['day']][k] for k in ('e24', 'e22', 'ed24')})
    put('RETURNING', dump({'days': series, 'latest': _latest}))
# per-day map data so the map can be shown "as of" any day: no-primary-history counts, early-voter primary-history [n, sum of R shares], and cumulative votes by location
put('NP_BY_DAY', dump({str(d['day']): {k: v[0] for k, v in d['history_nonprimary']['by_precinct'].items() if v[0]} for d in days if 'history_nonprimary' in d}))
put('HIST_EARLY_BY_DAY', dump({str(d['day']): {k: [v[0], round(v[1], 2)] for k, v in d.get('history_early', {}).items()} for d in days}))
_locs = sorted(glob.glob('data/daily/locations-day-*.json'))
if _locs:
    _L = json.load(open(_locs[-1])); _pb = {}
    for _n, _v in _L['locations'].items():
        _acc, _arr = 0, []
        for _c in _L['dates']: _acc += _v['by_day'][_c]; _arr.append(_acc)
        _pb[int(_n)] = _arr
    put('POLL_BY_DAY', dump(_pb))
if os.path.exists('data/profile/still_to_vote.json'): put('STILL_TO_VOTE', dump(json.load(open('data/profile/still_to_vote.json'))))   # past voters still to vote, by precinct
if os.path.exists('data/profile/profile.json'): put('PROFILE', dump(json.load(open('data/profile/profile.json'))))   # voter profile totals (age, registration, general record, first-time voters)
put('PRECINCT_HISTORY', dump([{'day': d['day'], 'label': d['label'], 'p': d['precincts']} for d in days]))
groups = [("By Commissioner Precinct", "com", "Commissioner Pct"), ("By State Senate District", "sen", "Senate District"), ("By State House District", "hse", "House District"),
          ("By Congressional District", "cong", "Congressional District"), ("By State Board of Education District", "sboe", "SBOE District"), ("By Justice of the Peace Precinct", "jp", "Justice of the Peace Precinct")]
def rows(field, prefix):
    tot = {}
    for p, v in latest['precincts'].items():
        k = meta[int(p)][field]; tot[k] = tot.get(k, 0) + v
    return [{"key": k, "name": f"{prefix} {k}", "count": tot.get(k, 0)} for k in sorted({m[field] for m in PRE}, key=int)]
geo = f'const GEO = {{ date:"{MONTH(latest["snapshot_date"])}", groups:[\n' + ''.join(f'  {{title:"{t}", field:"{f}", rows:{json.dumps(rows(f, pre))}}},\n' for t, f, pre in groups) + ']};'
gs = html.index('const GEO = '); html = html[:gs] + geo + html[html.index(']};', gs) + 3:]

# --- polling locations (latest by-location report)
locs = sorted(glob.glob('data/daily/locations-day-*.json'))
if locs: put('POLL_VOTES', dump({int(n): v['total'] for n, v in sorted(json.load(open(locs[-1]))['locations'].items(), key=lambda x: int(x[0]))}))

# --- mail sent vs received (latest absentee report)
abs_files = sorted(glob.glob('data/mail/abs-*.json'))
if abs_files:
    a = json.load(open(abs_files[-1])); S, R = a['sent'], a['received']
    ds = sorted(set(S['Total']['by_date']) | set(R['Total']['by_date']))
    g = lambda blk, k, d: blk[k]['by_date'].get(d, 0)
    rows_ = [[d, g(S, 'Total', d), g(R, 'Total', d), g(S, 'FPCA', d), g(R, 'FPCA', d)] for d in ds]
    stamp = a['report_asof']; asof = f"{MONTH(stamp[:10])}, {stamp[11:]}"
    put('MAIL26', f'{{asof:"{asof}", election:"2026-11-03", days:{dump(rows_)}}}')
lm2 = latest.get('history_method', {})
if lm2.get('inperson') and lm2.get('mail'):
    e = [a + b for a, b in zip(lm2['inperson'], lm2['mail'])]; b0 = get('HIST_METHOD')['base']
    dsh = lambda a: (a[5] + a[6]) / (a[2] + a[3] + a[5] + a[6]) * 100
    print(f"plain split (primary voters): early {dsh(e):.0f}% D-leaning / {100 - dsh(e):.0f}% R-leaning vs all list voters {dsh(b0):.0f}% / {100 - dsh(b0):.0f}% | early voters on list {sum(e[2:7]):,}")
open(PAGE, 'w').write(html)
print(f"built from {len(days)} day(s); latest {latest['label']} | in-person {latest['in_person_cumulative']:,} | mail {latest['mail_cumulative']:,} | tilt {entries[-1]['tilt']:+} | mail report {abs_files[-1] if abs_files else 'none'}")
