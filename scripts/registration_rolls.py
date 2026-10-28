#!/usr/bin/env python3
"""Turn the full Tarrant registration rolls (VUID, PRECINCT, GENDER, DOB, registration_date, PE2026..PE2016, GE2024..GE2016) into ONE compact private file.
The compact file keeps: vuid, precinct (4-digit, blank if missing/placeholder), gender, age on Nov 3 2026 (instead of the exact DOB), registration date (blank if implausible), primary history (6 chars, newest first: N/R/D), general history (5 chars, newest first: V/N).
Names/addresses are not in the rolls and exact birth dates are not kept. The compact file goes in the PRIVATE repo only.
usage: registration_rolls.py --rolls TarrantRegistrationRolls.txt --out PRIVATE/rolls_compact.csv.gz"""
import argparse
import pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument('--rolls', required=True); ap.add_argument('--out', required=True); ap.add_argument('--election', default='2026-11-03'); a = ap.parse_args()
r = pd.read_csv(a.rolls, dtype=str, keep_default_na=False)
import re
pe = [c for c in r.columns if re.fullmatch(r'PE\d{4}', c)]; ge = [c for c in r.columns if re.fullmatch(r'GE\d{4}', c)]     # year columns only (not GENDER)
pe.sort(reverse=True); ge.sort(reverse=True)
r['vuid'] = r.VUID.str.strip().where(r.VUID.str.strip().str.len() >= 10, r.VUID.str.strip().str.zfill(10))
pn = pd.to_numeric(r.PRECINCT, errors='coerce'); r['precinct'] = pn.astype('Int64')
dob = pd.to_datetime(r.DOB, format='%Y%m%d', errors='coerce'); dob = dob.where(dob > '1905-01-01')
age = ((pd.Timestamp(a.election) - dob).dt.days / 365.2425).apply(lambda x: int(x) if pd.notna(x) else None)
reg = pd.to_datetime(r.registration_date, format='%Y%m%d', errors='coerce'); reg = reg.where((reg >= '1900-01-01') & (reg <= '2026-10-31'))
out = pd.DataFrame({'vuid': r.vuid, 'precinct': r.precinct, 'gender': r.GENDER, 'age': age, 'reg_date': reg.dt.strftime('%Y-%m-%d'), 'pe': r[pe].agg(''.join, axis=1), 'ge': r[ge].agg(''.join, axis=1)})
out.to_csv(a.out, index=False)
print(f"{len(out):,} voters -> {a.out} | precinct missing {int(out.precinct.isna().sum())} | age missing {int(out.age.isna().sum())} | reg_date missing/implausible {int(out.reg_date.isna().sum()):,} | order: PE {pe}, GE {ge}")
