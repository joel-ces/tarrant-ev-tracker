#!/usr/bin/env python3
"""Returning-voters graphic: who is voting early in 2026 and how they voted in 2022 and 2024. Run from the repo root:
    python3 scripts/make_returning_graphic.py [--out out/]     (reads data/returning/day-*.json and data/daily/day-*.json; totals only)"""
import argparse, glob, json, os
from datetime import date
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument('--out', default='out/'); a = ap.parse_args()
INK, MUTED, AMBER, CHAR, LINE, PAPER, GRAY = '#3A332F', '#6B6558', '#F0AC42', '#504846', '#D9D4C7', '#F7F5EF', '#8C8279'
plt.rcParams['font.family'] = 'DejaVu Sans'
R = [json.load(open(f)) for f in sorted(glob.glob('data/returning/day-*.json'))]; L = R[-1]
days = {json.load(open(f))['day']: json.load(open(f)) for f in sorted(glob.glob('data/daily/day-*.json'))}; t = date.fromisoformat(days[L['day']]['snapshot_date'])
n = L['early_voters_matched']; c = L['composition']; rt = L['retention_2026']; pc = lambda x: x / n * 100
one = n - c['both_years'] - c['neither_year']

W, H = 7.28, 11.7
fig = plt.figure(figsize=(W, H), dpi=200); fig.patch.set_facecolor('white'); top = lambda y: 1 - y / H
fig.text(0.35 / W, top(0.50), "Who's coming back", fontsize=21, fontweight='bold', color=INK, va='top')
fig.text(0.35 / W, top(0.98), f"How 2026's early voters voted in 2022 and 2024  \u00b7  {n:,} matched voters through {t.strftime('%b')} {t.day}", fontsize=9.6, color=MUTED, va='top')
bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, W); bg.set_ylim(0, H); bg.axis('off'); bg.patch.set_alpha(0)
tiles = [(f"{pc(c['voted_early_2024']):.0f}%", "voted early in 2024"), (f"{pc(c['both_years']):.0f}%", "voted in both 2022 and 2024"), (f"{pc(c['neither_year']):.0f}%", "voted in neither year")]
tw, gap = 2.12, 0.14
for i, (big, lab) in enumerate(tiles):
    x = 0.35 + i * (tw + gap); y = H - 2.45
    bg.add_patch(FancyBboxPatch((x, y), tw, 0.95, boxstyle="round,pad=0,rounding_size=0.06", facecolor=PAPER, edgecolor=LINE, lw=0.8)); bg.add_patch(plt.Rectangle((x, y), 0.08, 0.95, facecolor=AMBER, edgecolor='none'))
    bg.text(x + 0.22, y + 0.58, big, fontsize=24, fontweight='bold', color=INK, va='center'); bg.text(x + 0.22, y + 0.22, lab, fontsize=8.4, color=MUTED, va='center')

fig.text(0.35 / W, top(2.85), "How they voted before", fontsize=10, fontweight='bold', color=INK, va='center')
ax = fig.add_axes([1.75 / W, top(4.35), 5.1 / W, 1.25 / H]); ax.set_xlim(0, 100); ax.set_ylim(-0.5, 2.5); ax.axis('off')
rows = [("In 2024", [c['voted_early_2024'], c['election_day_2024'], c['no_2024_vote']], [CHAR, AMBER, LINE]), ("In 2022", [c['voted_early_2022'], c['election_day_2022'], c['no_2022_vote']], [CHAR, AMBER, LINE]),
        ("2022 and 2024", [c['both_years'], one, c['neither_year']], [CHAR, GRAY, AMBER])]
for yi, (name, v, cols) in enumerate(rows[::-1]):
    left = 0
    for k in range(3):
        w = v[k] / n * 100; ax.barh(yi, w, left=left, color=cols[k], height=0.62)
        if w >= 5: ax.text(left + w / 2, yi, f"{w:.0f}%", ha='center', va='center', fontsize=8.6, fontweight='bold', color='white' if (cols[k] in (CHAR, GRAY)) else INK)
        left += w
    ax.text(-0.012, yi, name, ha='right', va='center', fontsize=8.4, color=INK, transform=ax.get_yaxis_transform())
fig.text(1.75 / W, top(4.5), "Dark: voted early (2022, 2024) / both years.   Amber: Election Day / neither year.   Gray: did not vote / one year.", fontsize=6.9, color=MUTED, va='center')

