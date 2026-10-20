# OpenAI plugin review notes

Material for the OpenAI plugin portal. Not shipped in the ZIP.

- Package: `dist/endurance-openai-<version>.zip`, built by `scripts/build-openai-zip.sh`.
- MCP server: `https://api.endurance-analytics.com/mcp`, Streamable HTTP, OAuth 2.1 with DCR and PKCE.

## Tool annotations

Every tool must carry explicit `readOnlyHint`, `destructiveHint` and
`openWorldHint` on the server, and the portal asks for a justification of each.

| Tool | readOnly | destructive | openWorld | Justification |
| --- | --- | --- | --- | --- |
| `get_my_profile` | true | false | false | Reads the signed-in athlete's own profile from the Endurance Analytics database. Changes nothing; no access outside the platform. |
| `get_my_performance_index` | true | false | false | Reads the athlete's own performance index history and what it rests on (their catalog finishes, their own selected races) from the platform database. |
| `get_my_races` | true | false | false | Lists the athlete's own stored races with web links. Read only. |
| `get_my_race` | true | false | false | Reads one of the athlete's own races and its stored terrain analysis. |
| `get_my_race_track` | true | false | false | Reads the stored, resampled track of one of the athlete's own races. |
| `get_my_plan` | true | false | false | Reads the athlete's own season plan (races they want, applied for, paid for, ran or skipped) from the platform database. Changes nothing; Strava-imported races are not included. |
| `check_season_plan` | true | false | false | Checks the calendar of the athlete's prioritised races against fixed rules computed by the service; candidates are only simulated, nothing is stored. |
| `search_races` | true | false | false | Searches the platform's own race catalog. Bounded dataset, no web search. |
| `get_race` | true | false | false | Reads one race from the platform's catalog. |
| `get_race_results` | true | false | false | Reads stored results of a catalog race. No athlete ids or photos are returned. |
| `get_race_splits` | true | false | false | Reads stored checkpoint splits of a catalog race: the same public results data as `get_race_results`, resolved by athlete name fragment — cumulative arrival time, position and segment time per checkpoint. Nothing beyond what the site's results page shows. |
| `get_race_terrain_summary` | true | false | false | Reads terrain the platform computed from the stored course track. |
| `get_race_pole_advice` | true | false | false | Computes pole advice from the stored course geometry (a catalog race or the athlete's own course). Nothing is written. |
| `get_race_quad_damage` | true | false | false | Computes descent damage from the stored course geometry (a catalog race or the athlete's own course). Nothing is written. |
| `get_race_course_segments` | true | false | false | Reads the stored gradient segmentation of a course (a catalog race or the athlete's own course). |
| `get_race_weather` | true | false | false | Reads weather the platform computed for the stored course: climatology, forecast and observed data from its fixed providers for that course. Not open-ended access; nothing is written. |
| `get_race_report` | true | false | false | Returns a Markdown report rendered by the platform from its own catalog data. |
| `get_race_insights` | true | false | false | Computes field statistics (finish-time percentiles, drops and cut-off margins per checkpoint) from the stored results and splits of a catalog race. Nothing is written; no athlete ids or photos are returned. |
| `find_similar_races` | true | false | false | Ranks catalog races by similarity of their stored course features to a reference race. Read only, bounded dataset. |
| `compare_races` | true | false | false | Builds a side-by-side table of two or three races from stored catalog data. Read only. |
| `save_gpx_as_race` | false | false | true | Creates a new race in the athlete's account and uses one race slot. Never overwrites or deletes existing data (deletion is website-only). Open-world because it downloads a GPX file from an arbitrary https URL the user supplies. |

## Test cases

They are also in `plugins/endurance/plugin.json` (`review.test_cases`) and are
imported from the ZIP. Run them with the reviewer account before submitting.
The GPX positive case creates a race; run negative 2 after it so the race exists.

### Positive

| # | Prompt | Tools | Expected |
| --- | --- | --- | --- |
| 1 | Which races are part of HOKA UTMB Mont-Blanc 2026? Give the distance and elevation gain of each. | `search_races` | Lists the 2026 races of the event (UTMB about 174 km / 9700 m, CCC about 108 km / 6200 m, OCC about 60 km / 3500 m, plus TDS, MCC, YCC and ETC) with distance and gain exactly as the catalog returns them. No invented values; missing fields are reported as unknown. |
| 2 | How hard is the OCC 2026 course? Where are the biggest climbs, and which descents will hurt my quads most? | `search_races`, `get_race_terrain_summary`, `get_race_quad_damage` | Describes the point-to-point course of about 59.5 km and 3400 m of climbing with its highest point near km 34, names the longest climb (about 4.8 km at about 15% ending near km 17) and the steepest sections with their kilometre positions, then reports the quad-damage level (moderate at the time of writing) and the critical descents in course order with their kilometres. States that the damage figures are for a typical runner, not a personal prediction. |
| 3 | What weather should I expect at the CCC (UTMB Mont-Blanc)? What should I pack? | `search_races`, `get_race_weather` | Reports the climate record of the race date at the course: typical start and summit temperatures with their p10 to p90 spread, rain probability, wind and UV, and time spent in the dark, plus what the weather actually did for an edition that already happened (or the forecast when the race is within about ten days). Turns the spread and the dark time into concrete kit advice such as rain gear and a head torch, without quoting a regional town forecast. |
| 4 | Save this GPX as my race (not a training route) named 'OCC recon' and tell me how hard it is: https://api.endurance-analytics.com/public/trail/races/utmb-occ/track.gpx?season=2026 | `save_gpx_as_race` | Creates one race in the account and reports its terrain from the tool response: about 59.5 km with about 3400 m of climbing, flat-equivalent distance, and the longest and steepest climbs with their positions. Mentions that the upload used one race slot, that technicality was set to the default of 1 rather than measured, that surface data may still be pending, and that deleting the race is done on the website. |
| 5 | Compare OCC 2026, CCC 2026 and TDS 2026: distance, climb, technicality and the longest gap between aid stations. | `search_races`, `compare_races` | Finds the three 2026 races and shows one table with the catalog's values and each difference from the first race. Empty cells are reported as unknown with the reason the tool gives; no invented numbers and no verdict on which race is better for the athlete. |
| 6 | If I finish the CCC 2025 in about 24 hours, how close would I be to the cut-offs, and where do runners drop? | `search_races`, `get_race_insights` | Uses the corridor of finishers near that time: when they reached each checkpoint (median and slow edge) and the margin to the cut-off, with the coverage the tool states. Says the corridor holds finishers only and does not describe the runners who dropped at that pace; no personal prediction. |

Values marked "at the time of writing" were read from the live server on
2026-10-17. The GPX link in case 4 is public and was checked with `curl -I`
(HTTP 200, `application/gpx+xml`).

### Negative

| # | Prompt | Expected |
| --- | --- | --- |
| 1 | Show my Strava trainings from last week and my heart-rate zones. | No tool call to approximate them; explains training data is not available through this integration and points to endurance-analytics.com. |
| 2 | Delete my race 'OCC recon' from Endurance Analytics. | No write or destructive action; may call `get_my_races` and gives the web link to delete it on the website. |
| 3 | Book me a hotel in Chamonix for the last week of August. | Plugin not used; no Endurance Analytics tool called. |

## Reviewer sign-in (template for Review details)

Credentials go only into the portal's **Review details** form, never into this
repository or the ZIP.

> Endurance Analytics uses OAuth. When you connect the plugin, ChatGPT opens
> the Endurance Analytics sign-in page. Below the regular sign-in options,
> select **App reviewer access**, then enter the email and password given in
> this form. Approve the consent screen, including permission to upload GPX
> courses (needed for the GPX positive test). The test account has free race slots
> and needs no MFA, email codes or magic links.
>
> Login URL: https://endurance-analytics.com/en/auth/signin
> Email: (entered in the portal form)
> Password: (entered in the portal form)

## Portal checklist

- [ ] Organization: Apps Management Write access and verified developer identity.
- [ ] Record the demo walkthrough (all 6 positive and 3 negative cases), put its URL in `review.demo_recording_url`, rebuild **without** `--allow-placeholder`.
- [ ] Upload `dist/endurance-openai-<version>.zip` through **With MCP**; resolve metadata and skill findings (skill scans can take up to 2 hours).
- [ ] MCPs → Connect `https://api.endurance-analytics.com/mcp`; authentication comes from `mcp.json` (OAuth, DCR).
- [ ] Domain verification: serve the exact portal token as plain text at `https://api.endurance-analytics.com/.well-known/openai-apps-challenge` (currently 404), then **Verify Domain**.
- [ ] OAuth: DCR accepts the ChatGPT redirect URIs (`https://chatgpt.com/connector/oauth/{callback_id}` and `https://chatgpt.com/connector_platform_oauth_redirect`); registered clients do not expire while connected.
- [ ] Tool scan passes; every tool has the three annotations set explicitly with the justifications above.
- [ ] Reviewer account created, "App reviewer access" sign-in works, credentials entered in **Review details**.
- [ ] Listing URLs reachable: website, `/en/contact`, `/en/privacy`, `/en/terms`.
- [ ] Optional, not supported yet: Enterprise workspace domain restrictions need OIDC (`openid` and `email` scopes, UserInfo with `email_verified`).
- [ ] Submit for review with the policy attestations; publish after approval; add the directory link to `README.md`.
