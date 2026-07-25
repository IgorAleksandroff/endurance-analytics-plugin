---
name: gpx-courses
description: Use when the athlete wants a GPX course analysed — a track they found online, a route they exported, or a race whose GPX they have. Covers uploading it to Endurance Analytics and handling quota and pending-enrichment cases.
---

# Uploading and analysing a GPX course

## The flow

1. Get the GPX. A direct `https` link is the preferred input — pass it as
   `gpx_url` and the service downloads it. If the athlete already handed you the
   file contents, send `gpx_base64` instead. Exactly one of the two.
2. Call `save_gpx_as_race` with a name the athlete will recognise, and a date if
   they gave one.
3. The response already contains the full terrain analysis: distance, elevation,
   flat-equivalent distance, the breakdown by steepness band, and the longest and
   steepest climbs and descents.

Only direct links to `.gpx` files work. A link to a page *about* a route is not a
GPX; find the download link, or ask the athlete to paste the file.

## This writes to the athlete's account

Uploading stores the course as one of the athlete's races and **consumes one of
their race slots**. Say so before uploading if the athlete only wanted a quick
look — there is no throwaway mode.

You need the upload permission for this. If the token is read-only, the tool says
so; the athlete reconnects granting the upload permission.

## Two cases to handle properly

**Quota exhausted.** The error carries a `help_url`. There is no delete tool on
purpose — hand the athlete that link so they can free a slot themselves, and do
not retry the upload until they say they have.

**Enrichment pending.** Surface and technicality come from map data, fetched
asynchronously, so right after an upload `enrichment.status` is often `pending`.
Everything derived from the elevation profile — distance, climbing, bands,
superlatives — is already final and safe to report. Technicality is not: say it
is still being computed, and call `get_my_race` again in a minute rather than
guessing a TDI. If the status becomes `failed`, report that the map data could
not be matched; the geometry-based numbers still stand.

## Reporting the result

Lead with what the athlete asked. If they asked "how hard is this", give
flat-equivalent distance and the biggest climb with its position, not a dump of
every band. Mention where the hardest section falls in the course — an athlete
plans around km 62, not around a gradient bucket.
