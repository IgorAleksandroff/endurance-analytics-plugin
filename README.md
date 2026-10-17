# Endurance Analytics plugin

Trail race analytics from [Endurance Analytics](https://endurance-analytics.com)
in your AI assistant: prepare for a race from its real course data, and upload
GPX courses to get their terrain analysed.

One package serves ChatGPT and Claude Code. It connects to the remote MCP
server `https://api.endurance-analytics.com/mcp` and adds three skills:
getting started, race preparation and GPX courses.

You need an Endurance Analytics account. Sign up at
[endurance-analytics.com](https://endurance-analytics.com).

## What it can do

- Search the public race catalog by name, country, race type and dates
- Explain a course: flat-equivalent distance, climbs and descents with where
  they fall, highest point, surface and technical sections
- Plan descents: how much quad damage they inflict and where to hold back
- Advise on running poles: whether to carry them and where to use them
- Check race-day weather at the course: the climate record of that date, the
  forecast when the race is close, and what the weather did once it is run
- Read results of completed races
- Read your profile, performance index, stored races and race wishlist
- Upload a GPX course (by link or file) as one of your races and analyse its
  terrain

## What it cannot do

- Training data, endurance curves, heart-rate zones and readiness are not
  available through this integration. They stay on the website.
- Deleting or editing races, settings and payments are website-only. When one
  of those is needed, the assistant gives you a link.
- Uploading a GPX course uses one of your race slots.

## ChatGPT

Directory listing: coming soon.

Until it is published, add the server yourself (account and workspace policies
apply to custom MCP servers):

1. Open [ChatGPT Plugins](https://chatgpt.com/plugins), select the plus button,
   then **Add custom MCP server**.
2. Name it Endurance Analytics and enter the URL
   `https://api.endurance-analytics.com/mcp`.
3. Choose OAuth authentication, confirm the warning and select
   **Create as a plugin**.
4. Sign in to Endurance Analytics in the window that opens and approve access.

The custom server gives you the tools; the skills arrive with the directory
listing.

## Claude Code

```
/plugin marketplace add IgorAleksandroff/endurance-analytics-plugin
/plugin install endurance@endurance-analytics
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
.claude-plugin/marketplace.json     Claude Code marketplace
plugins/endurance/
  plugin.json, mcp.json, assets/    OpenAI plugin (Agent Plugins format)
  .claude-plugin/plugin.json        Claude Code plugin manifest
  .mcp.json                         Claude Code MCP configuration
  skills/                           Skills shared by both
scripts/
  validate-openai.py                Checks the OpenAI package
  build-openai-zip.sh               Validates and builds dist/endurance-openai-<version>.zip
review-notes.md                     OpenAI review material (not in the ZIP)
```

Build the OpenAI package:

```bash
scripts/build-openai-zip.sh                      # release build
scripts/build-openai-zip.sh --allow-placeholder  # draft, while the demo video URL is a placeholder
```

Bump the version in `plugins/endurance/plugin.json`,
`plugins/endurance/.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json` together; the validator checks they match.

## Keeping the plugin in sync with the server

The MCP server lives in the backend (`internal/mcpserver`). Whenever a tool is
added, removed or renamed, or its inputs, outputs, annotations or limits change,
update this repository in the same piece of work:

1. `skills/*/SKILL.md`: every mention of the tool, its parameters and its fields.
2. `scripts/validate-openai.py`: `KNOWN_TOOLS`.
3. `plugin.json` → `review.test_cases`, and `review-notes.md` (annotation
   justifications, test cases). A test case must still run on a fresh reviewer
   account.
4. `README.md` → "What it can do" / "What it cannot do"; `plugin.json` →
   `longDescription` and `defaultPrompt`; `marketplace.json` description.
5. Bump the version in all three manifests, run the validator, commit and push.
6. ChatGPT: tool changes reach the listing through OpenAI's daily rescan, but
   new tools stay hidden until approved, and anything inside the package
   (skills, metadata) needs a new ZIP: build it and upload it as a new version
   in the plugin portal.

Data obtained from Strava (trainings, curves, zones, readiness) must never be
exposed through the tools or described in the skills.

## Documentation and privacy

- Setup guide: <https://endurance-analytics.com/en/connect>
- Agent-facing reference: <https://endurance-analytics.com/agents.md>
- Privacy policy: <https://endurance-analytics.com/en/privacy>
- Terms: <https://endurance-analytics.com/en/terms>

## License

MIT
