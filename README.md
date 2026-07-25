# Endurance Analytics plugin for Claude Code

Query your [Endurance Analytics](https://endurance-analytics.com) training
history, endurance curves and race courses from your AI assistant — and upload
GPX courses to get their terrain analysed.

## Install

```
/plugin marketplace add IgorAleksandroff/endurance-analytics-plugin
/plugin install endurance@endurance-analytics
```

Then run `/mcp` and follow the browser sign-in. You approve what the assistant
may access on a consent screen; the token refreshes itself afterwards.

You need an Endurance Analytics account. Sign up at
[endurance-analytics.com](https://endurance-analytics.com).

## What it can do

- Answer questions about your trainings, current form, endurance curves, training
  zones, performance index and stored races
- Search the public race catalog and read results and course terrain
- Upload a GPX course as one of your races and analyse its terrain

## What it cannot do

Deleting races, editing data, changing settings and payments are website-only.
When one of those is needed, the assistant gives you a link.

## Scripts

For automation without OAuth, create a personal token in
**Profile → Settings → AI agent access** and add the server directly:

```bash
claude mcp add --transport http endurance https://api.endurance-analytics.com/mcp \
  --header "Authorization: Bearer $ENDURANCE_PAT"
```

The plugin itself ships no secrets: `.mcp.json` here contains only the endpoint.

## Documentation

- Setup guide: <https://endurance-analytics.com/en/connect>
- Agent-facing reference: <https://endurance-analytics.com/agents.md>

## License

MIT
