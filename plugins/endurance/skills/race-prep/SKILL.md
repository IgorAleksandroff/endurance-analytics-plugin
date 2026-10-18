---
name: race-prep
description: Use when the athlete wants to prepare for a specific race, asks how hard a course is or where its climbs and descents are, wants pole or weather advice for race day, or wants to compare two races. Builds a race-day plan from Endurance Analytics course terrain, course segments, quad damage, pole advice, weather and results.
---

# Preparing for a race

The goal is a race-day plan built only from what the platform computed for the
course. Interpret the numbers; never invent them. If the athlete asks for one
thing (only poles, only weather), answer that and skip the rest.

## Gather the data

1. `search_races` with the race or event name. The catalog stores the
   organiser's own name: translate a name from another language to the local or
   English form (Monte Bianco → Mont Blanc) and pass the country as `nation`.
   A race is identified by slug **and** season; the same slug exists in several
   seasons. If several races or seasons match, pick the one the athlete means
   or ask.
2. `get_race`: date, start time, time limit, distance, elevation,
   flat-equivalent distance, whether it has a track and results.
3. `get_race_terrain_summary`: steepness breakdown, longest and steepest
   climbs and descents with positions, highest point, named cols and peaks,
   surface mix and technical spans.
4. `get_race_course_segments` with `min_length_m` around 500 to name the
   features worth planning around, in course order. Without the filter a long
   race returns hundreds of segments.
5. `get_race_quad_damage`, `get_race_pole_advice`, `get_race_weather`.
6. `get_race_results` for context only: winning and typical times, finishers
   and DNFs. Results show what others ran; they say nothing about this athlete.
7. `get_race_report` when the athlete wants a ready-to-share write-up or an
   aid-station table. Pass it through rather than rewriting its numbers.

A race without a course track has no terrain, segments, poles, quad damage or
weather. Say so; do not fill the gap with a regional description or forecast.

`get_my_profile` and `get_my_performance_index` are context, not inputs to a
prediction. The one place to use the index is the `pi` parameter of
`get_race_weather`, which times the course for the athlete: pass the `pi` field
of `get_my_profile` as is, whatever the athlete's gender. An index computed
from races imported from Strava is withheld (null, with
`performance_index_withheld`); then omit `pi`, say the course is timed for a
reference runner, and give the athlete `performance_index_web_url` to see
their index on the website. Never estimate the index yourself.

For "how did I run X", read `basis.catalog_finishes` of
`get_my_performance_index`: the athlete's own catalog finishes with time and
place; pass `race_slug` and `season` to `get_race` or `get_race_results`.
`basis.my_races` lists the own stored races the manual index is built on
(open one with `get_my_race`). Races imported from Strava never appear there.

## Reading the course

- **Flat-equivalent distance (`flat_km`)** is how far the course "feels" on
  flat ground. Lead with it when sizing an effort or comparing races; raw
  distance and gain alone mislead.
- **Technicality (TDI, 0 to 5)** is footing, not steepness: 0 is smooth road,
  1 to 2 runnable trail, 3 and above rocks, roots or scree. Say which kind of
  hard a section is. If surface status is not `ready`, footing is unknown.
- **Superlatives** answer "what is the hardest part": "a 4.8 km climb at 15 %
  from km 12.5" beats "12 km at 10 to 15 %".
- **Position matters as much as size.** The same climb at km 8 and at km 62
  are different problems. Always give the kilometre.
- **Descents are not recovery.** Long steep descents cost the quads, and the
  bill arrives on later climbs.

## Descents and quad damage

`get_race_quad_damage` rates how much the descents damage the quads of a
typical runner: a level (none to extreme) with a 0 to 100 index, the share of
damage in the first half, and the descents that matter in course order. Lead
with the level, then the critical descents with their kilometres. `advice`
says how to run each one: `control` means hold back because much of the race
is still ahead, `target` means run it at the planned effort, and `free`,
`freeLong` or `freeVeryLong` mark the final descent home, where letting go is
safe (the long variants are long enough to pace with care). `zones` give the
kilometre where the last control descent ends and where the free finishing
descent starts. It is not a personal prediction: training, sex and actual
speed change the real damage.

## Poles

`get_race_pole_advice` comes from course geometry alone, so it is the same for
every runner. Lead with `verdict.level`, then walk the `stints`: where poles
come out and go away, with the elevation there. Use `spans` to explain any
stretch: `action` is what to do, `cat` is why. A short climb marked `stow` is
not worth deploying for. Braking with poles is only recommended on long ultras.

## Weather at the course

`get_race_weather` is about the course itself; temperatures are corrected for
the elevation of each point. What is present tells where the race sits in time:

- **Climatology**, always: typical start and summit temperatures with the
  p10 to p90 spread, rain and snow probability, wind, UV, daylight, minutes
  in the dark, and the year-by-year record of the date.
- **Forecast**, within about ten days of the race, along the course.
- **Actual**, for an edition that already happened.

Answer packing questions from the spread, not the median: 8 to 14 °C is one
outfit, 2 to 26 °C means preparing for both ends. `ci_low` to `ci_high` only
says how solid the average is. A rain probability of 0.45 means nearly half
the editions were wet, not "it will rain". The `corridor` gives conditions
at the hour a runner passes each point; use it for "how cold is the ridge at
night". If `start_assumed` is true, every time is an estimate.

Volunteer two things: a head torch when there are dark minutes (slower runners
get more darkness), and sun protection when UV at altitude is above 6.

## The race-day plan

Use these sections, keep each short, and cite kilometres:

1. **The course in brief**: distance, climbing, flat-equivalent distance,
   highest point and where, layout, footing.
2. **Key sections** in course order: the climbs and descents that shape the
   day, with named cols where the terrain summary gives them.
3. **Descent management**: quad-damage level, the descents to hold back on,
   where it is safe to let go.
4. **Poles**: verdict and where they come out and go away.
5. **Weather and kit**: the range to dress for, rain odds, dark time and
   head torch, sun protection.
6. **Unknowns**: anything the tools did not return.

## Comparing two races

Run the same gathering for both. Compare `flat_km` first, then the shape:
total climbing, size and position of the biggest climbs, technicality, the
quad-damage level and the pole verdict, then the typical weather. Equal
distance and climbing can still hide very different races: three long climbs
are not forty rollers.
