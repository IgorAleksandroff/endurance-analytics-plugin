#!/usr/bin/env python3
"""Validate the OpenAI (Agent Plugins) package of the endurance plugin.

Run isolated: python3 -I scripts/validate-openai.py [--allow-placeholder] [PLUGIN_DIR]
Exit code 1 on any error. Standard library only.
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path

PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"

KNOWN_TOOLS = {
    "get_my_profile",
    "get_my_performance_index",
    "get_my_races",
    "get_my_race",
    "get_my_race_track",
    "get_my_wishlist",
    "search_races",
    "get_race",
    "get_race_results",
    "get_race_splits",
    "get_race_terrain_summary",
    "get_race_pole_advice",
    "get_race_quad_damage",
    "get_race_course_segments",
    "get_race_weather",
    "get_race_report",
    "save_gpx_as_race",
}

CATEGORIES = {
    "Productivity", "Creativity", "Developer Tools", "Business & Operations",
    "Data & Analytics", "Communication", "Education & Research", "Security",
    "Finance", "Healthcare", "Travel", "Entertainment", "Other",
}

FORBIDDEN_KEYS = {
    "test_credentials", "reviewer_instructions", "headers", "clientSecret",
    "apps", "hooks",
}

# Paths that must not be shipped in the OpenAI ZIP (relative to the plugin root).
FORBIDDEN_PATHS = [".app.json", "hooks", "hooks.json", "commands", "agents", ".codex-plugin"]

# Excluded from the ZIP by build-openai-zip.sh; the validator must mirror it.
ZIP_EXCLUDES = {".claude-plugin", ".mcp.json", ".DS_Store", "dist"}

PLACEHOLDER = re.compile(r"example\.(invalid|com)|TODO", re.IGNORECASE)
SECRET = re.compile(
    r"""(?ix)
    (api[_-]?key|secret|password|passwd|bearer|token)["']?\s*[:=]\s*["'][^"'\s]{8,}["']
    | -----BEGIN\ [A-Z ]*PRIVATE\ KEY-----
    | \bsk-[A-Za-z0-9]{20,}
    """
)
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$")
PLUGIN_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SKILL_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CLAUDE_WORD = re.compile(r"\bclaude\b", re.IGNORECASE)


class Report:
    def __init__(self):
        self.errors = []
        self.notes = []

    def err(self, msg):
        self.errors.append(msg)

    def note(self, msg):
        self.notes.append(msg)


def load_json(path, rep):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        rep.err(f"{path.name}: missing")
    except json.JSONDecodeError as e:
        rep.err(f"{path.name}: malformed JSON at line {e.lineno}: {e.msg}")
    return None


def find_keys(obj, keys, trail=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{trail}.{k}" if trail else k
            if k in keys:
                found.append(here)
            found.extend(find_keys(v, keys, here))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(find_keys(v, keys, f"{trail}[{i}]"))
    return found


def text(rep, obj, key, where, limit, single_line=False, required=True):
    val = obj.get(key) if isinstance(obj, dict) else None
    if val is None:
        if required:
            rep.err(f"{where}.{key}: required")
        return None
    if not isinstance(val, str) or not val.strip():
        rep.err(f"{where}.{key}: must be a non-empty string")
        return None
    if val != val.strip():
        rep.err(f"{where}.{key}: leading or trailing whitespace")
    if len(val) > limit:
        rep.err(f"{where}.{key}: {len(val)} chars, limit {limit}")
    if single_line and ("\n" in val or "\r" in val):
        rep.err(f"{where}.{key}: must be one line")
    if re.search(r"[\x00-\x08\x0b-\x1f\x7f]", val):
        rep.err(f"{where}.{key}: control characters")
    return val


def https_url(rep, obj, key, where, limit=1024):
    val = text(rep, obj, key, where, limit, single_line=True)
    if val and not re.match(r"^https://[^\s/@:]+(:\d+)?(/\S*)?$", val):
        rep.err(f"{where}.{key}: must be an https URL without credentials: {val}")
    return val


def luminance(hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def png_size(path):
    with path.open("rb") as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def check_asset(rep, root, rel, field):
    if not isinstance(rel, str) or not rel.startswith("./"):
        rep.err(f"interface.{field}: path must start with ./")
        return
    if ".." in Path(rel).parts:
        rep.err(f"interface.{field}: path must stay inside the plugin")
        return
    path = (root / rel).resolve()
    if root.resolve() not in path.parents:
        rep.err(f"interface.{field}: path escapes the plugin root")
        return
    if not path.is_file():
        rep.err(f"interface.{field}: {rel} does not exist")
        return
    if path.suffix.lower() != ".png":
        rep.err(f"interface.{field}: only PNG is checked here, got {path.suffix}")
        return
    if path.stat().st_size > 5 * 1024 * 1024:
        rep.err(f"interface.{field}: larger than 5 MiB")
    size = png_size(path)
    if size is None:
        rep.err(f"interface.{field}: not a valid PNG (no IHDR)")
        return
    w, h = size
    if w != h:
        rep.err(f"interface.{field}: not square ({w}x{h})")
    if not 48 <= w <= 4096:
        rep.err(f"interface.{field}: {w}x{h} outside 48..4096")
    rep.note(f"{field}: {rel} PNG {w}x{h}")


def check_interface(rep, root, iface):
    where = "interface"
    if not isinstance(iface, dict):
        rep.err("extensions.com.openai.interface: required object")
        return
    text(rep, iface, "displayName", where, 30, single_line=True)
    text(rep, iface, "shortDescription", where, 30, single_line=True)
    text(rep, iface, "longDescription", where, 4000)
    text(rep, iface, "developerName", where, 80, single_line=True)
    cat = text(rep, iface, "category", where, 64, single_line=True)
    if cat and cat not in CATEGORIES:
        rep.err(f"{where}.category: unknown category {cat!r}")
    for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        https_url(rep, iface, key, where)

    prompts = iface.get("defaultPrompt")
    if not isinstance(prompts, list) or len(prompts) != 3:
        rep.err(f"{where}.defaultPrompt: exactly 3 prompts required")
    else:
        seen = set()
        for i, p in enumerate(prompts):
            if not isinstance(p, str) or not p.strip():
                rep.err(f"{where}.defaultPrompt[{i}]: non-empty string required")
                continue
            if len(p) > 128:
                rep.err(f"{where}.defaultPrompt[{i}]: {len(p)} chars, limit 128")
            if "\n" in p:
                rep.err(f"{where}.defaultPrompt[{i}]: must be one line")
            if "@" in p:
                rep.err(f"{where}.defaultPrompt[{i}]: must not contain @")
            norm = " ".join(p.split()).casefold()
            if norm in seen:
                rep.err(f"{where}.defaultPrompt[{i}]: duplicate")
            seen.add(norm)

    for key, against, label in (("brandColor", "#FFFFFF", "white"), ("brandColorDark", "#212121", "#212121")):
        val = iface.get(key)
        if not isinstance(val, str) or not HEX.match(val):
            rep.err(f"{where}.{key}: #RRGGBB required")
            continue
        ratio = contrast(val, against)
        if ratio < 2.0:
            rep.err(f"{where}.{key}: contrast {ratio:.2f}:1 against {label}, need >= 2:1")
        rep.note(f"{key} {val}: {ratio:.2f}:1 against {label}")

    for key in ("logo", "composerIcon"):
        if key not in iface:
            rep.err(f"{where}.{key}: required")
        else:
            check_asset(rep, root, iface[key], key)
    if "screenshots" in iface:
        rep.err(f"{where}.screenshots: not allowed without a custom UI")


def check_cases(rep, cases, kind, count, fields):
    where = f"review.test_cases.{kind}"
    if not isinstance(cases, list) or len(cases) != count:
        rep.err(f"{where}: exactly {count} cases required")
        return
    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            rep.err(f"{where}[{i}]: object required")
            continue
        for f in fields:
            text(rep, case, f, f"{where}[{i}]", 4000)
        tools = case.get("tools_triggered")
        if isinstance(tools, str):
            names = [t.strip() for t in tools.split(",")]
            unknown = [t for t in names if t not in KNOWN_TOOLS]
            if unknown or not all(names):
                rep.err(f"{where}[{i}].tools_triggered: unknown tools {unknown or names}")


def check_review(rep, review, allow_placeholder):
    if not isinstance(review, dict):
        rep.err("extensions.com.openai.review: required object")
        return
    tc = review.get("test_cases")
    if not isinstance(tc, dict):
        rep.err("review.test_cases: required object")
    else:
        check_cases(rep, tc.get("positive"), "positive", 5,
                    ("description", "prompt", "tools_triggered", "expected_behavior"))
        check_cases(rep, tc.get("negative"), "negative", 3, ("description", "prompt"))
    demo = https_url(rep, review, "demo_recording_url", "review")
    if demo and PLACEHOLDER.search(demo):
        if allow_placeholder:
            rep.note(f"review.demo_recording_url is a placeholder ({demo}), allowed by flag")
        else:
            rep.err(f"review.demo_recording_url is a placeholder: {demo}")
    if not isinstance(review.get("commerce"), bool):
        rep.err("review.commerce: boolean required")


def check_publication(rep, pub):
    if not isinstance(pub, dict):
        rep.err("extensions.com.openai.publication: required object")
        return
    countries = pub.get("countries")
    if not isinstance(countries, list) or not all(isinstance(c, str) and re.match(r"^[A-Z]{2}$", c) for c in countries):
        rep.err("publication.countries: list of uppercase 2-letter codes required ([] = everywhere)")
    text(rep, pub, "release_notes", "publication", 4000)


def check_manifest(rep, root, manifest, allow_placeholder):
    if manifest.get("$schema") != PLUGIN_SCHEMA:
        rep.err(f"plugin.json: $schema must be {PLUGIN_SCHEMA}")
    name = text(rep, manifest, "name", "plugin.json", 64, single_line=True)
    if name and not PLUGIN_NAME.match(name):
        rep.err(f"plugin.json.name: must be kebab-case: {name}")
    version = text(rep, manifest, "version", "plugin.json", 64, single_line=True)
    if version and not SEMVER.match(version):
        rep.err(f"plugin.json.version: not semver: {version}")
    text(rep, manifest, "description", "plugin.json", 1024)
    author = manifest.get("author")
    if not isinstance(author, dict):
        rep.err("plugin.json.author: required object")
    else:
        text(rep, author, "name", "plugin.json.author", 120, single_line=True)
        https_url(rep, author, "url", "plugin.json.author", 2048)
    https_url(rep, manifest, "homepage", "plugin.json", 2048)
    text(rep, manifest, "license", "plugin.json", 64, single_line=True)
    allowed_root = {"$schema", "name", "version", "description", "author", "homepage",
                    "repository", "license", "keywords", "extensions"}
    extra = set(manifest) - allowed_root
    if extra:
        rep.err(f"plugin.json: keys not allowed by the schema: {sorted(extra)}")

    oai = manifest.get("extensions", {}).get("com.openai")
    if not isinstance(oai, dict):
        rep.err("plugin.json: extensions.com.openai object required")
        return name
    check_interface(rep, root, oai.get("interface"))
    onboarding = oai.get("onboardingSkill")
    if not isinstance(onboarding, str) or not re.match(r"^\./skills/[^/]+/SKILL\.md$", onboarding):
        rep.err("onboardingSkill: must be ./skills/<name>/SKILL.md")
    elif not (root / onboarding).is_file():
        rep.err(f"onboardingSkill: {onboarding} does not exist")
    check_review(rep, oai.get("review"), allow_placeholder)
    check_publication(rep, oai.get("publication"))
    return name


def check_mcp(rep, root):
    mcp = load_json(root / "mcp.json", rep)
    if mcp is None:
        return None
    if mcp.get("$schema") != MCP_SCHEMA:
        rep.err(f"mcp.json: $schema must be {MCP_SCHEMA}")
    servers = mcp.get("mcpServers")
    if not isinstance(servers, dict) or len(servers) != 1:
        rep.err("mcp.json: exactly one server required (plugin-level test cases need one)")
        return None
    (sname, server), = servers.items()
    where = f"mcp.json.mcpServers.{sname}"
    if server.get("type") != "streamable-http":
        rep.err(f"{where}.type: must be streamable-http")
    url = https_url(rep, server, "url", where, 2048)
    auth = server.get("extensions", {}).get("com.openai", {}).get("auth")
    if not isinstance(auth, dict) or auth.get("type") != "oauth":
        rep.err(f"{where}: extensions.com.openai.auth.type must be oauth")
    elif not isinstance(auth.get("client"), dict) or auth["client"].get("mode") != "dcr":
        rep.err(f"{where}: auth.client.mode must be dcr")
    elif set(auth["client"]) != {"mode"}:
        rep.err(f"{where}: a dcr client must not carry clientId or credentials")
    return url


def check_claude_side(rep, root, openai_url, version):
    claude_mcp = load_json(root / ".mcp.json", rep)
    if claude_mcp is not None:
        urls = {s.get("url") for s in claude_mcp.get("mcpServers", {}).values()}
        if urls != {openai_url}:
            rep.err(f".mcp.json: server URL {sorted(map(str, urls))} differs from mcp.json {openai_url}")
    claude_manifest = load_json(root / ".claude-plugin" / "plugin.json", rep)
    if claude_manifest is not None and claude_manifest.get("version") != version:
        rep.err(f".claude-plugin/plugin.json: version {claude_manifest.get('version')} != {version}")
    market = load_json(root.parent.parent / ".claude-plugin" / "marketplace.json", rep)
    if market is not None:
        for p in market.get("plugins", []):
            if p.get("source") == "./plugins/" + root.name and p.get("version") != version:
                rep.err(f"marketplace.json: plugin version {p.get('version')} != {version}")


def parse_frontmatter(raw):
    if not raw.startswith("---\n"):
        return None, None
    end = raw.find("\n---\n", 4)
    if end == -1:
        return None, None
    fields = {}
    for line in raw[4:end].splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            return None, None
        val = m.group(2).strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        fields[m.group(1)] = val
    return fields, raw[end + 5:]


def check_skill_yaml(rep, path, where):
    raw = path.read_text(encoding="utf-8")
    if not re.match(r"^interface:\s*$", raw.splitlines()[0] if raw else ""):
        rep.err(f"{where}: must start with an interface mapping")
        return
    for key in ("display_name", "short_description"):
        m = re.search(rf"^\s+{key}:\s*\"?([^\"\n]+)\"?\s*$", raw, re.MULTILINE)
        if not m or not m.group(1).strip():
            rep.err(f"{where}: interface.{key} required")
    if CLAUDE_WORD.search(raw):
        rep.err(f"{where}: mentions Claude; use neutral wording")


def check_skills(rep, root, plugin_name):
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        rep.err("skills/: missing")
        return
    names = []
    for d in sorted(skills_dir.iterdir()):
        if d.name in ZIP_EXCLUDES:
            continue
        if not d.is_dir():
            rep.err(f"skills/{d.name}: files directly under skills/ are ignored")
            continue
        where = f"skills/{d.name}"
        if d.name.startswith("."):
            rep.err(f"{where}: hidden skill directory")
        skill_md = d / "SKILL.md"
        if not skill_md.is_file():
            rep.err(f"{where}: SKILL.md missing")
            continue
        raw = skill_md.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(raw)
        if fm is None:
            rep.err(f"{where}/SKILL.md: YAML front matter missing or malformed")
            continue
        name, desc = fm.get("name", ""), fm.get("description", "")
        if name != d.name:
            rep.err(f"{where}: front matter name {name!r} != folder name")
        if not SKILL_NAME.match(name):
            rep.err(f"{where}: name must be kebab-case")
        if not desc:
            rep.err(f"{where}: description required")
        elif len(desc) > 1024:
            rep.err(f"{where}: description {len(desc)} chars, limit 1024")
        if not body.strip():
            rep.err(f"{where}: body is empty")
        if plugin_name and len(f"{plugin_name}:{name}") > 64:
            rep.err(f"{where}: '{plugin_name}:{name}' longer than 64 chars")
        if CLAUDE_WORD.search(raw):
            rep.err(f"{where}/SKILL.md: mentions Claude; use neutral wording")
        agent_yaml = d / "agents" / "openai.yaml"
        if agent_yaml.exists():
            check_skill_yaml(rep, agent_yaml, f"{where}/agents/openai.yaml")
        names.append(name)
    if not names:
        rep.err("skills/: at least one skill required")
    rep.note(f"skills: {', '.join(names)}")


def packaged_files(root):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in ZIP_EXCLUDES for part in rel.parts):
            continue
        if path.is_file():
            yield rel, path


def check_package(rep, root, docs):
    for rel in FORBIDDEN_PATHS:
        if (root / rel).exists():
            rep.err(f"forbidden in the ZIP: {rel}")
    for where, doc in docs.items():
        for hit in find_keys(doc, FORBIDDEN_KEYS):
            rep.err(f"{where}: forbidden key {hit}")
    for rel, path in packaged_files(root):
        if path.is_symlink():
            rep.err(f"{rel}: symlinks are not allowed")
        if path.suffix in {".md", ".json", ".yaml", ".yml", ".txt"}:
            if SECRET.search(path.read_text(encoding="utf-8")):
                rep.err(f"{rel}: looks like it contains a secret")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_dir", nargs="?",
                        default=str(Path(__file__).resolve().parent.parent / "plugins" / "endurance"))
    parser.add_argument("--allow-placeholder", action="store_true",
                        help="accept a placeholder demo_recording_url (draft builds only)")
    args = parser.parse_args()

    root = Path(args.plugin_dir).resolve()
    rep = Report()
    manifest = load_json(root / "plugin.json", rep)
    if manifest is None:
        print("\n".join(f"ERROR {e}" for e in rep.errors))
        return 1

    name = check_manifest(rep, root, manifest, args.allow_placeholder)
    url = check_mcp(rep, root)
    check_claude_side(rep, root, url, manifest.get("version"))
    check_skills(rep, root, name)
    mcp_doc = load_json(root / "mcp.json", Report()) or {}
    check_package(rep, root, {"plugin.json": manifest, "mcp.json": mcp_doc})

    for n in rep.notes:
        print(f"ok    {n}")
    for e in rep.errors:
        print(f"ERROR {e}")
    if rep.errors:
        print(f"FAILED: {len(rep.errors)} error(s) in {root}")
        return 1
    print(f"PASSED: {manifest.get('name')} {manifest.get('version')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
