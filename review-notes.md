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
| `get_my_wishlist` | true | false | false | Reads the catalog races the athlete saved. |
| `search_races` | true | false | false | Searches the platform's own race catalog. Bounded dataset, no web search. |
| `get_race` | true | false | false | Reads one race from the platform's catalog. |
| `get_race_results` | true | false | false | Reads stored results of a catalog race. No athlete ids or photos are returned. |
| `get_race_splits` | true | false | false | Reads stored checkpoint splits of a catalog race: the same public results data as `get_race_results`, resolved by athlete name fragment — cumulative arrival time, position and segment time per checkpoint. Nothing beyond what the site's results page shows. |
| `get_race_terrain_summary` | true | false | false | Reads terrain the platform computed from the stored course track. |
| `get_race_pole_advice` | true | false | false | Computes pole advice from the stored course geometry. Nothing is written. |
| `get_race_quad_damage` | true | false | false | Computes descent damage from the stored course geometry. Nothing is written. |
| `get_race_course_segments` | true | false | false | Reads the stored gradient segmentation of a course. |
| `get_race_weather` | true | false | false | Reads weather the platform computed for the stored course: climatology, forecast and observed data from its fixed providers for that course. Not open-ended access; nothing is written. |
| `get_race_report` | true | false | false | Returns a Markdown report rendered by the platform from its own catalog data. |
| `save_gpx_as_race` | false | false | true | Creates a new race in the athlete's account and uses one race slot. Never overwrites or deletes existing data (deletion is website-only). Open-world because it downloads a GPX file from an arbitrary https URL the user supplies. |

## Test cases

They are also in `plugins/endurance/plugin.json` (`review.test_cases`) and are
imported from the ZIP. Run them with the reviewer account before submitting.
Positive 5 creates a race; run negative 2 after it so the race exists.

### Positive

| # | Prompt | Tools | Expected |
| --- | --- | --- | --- |
| 1 | Which races are part of HOKA UTMB Mont-Blanc 2026? Give the distance and elevation gain of each. | `search_races` | The event's 2026 races (UTMB about 174 km / 9700 m, CCC about 108 km, OCC about 60 km, plus TDS, MCC, YCC, ETC) with catalog values only. |
| 2 | How hard is the OCC 2026 course? Where are the biggest climbs, and which descents will hurt my quads most? | `search_races`, `get_race_terrain_summary`, `get_race_quad_damage` | About 59.5 km / 3400 m, point to point, highest point near km 34, longest climb about 4.8 km at about 15 % ending near km 17; quad damage moderate with critical descents and their kilometres; framed as typical runner, not personal. |
| 3 | Should I carry poles at the CCC 2026, and where on the course should I use them? | `search_races`, `get_race_pole_advice` | Verdict high; stints in course order with kilometre and elevation; braking spots; same advice for every runner. |
| 4 | What weather should I expect at the CCC (UTMB Mont-Blanc)? What should I pack? | `search_races`, `get_race_weather` | Course climatology (start and summit temperatures with spread, rain probability, wind, UV, dark time), actual weather of the past edition or the forecast when close; concrete kit advice. |
| 5 | Save this GPX as my race named 'OCC recon' and tell me how hard it is: https://api.endurance-analytics.com/public/trail/races/utmb-occ/track.gpx?season=2026 | `save_gpx_as_race` | One new race; about 59.5 km / 3400 m, flat-equivalent distance, biggest climbs with positions; says a slot was used, TDI defaulted to 1, surface may be pending, deletion is on the website. |
| 6 | Trace Francesco Puppi's CCC 2025 checkpoint by checkpoint: where did he lead, and where was the race close? | `search_races`, `get_race_splits` | Splits in course order with values only from the tool: arrival time and position at each checkpoint, segment time with rank and gap, where the gap to the field grew or shrank (that is where the race was decided). Puppi won in about 10:06; no invented intermediate times. |

Values marked "at the time of writing" were read from the live server on
2026-10-17. The GPX link in case 5 is public and was checked with `curl -I`
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
> courses (needed for positive test 5). The test account has free race slots
> and needs no MFA, email codes or magic links.
>
> Login URL: https://endurance-analytics.com/en/auth/signin
> Email: (entered in the portal form)
> Password: (entered in the portal form)

## Portal checklist

- [ ] Organization: Apps Management Write access and verified developer identity.
- [ ] Record the demo walkthrough (all 5 positive and 3 negative cases), put its URL in `review.demo_recording_url`, rebuild **without** `--allow-placeholder`.
- [ ] Upload `dist/endurance-openai-<version>.zip` through **With MCP**; resolve metadata and skill findings (skill scans can take up to 2 hours).
- [ ] MCPs → Connect `https://api.endurance-analytics.com/mcp`; authentication comes from `mcp.json` (OAuth, DCR).
- [ ] Domain verification: serve the exact portal token as plain text at `https://api.endurance-analytics.com/.well-known/openai-apps-challenge` (currently 404), then **Verify Domain**.
- [ ] OAuth: DCR accepts the ChatGPT redirect URIs (`https://chatgpt.com/connector/oauth/{callback_id}` and `https://chatgpt.com/connector_platform_oauth_redirect`); registered clients do not expire while connected.
- [ ] Tool scan passes; every tool has the three annotations set explicitly with the justifications above.
- [ ] Reviewer account created, "App reviewer access" sign-in works, credentials entered in **Review details**.
- [ ] Listing URLs reachable: website, `/en/contact`, `/en/privacy`, `/en/terms`.
- [ ] Optional, not supported yet: Enterprise workspace domain restrictions need OIDC (`openid` and `email` scopes, UserInfo with `email_verified`).
- [ ] Submit for review with the policy attestations; publish after approval; add the directory link to `README.md`.
