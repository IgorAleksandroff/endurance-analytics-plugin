# Endurance Analytics plugin

<!-- listing:start (scripts/sync-listing.py) -->
Endurance Analytics plans trail and ultra races: the season, the race day and the review afterwards.

Season: search the public race catalog by name, country, month, terrain and open registration, rank and compare races, find races like one you loved, and keep your season plan. Every change can be undone for 90 days.

Race day: arrival at every aid station and the margin to each cut-off for your target time or performance index, with gels, food, drink and salt per segment. Save the plan with your own fuel and fine-tune it on the race page.

Course: flat-equivalent distance, key climbs and descents and where they fall, technical sections, where poles pay off, quad damage and the weather at the course itself. Practical questions are answered from the race FAQ with source and date.

Review: results, any athlete checkpoint by checkpoint, and how the field went. Upload a GPX for the same analysis. Profiles, maps and results come as the website's charts right in the chat.

Limitations: no training data, heart-rate zones or readiness here. Deleting races or plans, settings and payments happen on the website. A GPX upload uses a race slot, a new race plan a race-plan slot. Numbers come only from the platform; course insights are for a reference runner. Your own data needs an Endurance Analytics account.

Official listings: [ChatGPT](https://chatgpt.com/plugins/plugin_asdk_app_6ae6286b0b008191850171a45207127f) · [Claude](https://claude.ai/directory/endurance-analytics)
<!-- listing:end -->

One plugin for ChatGPT and Claude: the same folder `plugins/endurance`, the
same skills and the same remote MCP server `https://api.endurance-analytics.com/mcp`.
You need an Endurance Analytics account. Sign up at
[endurance-analytics.com](https://endurance-analytics.com).

## ChatGPT

Install from the ChatGPT directory:
[Endurance Analytics in ChatGPT](https://chatgpt.com/plugins/plugin_asdk_app_6ae6286b0b008191850171a45207127f).
Select **Connect** and sign in to Endurance Analytics in the window that opens.

## Claude

On claude.ai and in Claude Desktop, add the connector from the directory:
[Endurance Analytics in Claude](https://claude.ai/directory/endurance-analytics).
Select **Connect** and sign in to Endurance Analytics. The connector gives the
tools; the skills of this plugin come with Claude Code below.

## Claude Code

```
/plugin marketplace add IgorAleksandroff/endurance-analytics-plugin
/plugin install endurance-analytics@endurance-analytics
```

Then run `/mcp` and follow the browser sign-in. You approve what the assistant
may access on a consent screen; the token refreshes itself afterwards.

## Scripts

For automation without OAuth, create a personal token in your profile settings
under **AI agent access** and add the server directly:

```bash
claude mcp add --transport http endurance https://api.endurance-analytics.com/mcp \
  --header "Authorization: Bearer $ENDURANCE_PAT"
```

The plugin ships no secrets: its MCP configuration contains only the endpoint.

## Repository layout

```
listing.json                        THE listing text: name, descriptions, prompts, release notes, data use
agent-surface.json                  The server's tool list, copied from the backend's docs/api/agent_surface.json
connector-listing.md                Generated: fields to paste into the Claude connector listing
.claude-plugin/marketplace.json     Generated: Claude Code marketplace
plugins/endurance/                  The plugin, one folder for both directories
  README.md                         Generated: the listing page in Anthropic's directory
  plugin.json, mcp.json, assets/    OpenAI manifest (shared fields generated) and MCP config
  .claude-plugin/plugin.json        Generated: Claude manifest
  .mcp.json                         Claude MCP config (same URL; the validator checks it)
  skills/                           Skills shared by both
scripts/
  sync-listing.py                   Writes every generated file; --check fails when one is stale
  validate-openai.py                Checks the OpenAI package and the tool sync
  build.sh                          sync --check, validators, then dist/endurance-{openai,claude}-<version>.zip
review-notes.md                     OpenAI review material (not in the ZIP)
```

```bash
scripts/sync-listing.py                      # after editing listing.json
scripts/build.sh                             # release build of both packages
scripts/build.sh --allow-placeholder         # draft, while the demo video URL is a placeholder
```

## Keeping the plugin in sync with the server

The MCP server lives in the backend (`internal/mcpserver`). Its tool list is
exported to `docs/api/agent_surface.json` by
`go test ./internal/mcpserver -run TestAgentSurfaceDump -update-agent-surface`
(the test fails while the export is stale). Whenever a tool is added, removed or
renamed, or its inputs, outputs, annotations or limits change:

1. `scripts/sync-listing.py --surface-from <back>/docs/api/agent_surface.json`.
2. The validator then names what is missing: every tool in `skills/*/SKILL.md`
   and in the `review-notes.md` annotation table with the server's hints.
3. `listing.json`: description, prompts and release notes if the change is
   visible to the athlete; bump `version`; run `scripts/sync-listing.py`.
4. `plugin.json` → `review.test_cases` if a case changes; a case must still run
   on a fresh reviewer account.
5. `scripts/build.sh`, commit and push: the Claude directory picks up the push.
6. ChatGPT: upload `dist/endurance-openai-<version>.zip` as a new version in the
   plugin portal. Tool changes reach ChatGPT through the daily rescan, new tools
   stay hidden until approved.
7. Claude connector: paste `connector-listing.md` into the listing when its
   tagline, description or tool names changed.
8. The website's agent texts (`/connect`, `agents.md`, `llms.txt`, server card):
   `npm run sync:agent-surface` in the front, whose tests check them against the
   same export and `listing.json`.

Data obtained from Strava (trainings, curves, zones, readiness) must never be
exposed through the tools or described in the skills.

## Documentation and privacy

- Setup guide: <https://endurance-analytics.com/en/connect>
- Agent-facing reference: <https://endurance-analytics.com/agents.md>
- Privacy policy: <https://endurance-analytics.com/en/privacy>
- Terms: <https://endurance-analytics.com/en/terms>

## License

MIT
