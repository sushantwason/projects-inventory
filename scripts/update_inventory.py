"""
update_inventory.py
Fetches live GitHub data for Sushant's projects and regenerates
projects.md and projects.html in the repo root.

Manual fields (secrets, notes, links, TODOs) live in config.json.
Everything auto-detectable (last active, tech stack, description,
new repos) is pulled from the GitHub API.
"""

import json
import os
import requests
from datetime import datetime, timezone

GITHUB_USER = "sushantwason"
TOKEN = os.environ.get("INVENTORY_PAT", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
NOW = datetime.now(timezone.utc)


# ── GitHub API helpers ────────────────────────────────────────────────────────

def get_repos():
    """Return all repos for the user (public + private via PAT)."""
    repos, page = [], 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{GITHUB_USER}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "all"},
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return {repo["name"]: repo for repo in repos}


def get_workflows(repo_name):
    """Return list of workflow files in .github/workflows/."""
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/.github/workflows",
        headers=HEADERS,
    )
    if r.status_code == 404:
        return []
    r.raise_for_status()
    return [f["name"] for f in r.json() if f["name"].endswith(".yml")]


def get_workflow_content(repo_name, filename):
    """Return decoded content of a workflow file."""
    import base64
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/.github/workflows/{filename}",
        headers=HEADERS,
    )
    if r.status_code != 200:
        return ""
    return base64.b64decode(r.json()["content"]).decode()


def days_since(iso_str):
    """Return human-readable time since an ISO date string."""
    if not iso_str:
        return "unknown"
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    delta = NOW - dt
    if delta.days == 0:
        return "today"
    if delta.days == 1:
        return "yesterday"
    if delta.days < 30:
        return f"{delta.days}d ago"
    if delta.days < 365:
        return f"{delta.days // 30}mo ago"
    return f"{delta.days // 365}y ago"


def format_date(iso_str):
    """Return 'Mar 13, 2026' style date."""
    if not iso_str:
        return "unknown"
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%b %-d, %Y")


# ── Load config ───────────────────────────────────────────────────────────────

with open("config.json") as f:
    config = json.load(f)

known_repos = {p["repo"] for p in config["projects"] if p.get("repo")}


# ── Fetch live data ───────────────────────────────────────────────────────────

print("Fetching GitHub repos...")
all_repos = get_repos()

# Detect new repos not in config (created in last 90 days, not forks)
new_repos = [
    r for name, r in all_repos.items()
    if name not in known_repos
    and not r["fork"]
    and r.get("pushed_at")
    and (NOW - datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).days < 90
]

