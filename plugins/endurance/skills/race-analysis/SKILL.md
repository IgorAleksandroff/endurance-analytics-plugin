---
name: race-analysis
description: Use when the athlete asks about a race course — how hard it is, where the climbs are, how it compares with another race, or what to expect on the day. Covers reading terrain summaries, gradient bands and technicality from Endurance Analytics.
---

# Reading a race course

## Get the data first

A race is identified by **slug plus season**. The same slug exists in several
seasons, so a slug alone resolves the wrong year. Use `search_races` to get both,
then `get_race` for the headline numbers and `get_race_terrain_summary` for the
terrain. For the athlete's own uploaded courses, `get_my_race` returns the same
terrain shape.

## What the numbers mean

**Distance and elevation** are the advertised figures. They are the worst
predictor of difficulty on their own — a 40 km race with 3000 m of climbing is a
different sport from a flat 40 km.

**Flat-equivalent distance (`flat_km`)** is the honest comparison unit: how far
the course "feels" on flat ground. Two courses with the same `flat_km` demand
roughly the same work. Lead with it whenever the athlete is comparing races or
sizing an effort.

**Technicality (TDI)**, 0 to 5, describes footing, not steepness: 0 is smooth
road, 1–2 is runnable trail, 3+ means rocks, roots or scree that force a slower
pace regardless of gradient. A steep smooth fire road and a flat boulder field
are both hard, for different reasons — say which one you mean.

**The breakdown** splits the course by steepness band: how many kilometres and
what share are uphill, downhill and flat, one row per gradient bucket. Shares sum
to the whole course.

**The superlatives** are the actual hardest features — the longest climb, the
steepest climb, the longest and steepest descents — with their real gradients and
their position along the course (`start_km`, `end_km`). When the athlete asks
"what's the hardest part", answer from here, not from the bands: a band says
"12 km at 10–15%", a superlative says "a 7.4 km climb at 9% starting at km 31".

## Interpreting well

- **Position matters as much as size.** A 700 m climb at km 8 is a warm-up; the
  same climb at km 62 decides the race. Always mention where a feature sits.
- **Descents are not free.** Long steep descents cost quadriceps, and their price
  arrives later, on the next climb. Do not treat downhill kilometres as recovery.
- **Say what you do not know.** If technicality is missing or `enrichment.status`
  is `pending`, say the footing is unknown rather than assuming it is runnable.
- **Never estimate a finish time from the course alone.** Pair it with the
  athlete's own curves (`get_my_curves`) and current form
  (`get_my_athlete_state`), and state the uncertainty band you were given.

## Comparing two races

Compare `flat_km` first, then the shape: total climbing, the size and position of
the biggest climbs, and technicality. Two races with equal distance and equal
climbing can still differ sharply if one stacks its climbing into three long
ascents and the other spreads it over forty rollers.
