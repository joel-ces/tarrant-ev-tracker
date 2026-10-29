#!/usr/bin/env python3
"""Daily stacked-bar graphic: early voters each day by primary history (Democratic-leaning, Republican-leaning, no primary history).
Run from the repo root:  python3 scripts/make_category_chart.py [--out out/]
Democratic-leaning = Lean D + Reliable D; Republican-leaning = Lean R + Reliable R; 'No primary history' also holds the few early voters
with redacted IDs. Daily counts are each day's change in the running totals (Day 1 includes mail returned before early voting opened)."""
import argparse, glob, json, os
from datetime import date
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument('--out', default='out/'); ap.add_argument('--method', choices=['total', 'inperson', 'mail'], default='total'); ap.add_argument('--view', choices=['daily', 'running'], default='daily'); a = ap.parse_args()
INK, MUTED, LINE = '#3A332F', '#6B6558', '#D9D4C7'; COL = ('#1F5C6F', '#8A1538', '#F0AC42')
plt.rcParams['font.family'] = 'DejaVu Sans'
days = [json.load(open(f)) for f in sorted(glob.glob('data/daily/day-*.json'))]
cum = []
for d in days:
    hm = d['history_method']; n = d['history_nonprimary']; ms = ['inperson', 'mail'] if a.method == 'total' else [a.method]
    e = [sum(hm[m][i] for m in ms) for i in range(7)]; red = sum(n[m][2] for m in ms)
    cum.append((e[5] + e[6], e[2] + e[3], sum(n[m][1] for m in ms) + red, red))
daily = [tuple(max(0, c - p) for c, p in zip(cum[i][:3], cum[i-1][:3] if i else (0, 0, 0))) for i in range(len(cum))]
if a.view == 'running': daily = [c[:3] for c in cum]      # running totals through each day instead of each day's new voters
last = days[-1]; t = date.fromisoformat(last['snapshot_date']); tot = sum(cum[-1][:3])
share = [v / tot * 100 for v in cum[-1][:3]]

W, H = 7.28, 7.0
fig = plt.figure(figsize=(W, H), dpi=200); fig.patch.set_facecolor('white')
TITLE = ({'total': "Who's voting, day by day", 'inperson': "Who's voting in person, day by day", 'mail': "Who's returning mail ballots, by day"} if a.view == 'daily' else {'total': "Running total by primary history", 'inperson': "Running total, in person", 'mail': "Running total, mail ballots"})[a.method]
WHO = {'total': 'Early voters', 'inperson': 'In-person early voters', 'mail': 'Mail ballots returned'}[a.method]
fig.text(0.35/W, 1-0.50/H, TITLE, fontsize=21, fontweight='bold', color=INK, va='top')
fig.text(0.35/W, 1-0.98/H, f"{WHO} {'each day' if a.view == 'daily' else 'so far'} by primary history  \u00b7  through {t.strftime('%b')} {t.day}", fontsize=11, color=MUTED, va='top')
ax = fig.add_axes([0.95/W, 2.3/H, 5.95/W, 3.05/H])
labels = ['Democratic-leaning', 'Republican-leaning', 'No primary history']
for i, (dd, day) in enumerate(zip(daily, days)):
    x = day['day']; bottom = 0
    for k in range(3):
        ax.bar(x, dd[k], bottom=bottom, width=0.68, color=COL[k], label=labels[k] if i == 0 else None)
        if dd[k] > max(map(sum, daily)) * 0.10:   # count (k) on top, share of that day's voters underneath
            ax.text(x, bottom + dd[k] / 2, f"{dd[k] / 1000:.1f}k\n{dd[k] / sum(dd) * 100:.0f}%", ha='center', va='center', fontsize=7, fontweight='bold', linespacing=1.15, color=INK if k == 2 else 'white')
        bottom += dd[k]
    ax.text(x, bottom + max(map(sum, daily)) * 0.02, f"{bottom:,}", ha='center', va='bottom', fontsize=8, fontweight='bold', color=INK)
ymax = max(map(sum, daily)) * 1.15
ax.set_xlim(0.4, 12.6); ax.set_ylim(0, ymax); ax.set_xticks(range(1, 13))
ax.set_xticklabels([f"{d}" for d in range(1, 13)], fontsize=9, color=MUTED)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}")); ax.tick_params(axis='y', labelsize=8.5, colors=MUTED, length=0); ax.tick_params(axis='x', length=0)
ax.grid(axis='y', color=LINE, lw=0.8); ax.set_axisbelow(True)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xlabel('Day of early voting', fontsize=9.5, color=INK, labelpad=5)
fig.legend(loc='upper left', bbox_to_anchor=(0.35/W, 1-1.28/H), ncol=3, frameon=False, fontsize=9, handlelength=1.1, columnspacing=1.6)
fig.text(0.35/W, 1.80/H, f"So far:  {cum[-1][0]:,} Democratic-leaning ({share[0]:.0f}%)  \u00b7  {cum[-1][1]:,} Republican-leaning ({share[1]:.0f}%)", fontsize=9, fontweight='bold', color=INK, va='center')
fig.text(0.35/W, 1.60/H, f"{cum[-1][2]:,} no primary history ({share[2]:.0f}%)  \u00b7  {tot:,} {'early voters' if a.method == 'total' else ('in-person early voters' if a.method == 'inperson' else 'mail ballots')} in all", fontsize=9, fontweight='bold', color=INK, va='center')
for i, line in enumerate(["Democratic-leaning = mostly voted in Democratic primaries since 2016; Republican-leaning likewise.",
                          {"total": "Day 1 includes mail ballots returned before early voting opened. No primary history includes the",
                           "inperson": "In-person early voters only; mail ballots are not included. No primary history includes the",
                           "mail": "Mail ballots only: Day 1 is every ballot returned through Oct 19; later days are the net change. No primary history"}[a.method],
                          f"{'' if a.method != 'mail' else 'includes '}{cum[-1][3] / tot * 100:.1f}% of {'early voters' if a.method != 'mail' else 'ballots'} whose IDs are redacted. Past primary choices, not how anyone votes in November."]):
    fig.text(0.35/W, (1.34 - 0.2 * i)/H, line, fontsize=7.2, color=MUTED, va='center')
lg = fig.add_axes([0.35/W, 0.10/H, 1.0/W, 0.27/H]); lg.imshow(Image.open('assets/logo.png').convert('RGBA')); lg.axis('off')
fig.text(1.5/W, 0.235/H, 'Tarrant County Early Voting Tracker', fontsize=9.5, color=INK, va='center', fontweight='bold')
fig.text((W-0.35)/W, 0.235/H, 'cesdatatx.com', fontsize=10.5, color=INK, va='center', ha='right', fontweight='bold')
os.makedirs(a.out, exist_ok=True); path = os.path.join(a.out, f"voters_by_day{'' if a.method == 'total' else '_' + a.method}{'_running' if a.view == 'running' else ''}_day-{last['day']:02d}_{last['snapshot_date']}.png"); fig.savefig(path)
print(path, "| shares so far:", [f"{s:.1f}%" for s in share])