# Enrich each configured project with live GitHub data
for project in config["projects"]:
    repo_name = project.get("repo")
    if not repo_name or repo_name not in all_repos:
        project["_live"] = {}
        continue
    repo = all_repos[repo_name]
    workflows = get_workflows(repo_name)
    project["_live"] = {
        "description": repo.get("description") or project.get("description", ""),
        "language": repo.get("language") or "",
        "pushed_at": repo.get("pushed_at", ""),
        "pushed_label": format_date(repo.get("pushed_at", "")),
        "pushed_ago": days_since(repo.get("pushed_at", "")),
        "url": repo.get("html_url", ""),
        "topics": repo.get("topics", []),
        "workflows": workflows,
        "stars": repo.get("stargazers_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
    }
    print(f"  ✓ {repo_name} — last push: {project['_live']['pushed_label']}")


# ── Build Markdown ────────────────────────────────────────────────────────────

def md_table_row(*cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"


def build_markdown():
    today = NOW.strftime("%B %-d, %Y")
    lines = [
        f"# Sushant's Side Projects — Master Inventory",
        f"*Last updated: {today}*",
        "",
        "> Single source of truth for all active side projects.",
        "> Auto-refreshed twice daily via GitHub Actions. Manual fields live in `config.json`.",
        "",
        "---",
        "",
        "## Projects at a Glance",
        "",
        "| Project | Type | Status | Last Push |",
        "|---|---|---|---|",
    ]

    for p in config["projects"]:
        live = p.get("_live", {})
        anchor = p["name"].lower().replace(" ", "-").replace("/", "").replace("(", "").replace(")", "")
        status = "🟢 Active" if p.get("status") == "active" else "🔴 Inactive"
        last = live.get("pushed_label", "—")
        lines.append(md_table_row(f"[{p['name']}](#{anchor})", p.get("type", ""), status, last))

    lines += ["", "---", ""]

    for p in config["projects"]:
        live = p.get("_live", {})
        lines += [
            f"## {p['name']}",
            "",
            f"**Description:** {live.get('description') or p.get('description', '')}",
            "",
            f"**Status:** {'🟢 Active' if p.get('status') == 'active' else '🔴 Inactive'} — {p.get('status_note', '')}",
            "",
            f"**Last Push:** {live.get('pushed_label', '—')} ({live.get('pushed_ago', '—')})",
            "",
        ]

        # Tech stack
        stack = p.get("stack", [])
        if stack:
            lines += ["**Tech Stack:** " + " · ".join(f"`{s}`" for s in stack), ""]

        # Links
        links = p.get("links", {})
        live_url = live.get("url", "")
        if live_url:
            links["GitHub"] = live_url
        if links:
            lines.append("**Links:**")
            for label, url in links.items():
                if url:
                    lines.append(f"- [{label}]({url})")
                else:
                    lines.append(f"- {label}: *(add link)*")
            lines.append("")

        # Schedulers
        schedulers = p.get("schedulers", [])
        if schedulers:
            lines += [
                "**Schedulers / Automations:**",
                "",
                "| Name | Where | Schedule | Notes |",
                "|---|---|---|---|",
            ]
            for s in schedulers:
                lines.append(md_table_row(s.get("name", ""), s.get("where", ""), s.get("schedule", ""), s.get("notes", "")))
            lines.append("")

        # Secrets
        secrets = p.get("secrets", [])
        if secrets:
            lines += [
                "**Secrets / Credentials:**",
                "",
                "| Secret | Purpose | Where Stored |",
                "|---|---|---|",
            ]
            for s in secrets:
                lines.append(md_table_row(f"`{s['name']}`", s.get("purpose", ""), s.get("where", "")))
            lines.append("")

        # TODOs
        todos = p.get("todos", [])
        if todos:
            lines.append("**Open TODOs:**")
            for t in todos:
                lines.append(f"- [ ] {t}")
            lines.append("")

        # Notes
        notes = p.get("notes", [])
        if notes:
            lines.append("**Notes:**")
            for n in notes:
                lines.append(f"- {n}")
            lines.append("")

        lines += ["---", ""]

    # New repos alert
    if new_repos:
        lines += [
            "## ⚠️ New Repos Detected (not in inventory)",
            "",
            "| Repo | Description | Last Push |",
            "|---|---|---|",
        ]
        for r in new_repos:
            lines.append(md_table_row(
                f"[{r['name']}](https://github.com/{GITHUB_USER}/{r['name']})",
                r.get("description") or "—",
                format_date(r.get("pushed_at", ""))
            ))
        lines += ["", "> Add these to `config.json` when ready.", ""]

    return "\n".join(lines)


# ── Build HTML ────────────────────────────────────────────────────────────────

def build_html():
    today = NOW.strftime("%B %-d, %Y")

    def tag(name, content, cls="", **attrs):
        attr_str = (f' class="{cls}"' if cls else "") + "".join(f' {k}="{v}"' for k, v in attrs.items())
        return f"<{name}{attr_str}>{content}</{name}>"

    active_count = sum(1 for p in config["projects"] if p.get("status") == "active")
    scheduler_count = sum(len(p.get("schedulers", [])) for p in config["projects"])
    secret_count = sum(len(p.get("secrets", [])) for p in config["projects"])
    ios_count = sum(1 for p in config["projects"] if p.get("type") == "iOS App")

    cards_html = ""
    for p in config["projects"]:
        live = p.get("_live", {})
        status_badge = '<span class="badge active">● Active</span>' if p.get("status") == "active" else '<span class="badge inactive">○ Inactive</span>'

        # Links
        links_html = ""
        all_links = dict(p.get("links", {}))
        if live.get("url"):
            all_links = {"GitHub": live["url"], **all_links}
        for label, url in all_links.items():
            if url:
                links_html += f'<a class="link-btn" href="{url}" target="_blank">{label}</a>'
            else:
                links_html += f'<span class="link-btn placeholder">{label} — add link</span>'

        # Stack tags
        stack_html = "".join(f'<span class="tag">{s}</span>' for s in p.get("stack", []))

        # Schedulers table
        schedulers = p.get("schedulers", [])
        sched_html = ""
        if schedulers:
            rows = "".join(
                f"<tr><td>{s.get('name','')}</td><td>{s.get('where','')}</td>"
                f"<td><code>{s.get('schedule','')}</code></td><td>{s.get('notes','')}</td></tr>"
                for s in schedulers
            )
            sched_html = f"""
            <div class="section-label">Schedulers</div>
            <table><tr><th>Name</th><th>Where</th><th>Schedule</th><th>Notes</th></tr>{rows}</table>"""

        # Secrets table
        secrets = p.get("secrets", [])
        secrets_html = ""
        if secrets:
            rows = "".join(
                f"<tr><td><code>{s['name']}</code></td><td>{s.get('purpose','')}</td><td>{s.get('where','')}</td></tr>"
                for s in secrets
            )
            secrets_html = f"""
            <div class="section-label">Secrets</div>
            <table><tr><th>Secret</th><th>Purpose</th><th>Where Stored</th></tr>{rows}</table>"""

        # TODOs
        todos = p.get("todos", [])
        todos_html = ""
        if todos:
            items = "".join(f"<li>{t}</li>" for t in todos)
            todos_html = f'<div class="section-label">Open TODOs</div><ul class="todo-list">{items}</ul>'

        # Notes
        notes = p.get("notes", [])
        notes_html = ""
        if notes:
            items = "".join(f"<li>{n}</li>" for n in notes)
            notes_html = f'<div class="section-label">Notes</div><ul class="notes-list">{items}</ul>'

        # Warnings
        warnings_html = ""
        for w in p.get("warnings", []):
            warnings_html += f'<div class="warning-banner">⚠️ {w}</div>'

        cards_html += f"""
  <div class="project-card">
    <div class="project-header">
      <div>
        <div class="project-name">{p['name']}</div>
        <div class="project-sub">{p.get('type','')} · Last push: {live.get('pushed_label','—')} ({live.get('pushed_ago','—')})</div>
      </div>
      {status_badge}
    </div>
    <p class="desc">{live.get('description') or p.get('description','')}</p>
    {warnings_html}
    <div class="section-label">Tech Stack</div>
    <div class="tags">{stack_html}</div>
    <div class="section-label">Links</div>
    <div class="links">{links_html}</div>
    {sched_html}
    {secrets_html}
    {todos_html}
    {notes_html}
  </div>"""

    # New repos alert
    new_repos_html = ""
    if new_repos:
        rows = "".join(
            f'<tr><td><a href="https://github.com/{GITHUB_USER}/{r["name"]}" target="_blank">{r["name"]}</a></td>'
            f'<td>{r.get("description") or "—"}</td><td>{format_date(r.get("pushed_at",""))}</td></tr>'
            for r in new_repos
        )
        new_repos_html = f"""
  <div class="project-card" style="border-color:#4a3500;">
    <div class="project-header">
      <div class="project-name" style="color:#f59e0b;">⚠️ New Repos Detected</div>
    </div>
    <p class="desc">These repos are not yet in the inventory. Add them to <code>config.json</code> when ready.</p>
    <table><tr><th>Repo</th><th>Description</th><th>Last Push</th></tr>{rows}</table>
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Sushant's Projects</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f0f0f;color:#e0e0e0;min-height:100vh;padding:40px 24px}}
    .container{{max-width:960px;margin:0 auto}}
    header{{margin-bottom:40px}}
    header h1{{font-size:28px;font-weight:700;color:#fff}}
    header p{{color:#666;font-size:14px;margin-top:6px}}
    .summary-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:48px}}
    .summary-card{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;padding:20px}}
    .summary-card .label{{font-size:12px;color:#666;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}}
    .summary-card .value{{font-size:22px;font-weight:700;color:#fff}}
    .summary-card .sub{{font-size:12px;color:#555;margin-top:4px}}
    .project-card{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:16px;padding:28px;margin-bottom:20px}}
    .project-card:hover{{border-color:#3a3a3a}}
    .project-header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:10px}}
    .project-name{{font-size:20px;font-weight:700;color:#fff}}
    .project-sub{{font-size:13px;color:#555;margin-top:2px}}
    .badge{{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:600;padding:4px 10px;border-radius:20px}}
    .badge.active{{background:#0d2b1a;color:#34d399;border:1px solid #065f46}}
    .badge.inactive{{background:#1f1f1f;color:#888;border:1px solid #333}}
    .desc{{font-size:14px;color:#aaa;line-height:1.6;margin-bottom:20px}}
    .section-label{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:#555;margin-bottom:10px}}
    .tags{{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:20px}}
    .tag{{font-size:12px;background:#222;border:1px solid #333;color:#bbb;padding:3px 10px;border-radius:6px}}
    .links{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px}}
    .link-btn{{font-size:13px;color:#60a5fa;text-decoration:none;background:#1e2a3a;border:1px solid #2a3d55;padding:5px 12px;border-radius:8px}}
    .link-btn:hover{{background:#243246}}
    .link-btn.placeholder{{color:#444;background:#1a1a1a;border-color:#2a2a2a;cursor:default}}
    table{{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:20px}}
    th{{text-align:left;padding:8px 12px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#555;border-bottom:1px solid #2a2a2a}}
    td{{padding:9px 12px;border-bottom:1px solid #222;color:#ccc;vertical-align:top}}
    tr:last-child td{{border-bottom:none}}
    td code,p code{{font-family:'SF Mono','Fira Code',monospace;font-size:12px;background:#222;padding:2px 6px;border-radius:4px;color:#f9a8d4}}
    .todo-list,.notes-list{{list-style:none}}
    .todo-list li,.notes-list li{{font-size:13px;color:#aaa;padding:6px 0;border-bottom:1px solid #222;display:flex;align-items:flex-start;gap:8px}}
    .todo-list li:last-child,.notes-list li:last-child{{border-bottom:none}}
    .todo-list li::before{{content:"○";color:#444;flex-shrink:0}}
    .notes-list li::before{{content:"·";color:#444;flex-shrink:0}}
    .warning-banner{{background:#1f1a0d;border:1px solid #4a3500;border-radius:10px;padding:12px 16px;font-size:13px;color:#f59e0b;margin-bottom:20px}}
    footer{{margin-top:48px;text-align:center;font-size:12px;color:#444}}
  </style>
</head>
<body>
<div class="container">
  <header>
    <h1>Sushant's Side Projects</h1>
    <p>Last updated: {today} &nbsp;·&nbsp; Auto-refreshed 9 AM &amp; 6 PM PT via GitHub Actions</p>
  </header>
  <div class="summary-grid">
    <div class="summary-card"><div class="label">Total Projects</div><div class="value">{len(config['projects'])}</div><div class="sub">All tracked</div></div>
    <div class="summary-card"><div class="label">Active</div><div class="value">{active_count}</div><div class="sub">of {len(config['projects'])} total</div></div>
    <div class="summary-card"><div class="label">iOS Apps</div><div class="value">{ios_count}</div><div class="sub">on App Store</div></div>
    <div class="summary-card"><div class="label">Active Schedulers</div><div class="value">{scheduler_count}</div><div class="sub">across all projects</div></div>
  </div>
  {cards_html}
  {new_repos_html}
  <footer>
    Manual fields edited in <code>config.json</code> · Auto fields refreshed from GitHub API<br><br>
    Generated by GitHub Actions · {today}
  </footer>
</div>
</body>
</html>"""


# ── Write files ───────────────────────────────────────────────────────────────

print("Generating projects.md...")
with open("projects.md", "w") as f:
    f.write(build_markdown())

print("Generating projects.html...")
with open("projects.html", "w") as f:
    f.write(build_html())

print("Done.")