fig.text(0.35 / W, top(4.95), "Share of past voters who have voted early in 2026, by day", fontsize=10, fontweight='bold', color=INK, va='center')
lx = fig.add_axes([0.85 / W, top(7.3), 5.2 / W, 2.05 / H])
dd = [r['day'] for r in R]
for key, col, lab, ls in (('early_2024', CHAR, '2024 early voters', '-'), ('early_2022', AMBER, '2022 early voters', '-'), ('election_day_2024', GRAY, '2024 Election Day voters', (0, (4, 3)))):
    ys = [r['retention_2026'][key]['share'] for r in R]; lx.plot(dd, ys, color=col, lw=2.4, ls=ls, marker='o', ms=4.5)
    lx.text(dd[-1] + 0.2, ys[-1], f"{ys[-1]:.1f}%\n{lab}", color='#B9801E' if col == AMBER else col, fontsize=7.6, fontweight='bold', va='center', linespacing=1.15)
import math
ymax = math.ceil((max(r['retention_2026'][k]['share'] for r in R for k in ('early_2024', 'early_2022', 'election_day_2024')) + 8) / 20) * 20   # scale the axis to the data
lx.set_xlim(0.7, 12.6); lx.set_ylim(0, ymax); lx.set_xticks(range(1, 13)); lx.set_yticks(list(range(0, ymax + 1, 20))); lx.set_yticklabels([f'{v}%' for v in range(0, ymax + 1, 20)])
lx.tick_params(axis='both', labelsize=8, colors=MUTED, length=0); lx.grid(axis='y', color=LINE, lw=0.8); lx.set_axisbelow(True)
for s in lx.spines.values(): s.set_visible(False)
lx.set_xlabel('Day of early voting', fontsize=8.2, color=INK, labelpad=2)

fig.text(0.35 / W, top(7.72), "Share of 2024's in-person early voters who have voted in 2026,", fontsize=10, fontweight='bold', color=INK, va='center')
fig.text(0.35 / W, top(7.95), "by when they voted in 2024", fontsize=10, fontweight='bold', color=INK, va='center')
bx = fig.add_axes([0.85 / W, top(10.15), 5.9 / W, 1.95 / H]); bd = L['by_past_day']
for i, d in enumerate(bd):
    if d['in_person_2024']['pool'] > 0:
        v = d['in_person_2024']['share']; bx.bar(i, v, width=0.66, color=CHAR); bx.text(i, v + 1.5, f"{v:.0f}%", ha='center', va='bottom', fontsize=8, fontweight='bold', color=INK)
    else: bx.text(i, 3, "no\nvoting", ha='center', va='bottom', fontsize=6.6, color=MUTED, linespacing=1.1)
bx.set_xticks(range(len(bd))); bx.set_xticklabels([str(d['days_out']) for d in bd], fontsize=8, color=MUTED); ymb = math.ceil((max(d['in_person_2024']['share'] for d in bd) + 10) / 20) * 20; bx.set_ylim(0, ymb); bx.set_yticks(list(range(0, ymb + 1, 20))); bx.set_yticklabels([f'{v}%' for v in range(0, ymb + 1, 20)])
bx.tick_params(length=0, labelsize=8, colors=MUTED); bx.grid(axis='y', color=LINE, lw=0.8); bx.set_axisbelow(True)
for s in bx.spines.values(): s.set_visible(False)
bx.set_xlabel('Days before Election Day when they voted in person in 2024', fontsize=8.2, color=INK, labelpad=2)
for i, line in enumerate(["Early = in-person early voting or a mail ballot. Matched by voter ID to the 2022 and 2024 rosters. 'Did not vote' includes new registrants.",
                          "Past voters who are no longer registered in Tarrant are left out. 2026 early voting is only partly done, so people who voted late in 2024 have had",
                          "less time to vote again. 2024 was a presidential year, so it is not a like-for-like benchmark for 2026."]):
    fig.text(0.35 / W, top(10.85 + 0.19 * i), line, fontsize=6.6, color=MUTED, va='center')
lg = fig.add_axes([0.35 / W, 0.10 / H, 1.0 / W, 0.27 / H]); lg.imshow(Image.open('assets/logo.png').convert('RGBA')); lg.axis('off')
fig.text(1.5 / W, 0.235 / H, 'Tarrant County Early Voting Tracker', fontsize=9.5, color=INK, va='center', fontweight='bold'); fig.text((W - 0.35) / W, 0.235 / H, 'cesdatatx.com', fontsize=10.5, color=INK, va='center', ha='right', fontweight='bold')
os.makedirs(a.out, exist_ok=True); path = os.path.join(a.out, f"returning_voters_day-{L['day']:02d}_{days[L['day']]['snapshot_date']}.png"); fig.savefig(path)
print(path, f"| {n:,} matched | early 2024 {pc(c['voted_early_2024']):.1f}% | both {pc(c['both_years']):.1f}% | neither {pc(c['neither_year']):.1f}%")
