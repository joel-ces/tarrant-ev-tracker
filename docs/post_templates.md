# Post templates (Substack)

Daily (Tue/Wed/Thu/Sat/Sun): title with the day's total and % of registered; today's numbers (in-person, mail returned to date, total) with
the 2022 same-day comparison; mail return rate vs. the same point in 2022; busiest/quietest locations; who's showing up -- lead with the PLAIN SPLIT (scripts/build_page.py prints it: e.g. '58% D-leaning / 42% R-leaning among early voters with a
primary history vs. 49/51 for all primary voters'), then precinct-lean tilt, then the caveat; days remaining. Attach the daily card (scripts/make_daily_card.py). Link: cesdatatx.com.

Friday and the final weekend: everything above plus --
1. By district: commissioner precinct, Senate, House top lines with turnout %, lean and tilt (from the site's Geographic Breakdown).
2. **Spotlight: Senate District 9** (standing item, requested by the owner). Run `python3 scripts/district_spotlight.py` and report the
   by-day table (early votes, share of county, turnout, early-vote lean/tilt, primary-history gap, Reliable D vs Reliable R rates).
3. Where things stand.
A post is dated by the voting day in that morning's roster (Friday's files cover Thursday).

## Senate District 9 background (verified Oct 2026 from Ballotpedia, KERA/Fort Worth Report, Texas Tribune)
Rehmet (D, incumbent) beat Wambsganss (R) 57.3%-42.7% in the Jan. 31, 2026 special runoff, flipping a seat Trump carried by 17 points in 2024; first Democrat
to hold it in 30+ years. Nov. 2025 first round: Rehmet 47.6%, Wambsganss 35.9%, a third candidate (R) ~16.5%. Both unopposed in the March 2026 primaries.
The Nov. 3 winner serves a full four-year term starting Jan. 12, 2027. Cautions: precinct lean and primary history describe where/how people have voted
before, not how anyone votes in November; Day-1-style early electorates skew habitual; nothing here predicts the result.

Returning voters (from Day 7 on): scripts/voter_matching.py daily updates the private 2026 early-voter file and writes data/returning/day-NN.json; build_page.py loads them into the site's
"Returning voters" section; scripts/make_returning_graphic.py makes the post graphic. Quote the headline as "X% of early voters also voted early in 2024" and the retention of 2024's early voters.
Do NOT present 2022->2024 retention as a benchmark for 2026 (presidential vs midterm) until a 2020 roster (presidential -> midterm 2022) is available.
