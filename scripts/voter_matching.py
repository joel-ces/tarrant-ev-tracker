#!/usr/bin/env python3
"""Match 2026 early voters to how and when they voted in 2022 and 2024. Voter-level files stay PRIVATE; only aggregates are written to data/returning/.
Alignment is by days before Election Day (2022: Nov 8, 2024: Nov 5, 2026: Nov 3); all three early voting windows run 15 to 4 days out. Day N of 2026 = 16 - N days out.

  one time:  voter_matching.py prior --ge22 GE22.csv --ge24 GE24.csv --out PRIVATE/prior_votes.csv.gz
  daily:     voter_matching.py daily [--rolls PRIVATE/rolls_compact.csv.gz] --prior PRIVATE/prior_votes.csv.gz --state PRIVATE/early_2026.csv.gz --day N --inperson ROSTER.txt --mail ROSTER.txt --out data/returning/day-NN.json
"""
import argparse, json, os
import pandas as pd

ED = {2022: pd.Timestamp('2022-11-08'), 2024: pd.Timestamp('2024-11-05'), 2026: pd.Timestamp('2026-11-03')}
def norm(s):   # keep 10-digit IDs; pad 8-9 digit IDs that lost leading zeros; everything else (e.g. '--Redacted--') is unmatchable
    s = s.astype(str).str.strip(); s = s.where(~s.str.fullmatch(r'\d{8,9}'), s.str.zfill(10)); return s.where(s.str.fullmatch(r'\d{10}'))

def build_prior(a):
    g22 = pd.read_csv(a.ge22, dtype=str).rename(columns={'ID_VOTER': 'vuid', 'VOTING_METHOD': 'm', 'VOTING_DATE': 'date'})[['vuid', 'm', 'date']]
    g24 = pd.read_csv(a.ge24, dtype=str).rename(columns={'VUID': 'vuid', 'vote_method': 'm'})[['vuid', 'm', 'date']]
    g22['m'] = g22.m.map({'IN-PERSON': 'EV', 'MAIL-IN': 'BM', 'ED': 'ED'})
    out = []
    for g, y in ((g22, 2022), (g24, 2024)):
        g['vuid'] = norm(g.vuid); g = g.dropna(subset=['vuid']).drop_duplicates('vuid'); g['d'] = (ED[y] - pd.to_datetime(g['date'], format='%m/%d/%Y')).dt.days
        out.append(g[['vuid', 'm', 'd']].rename(columns={'m': f'm{y % 100}', 'd': f'd{y % 100}'}))
    prior = out[0].merge(out[1], on='vuid', how='outer'); prior.to_csv(a.out, index=False); print(f"prior records: {len(prior):,} -> {a.out}")

