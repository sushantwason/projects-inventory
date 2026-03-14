# Setup Instructions

## One-time setup (5 minutes)

### 1. Create a public GitHub repo
Go to https://github.com/new and create a **public** repo named `projects-inventory`.

### 2. Push these files to it
```bash
cd path/to/this/folder
git init
git add .
git commit -m "Initial inventory setup"
git remote add origin https://github.com/sushantwason/projects-inventory.git
git push -u origin main
```

### 3. Create a GitHub PAT
Go to https://github.com/settings/tokens/new and create a **Classic PAT** with:
- `repo` scope (to read private repos and commit back to this repo)

Copy the token.

### 4. Add the PAT as a repo secret
Go to your new repo → Settings → Secrets and variables → Actions → New repository secret:
- Name: `INVENTORY_PAT`
- Value: paste the token

### 5. Enable GitHub Pages
Go to your repo → **Settings → Pages**:
- Source: **Deploy from a branch**
- Branch: `main` / `/ (root)`
- Click Save

Your dashboard will be live at:
**https://sushantwason.github.io/projects-inventory/**

Bookmark this. It auto-updates every time the cron commits new files.

> The repo is public so GitHub Pages works on the free plan. Your secrets stay safe — they're stored in GitHub Actions, not in any of the committed files.

### 6. Trigger a test run
Go to Actions tab → "Update Projects Inventory" → Run workflow.

Once it completes, visit your GitHub Pages URL — you should see the live dashboard.

---

## How it works

- **Twice a day** (9 AM + 6 PM PST), GitHub Actions runs `scripts/update_inventory.py`
- The script calls the GitHub API to get live data: last push dates, descriptions, repo languages
- It also scans for new repos on your profile that aren't yet in the inventory
- It regenerates `projects.md` and `projects.html` and commits them back

---

## How to update manual fields

Edit `config.json` directly in GitHub (or clone and edit locally). Fields you own:
- `status` / `status_note` — active or inactive
- `stack` — tech stack tags
- `links` — App Store URLs, Gist URLs, etc.
- `schedulers` — list of cron jobs / cloud schedulers
- `secrets` — credentials inventory
- `todos` — open action items
- `notes` — anything else
- `warnings` — things shown as yellow banners

To **add a new project**, add a new object to the `projects` array in `config.json`.

---

## Schedule
| Run | Cron (UTC) | Local Time |
|---|---|---|
| Morning | `0 17 * * *` | 9 AM PST / 10 AM PDT |
| Evening | `0 2 * * *` | 6 PM PST / 7 PM PDT |
