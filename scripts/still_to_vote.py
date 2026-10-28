#!/usr/bin/env python3
"""Who is still to vote, by precinct (totals only). A past voter counts only if still on the registration rolls.
For each precinct: registered; early voters; and for four pools -- 2024 early voters, 2024 Election Day voters, voters in the 2022 or 2024 general (any method), and voters with no general
vote 2016-2024 -- how many are in the pool and how many have already voted early in 2026.
usage: still_to_vote.py --rolls PRIVATE/rolls_compact.csv.gz --prior PRIVATE/prior_votes.csv.gz --state PRIVATE/early_2026.csv.gz --out data/profile/still_to_vote.json"""
import argparse, json, os
import pandas as pd

ap = argparse.ArgumentParser()
for k in ('rolls', 'prior', 'state', 'out'): ap.add_argument(f'--{k}', required=True)
a = ap.parse_args()
c = pd.read_csv(a.rolls, dtype={'vuid': str, 'ge': str, 'pe': str}); pr = pd.read_csv(a.prior, dtype={'vuid': str}); st = pd.read_csv(a.state, dtype={'vuid': str})
c['early'] = c.vuid.isin(set(st.vuid)); c['ngen'] = c['ge'].str.count('V'); c['g2224'] = c['ge'].str[:2].str.contains('V')
c = c.merge(pr[['vuid', 'm22', 'm24']], on='vuid', how='left'); c = c.dropna(subset=['precinct']); c['precinct'] = c.precinct.astype(int)
pools = {'e24': c.m24.isin(['EV', 'BM']), 'ed24': c.m24 == 'ED', 'gen': c.g2224, 'nogen': c.ngen == 0}
out = {}
for p, g in c.groupby('precinct'):
    row = [len(g), int(g.early.sum())]
    for name in ('e24', 'ed24', 'gen', 'nogen'): m = pools[name].loc[g.index]; row += [int(m.sum()), int((m & g.early).sum())]
    out[str(p)] = row
tot = [sum(v[i] for v in out.values()) for i in range(10)]
json.dump({'fields': ['registered', 'early', 'e24_pool', 'e24_voted', 'ed24_pool', 'ed24_voted', 'gen_pool', 'gen_voted', 'nogen_pool', 'nogen_voted'], 'precincts': out}, open(a.out, 'w'), separators=(',', ':'))
print(f"{a.out}: {len(out)} precincts | registered {tot[0]:,} | early {tot[1]:,} | 2024 early pool {tot[2]:,} voted {tot[3]:,} still {tot[2]-tot[3]:,} | 2024 ED pool {tot[4]:,} voted {tot[5]:,} still {tot[4]-tot[5]:,} | 2022/2024 general pool {tot[6]:,} voted {tot[7]:,} | no general pool {tot[8]:,} voted {tot[9]:,}")