def daily(a):
    rd = lambda p, cols: pd.read_csv(p, sep='\t', dtype=str, usecols=cols, encoding_errors='replace')
    state = pd.read_csv(a.state, dtype={'vuid': str}) if os.path.exists(a.state) else pd.DataFrame(columns=['vuid', 'm26', 'dbe'])
    x = rd(a.inperson, ['SOS Voter ID']); x['vuid'] = norm(x['SOS Voter ID']); new = x.dropna(subset=['vuid']).drop_duplicates('vuid')[['vuid']]
    ev = state[state.m26 == 'EV']; new = new[~new.vuid.isin(ev.vuid)]; new['m26'] = 'EV'; new['dbe'] = 16 - a.day
    m = rd(a.mail, ['SOS Voter ID', 'Return Date']); m['vuid'] = norm(m['SOS Voter ID']); m = m.dropna(subset=['vuid']).drop_duplicates('vuid')
    m['dbe'] = (ED[2026] - pd.to_datetime(m['Return Date'], format='mixed')).dt.days; m['m26'] = 'BM'
    state = pd.concat([ev, new, m[['vuid', 'm26', 'dbe']]]).drop_duplicates('vuid'); state.to_csv(a.state, index=False)
    p = pd.read_csv(a.prior, dtype={'vuid': str}); p['v26'] = p.vuid.isin(set(state.vuid)); POINT = 16 - a.day
    # past voters who are no longer on the registration rolls (moved, died, cancelled) are left out of the retention pools when --rolls is given
    p['onroll'] = p.vuid.isin(set(pd.read_csv(a.rolls, dtype={'vuid': str}, usecols=['vuid']).vuid)) if a.rolls else True   # voted on/before this many days out = "same point in the cycle"
    e24, e22 = p.m24.isin(['EV', 'BM']), p.m22.isin(['EV', 'BM']); ed24, ed22 = p.m24 == 'ED', p.m22 == 'ED'
    j = state.merge(p, on='vuid', how='left'); n = len(j)
    def rate(pool, hit):
        pr_ = pool & p.onroll
        return dict(pool=int(pr_.sum()), voted=int((pr_ & hit).sum()), share=round(float((pr_ & hit).sum() / max(pr_.sum(), 1) * 100), 1), pool_all=int(pool.sum()), left_rolls=int((pool & ~p.onroll).sum()))
    res = {'day': a.day, 'early_voters_matched': n,
           'composition': {k: int(v.sum()) for k, v in {'voted_early_2024': j.m24.isin(['EV', 'BM']), 'election_day_2024': j.m24 == 'ED', 'no_2024_vote': j.m24.isna(), 'voted_early_2022': j.m22.isin(['EV', 'BM']),
                           'election_day_2022': j.m22 == 'ED', 'no_2022_vote': j.m22.isna(), 'both_years': j.m22.notna() & j.m24.notna(), 'neither_year': j.m22.isna() & j.m24.isna()}.items()},
           'retention_2026': {'early_2024': rate(e24, p.v26), 'in_person_2024': rate(p.m24 == 'EV', p.v26), 'mail_2024': rate(p.m24 == 'BM', p.v26), 'election_day_2024': rate(ed24, p.v26), 'early_2022': rate(e22, p.v26),
                              'election_day_2022': rate(ed22, p.v26), 'early_both': rate(e22 & e24, p.v26), 'voted_2024_not_2022': rate(p.m24.notna() & p.m22.isna(), p.v26)}}
    v24 = p.m24.isin(['EV', 'BM']) & (p.d24 >= POINT)
    res['same_point'] = {'point_days_out': POINT, 'early_2022_to_2024': rate(e22, v24), 'early_2024_to_2026': rate(e24, p.v26), 'election_day_2022_to_2024': rate(ed22, v24), 'election_day_2024_to_2026': rate(ed24, p.v26)}
    res['by_past_day'] = [{'days_out': d, 'in_person_2024': rate((p.m24 == 'EV') & (p.d24 == d), p.v26), 'in_person_2022_to_2024': rate((p.m22 == 'EV') & (p.d22 == d), v24)} for d in range(15, 3, -1)]
    if a.rolls:   # retention by day, among past voters still registered
        sd = (16 - state.dbe).where(state.m26 == 'EV', (16 - state.dbe).clip(lower=1)).astype(int); res['retention_definition'] = 'past voters still on the registration rolls'; res['retention_series'] = []
        for d_ in range(1, a.day + 1):
            vd = p.vuid.isin(set(state.vuid[sd <= d_])); res['retention_series'].append({'day': d_, 'e24': rate(e24, vd)['share'], 'e22': rate(e22, vd)['share'], 'ed24': rate(ed24, vd)['share']})
    res['method_grid_2026_by_2024'] = {m26: j[j.m26 == m26].m24.fillna('none').value_counts().to_dict() for m26 in ('EV', 'BM')}
    t = j[(j.m26 == 'EV') & (j.m24 == 'EV')]; sh = t.dbe - t.d24
    res['timing_in_person_returners'] = {'n': len(t), 'median_days_earlier': float(sh.median()), 'earlier_2plus': round(float((sh >= 2).mean() * 100), 1), 'same_within_1': round(float((sh.abs() <= 1).mean() * 100), 1), 'later_2plus': round(float((sh <= -2).mean() * 100), 1),
                                'caveat': 'only voters already voted by this day, so censored toward early'}
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True); json.dump(res, open(a.out, 'w'), indent=1); print(f"day {a.day}: {n:,} matched; early-2024 retention {res['retention_2026']['early_2024']['share']}% -> {a.out}")

ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
p1 = sp.add_parser('prior'); p1.add_argument('--ge22', required=True); p1.add_argument('--ge24', required=True); p1.add_argument('--out', required=True)
p2 = sp.add_parser('daily'); [p2.add_argument(f'--{k}', required=True) for k in ('prior', 'state', 'inperson', 'mail', 'out')]; p2.add_argument('--day', type=int, required=True); p2.add_argument('--rolls', default=None)
a = ap.parse_args(); build_prior(a) if a.cmd == 'prior' else daily(a)
