---
name: training-review
description: Use when the athlete asks about their own training — recent volume, whether they are fit or tired, what their curves say, which zones to run in, or how their form is trending in Endurance Analytics.
---

# Reading an athlete's training data

## Where the answers live

- `get_my_trainings` — the journal, newest first, filterable by date range.
- `get_my_training` — one session in detail.
- `get_my_athlete_state` — current form: fitness and fatigue axes, downhill
  resilience, load balance.
- `get_my_curves` — `kind=pace` (critical pace and predictions by duration),
  `kind=hr` (pace↔heart-rate), `kind=zones` (training zones).
- `get_my_performance_index` — how the athlete's level moved over time.

## Rules that keep answers honest

**Road and trail are separate models.** A trail pace and a road pace are not the
same measurement, and heart rate is not comparable across them either. Every
curve call takes a surface; always report which one you read.

**Excluded trainings are excluded on purpose** — bad heart-rate data, GPS
problems, or the athlete's own decision. They appear in the journal so the
athlete can see them, but they are not evidence of fitness. Never cite one when
explaining current form.

**Confidence bands are real.** Where a value carries P10/P50/P90, P50 is the
estimate and the spread is genuine uncertainty. Report the spread when it is
wide, and never present P50 as a measurement.

**Missing means unknown.** No flat-km, no technicality, no current form — say so.
A curve can be absent simply because the athlete has not yet run enough
qualifying efforts on that surface; that is a fact worth telling them, not a
gap to paper over.

**Compare with flat-equivalent distance, not raw distance.** `flat_km` and the
average flat pace are what make a hilly week and a flat week comparable.

## Talking about form

The current-form axes describe accumulated fitness against accumulated fatigue.
Read them as a state, not a verdict: high fatigue right after a big block is
expected, not a problem. What matters is the direction and the athlete's plan.

Downhill resilience is tracked separately because it fails separately — an
athlete can be aerobically ready for a race and still be wrecked by its descents.

If the athlete has no state yet, the tool says so. That means too little
processed history, not zero fitness.

## What you cannot do here

You cannot delete or edit trainings, change settings, or exclude a session. Those
live on the website. When the athlete wants one of them, hand them the link from
the tool response rather than describing a workaround.
