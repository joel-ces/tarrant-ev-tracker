#!/usr/bin/env python3
"""Voter profile totals: early voters vs. registered voters by age, registration date, and general-election record (2016-2024), plus first-time-voter measures.
Reads the PRIVATE compact rolls and the PRIVATE 2026 early-voter record; writes TOTALS ONLY to data/profile/profile.json.
usage: voter_profile.py --rolls PRIVATE/rolls_compact.csv.gz --state PRIVATE/early_2026.csv.gz --out data/profile/profile.json"""
import argparse, json, os
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument('--rolls', required=True); ap.add_argument('--state', required=True); ap.add_argument('--out', required=True); a = ap.parse_args()
c = pd.read_csv(a.rolls, dtype={'vuid': str, 'pe': str, 'ge': str}); st = pd.read_csv(a.state, dtype={'vuid': str})
st['day'] = np.where(st.m26 == 'EV', 16 - st.dbe, (16 - st.dbe).clip(lower=1)).astype(int)
c = c.merge(st[['vuid', 'day']], on='vuid', how='left'); c['early'] = c.day.notna(); c['reg'] = pd.to_datetime(c.reg_date)
c['ngen'] = c['ge'].str.count('V'); c['pprim'] = c['pe'].str[1:].str.count('[RD]'); c['p26'] = c['pe'].str[0]; c['first26'] = c.p26.isin(['R', 'D']) & (c.pprim == 0)
E = c[c.early]; last = int(st.day.max())
BANDS = [("Under 18", 0, 17), ("18-24", 18, 24), ("25-34", 25, 34), ("35-44", 35, 44), ("45-54", 45, 54), ("55-64", 55, 64), ("65+", 65, 200)]
COHORTS = [("Before 2016", None, '2015-12-31'), ("2016-2019", '2016-01-01', '2019-12-31'), ("2020 to the 2022 general", '2020-01-01', '2022-11-08'), ("After the 2022 general, before the 2024 general", '2022-11-09', '2024-11-05'), ("Since the 2024 general", '2024-11-06', '2026-10-31')]
def band(df): return {b[0]: int(df.age.between(b[1], b[2]).sum()) for b in BANDS} | {"Unknown": int(df.age.isna().sum())}
def cohort(df): return {n: int(((df.reg <= hi) & ((df.reg >= lo) if lo else True)).sum()) for n, lo, hi in COHORTS} | {"Unknown": int(df.reg.isna().sum())}
def gens(df): return {str(k): int((df.ngen == k).sum()) for k in range(6)}
res = {'day': last, 'registered_total': len(c), 'early_total': len(st), 'early_on_rolls': len(E), 'early_not_on_rolls': len(st) - len(E),
       'age': {'registered': band(c), 'early': band(E)}, 'registration': {'registered': cohort(c), 'early': cohort(E)}, 'generals': {'registered': gens(c), 'early': gens(E)}}
new = c.reg > '2024-11-05'; never = c.ngen == 0
res['new_voters'] = {'new_registrants_registered': int(new.sum()), 'new_registrants_early': int((new & c.early).sum()),
                     'no_general_registered': int(never.sum()), 'no_general_early': int((never & c.early).sum()), 'no_general_new_registrants_early': int((never & new & c.early).sum()), 'no_general_long_registered_early': int((never & ~new & c.early).sum()),
                     'no_general_new_registrants_registered': int((never & new).sum()), 'no_general_long_registered_registered': int((never & ~new).sum())}
f = c[c.first26]; rows = {}
for name, m in (("any", f.ngen >= 0), ("with_general", f.ngen >= 1), ("no_general", f.ngen == 0)): g = f[m]; rows[name] = {'voters': len(g), 'early': int(g.early.sum()), 'democratic': int((g.p26 == 'D').sum()), 'median_age': float(g.age.median()), 'new_registrants': int((g.reg > '2024-11-05').sum())}
res['first_time_primary'] = rows
cum = []
for d in range(1, last + 1):
    day_v = E[E.day == d]; res.setdefault('by_day', []).append({'day': d, 'age': band(day_v), 'new_registrants': int((day_v.reg > '2024-11-05').sum()), 'voters': len(day_v)})
os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True); json.dump(res, open(a.out, 'w'), indent=1)
print(f"{a.out}: through day {last} | {len(E):,} early voters on the rolls of {len(st):,} | 65+ share of early {res['age']['early']['65+']/len(E)*100:.1f}% vs registered {res['age']['registered']['65+']/len(c)*100:.1f}%")
