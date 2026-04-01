# Sushant's Side Projects — Master Inventory
*Last updated: April 1, 2026*

> Single source of truth for all active side projects.
> Auto-refreshed twice daily via GitHub Actions. Manual fields live in `config.json`.

---

## Projects at a Glance

| Project | Type | Status | Last Push |
|---|---|---|---|
| [PatchPal](#patchpal) | iOS App | 🟢 Active | Mar 30, 2026 |
| [MealSight / NutriLens](#mealsight--nutrilens) | iOS App | 🟢 Active | Mar 11, 2026 |
| [app-dashboard](#app-dashboard) | Automation | 🟢 Active | Mar 14, 2026 |
| [SafeSF](#safesf) | ML / Web App | 🟢 Active | Mar 7, 2026 |

---

## PatchPal

**Description:** iOS app on the App Store. Uses TelemetryDeck for in-app analytics. Legal docs hosted via GitHub Pages. Feedback email: patchpalfeedback@gmail.com.

**Status:** 🟢 Active — on App Store

**Last Push:** Mar 30, 2026 (yesterday)

**Tech Stack:** `iOS` · `Swift` · `TelemetryDeck` · `GitHub Pages`

**Links:**
- [Privacy Policy](https://sushantwason.github.io/patchpal-legal/)
- App Store: *(add link)*
- [GitHub](https://github.com/sushantwason/patchpal-legal)

**Secrets / Credentials:**

| Secret | Purpose | Where Stored |
|---|---|---|
| `ASC_KEY_ID` | App Store Connect API key ID | app-dashboard GitHub Actions |
| `ASC_ISSUER_ID` | App Store Connect issuer ID | app-dashboard GitHub Actions |
| `ASC_PRIVATE_KEY` | App Store Connect .p8 key | app-dashboard GitHub Actions |
| `TD_EMAIL` | TelemetryDeck login | app-dashboard GitHub Actions |
| `TD_PASSWORD` | TelemetryDeck password | app-dashboard GitHub Actions |

**Notes:**
- Android-specific privacy policy exists in repo — future Android version?
- Stats fetched daily by app-dashboard, not this repo directly

---

## MealSight / NutriLens

**Description:** Meal Tracker

**Status:** 🟢 Active — on App Store

**Last Push:** Mar 11, 2026 (21d ago)

**Tech Stack:** `Swift` · `iOS Widget` · `JavaScript` · `Backend`

**Links:**
- App Store: *(add link)*
- [GitHub](https://github.com/sushantwason/NutriLens)

**Secrets / Credentials:**

| Secret | Purpose | Where Stored |
|---|---|---|
| `ASC_KEY_ID` | Shared with PatchPal — same ASC account | app-dashboard GitHub Actions |
| `ASC_ISSUER_ID` | Shared with PatchPal | app-dashboard GitHub Actions |
| `ASC_PRIVATE_KEY` | Shared with PatchPal | app-dashboard GitHub Actions |

**Open TODOs:**
- [ ] Confirm if App Store listing name is MealSight or NutriLens and align repo name

**Notes:**
- Stats fetched daily by app-dashboard, not this repo directly

---

## app-dashboard

**Description:** Daily automation that fetches App Store Connect stats for PatchPal and MealSight, updates a GitHub Gist with data.json, generates a dashboard HTML, and emails a summary to sushwason@gmail.com.

**Status:** 🟢 Active — running daily

**Last Push:** Mar 14, 2026 (17d ago)

**Tech Stack:** `Python 3.12` · `GitHub Actions` · `PyJWT` · `HTML` · `Gmail SMTP`

**Links:**
- [GitHub Actions](https://github.com/sushantwason/app-dashboard/actions)
- Gist Dashboard: *(add link)*
- [GitHub](https://github.com/sushantwason/app-dashboard)

**Schedulers / Automations:**

| Name | Where | Schedule | Notes |
|---|---|---|---|
| daily-dashboard.yml | GitHub Actions | 0 17 * * * (UTC) | 9 AM PST / 10 AM PDT — drifts 1hr during daylight saving |

**Secrets / Credentials:**

| Secret | Purpose | Where Stored |
|---|---|---|
| `ASC_KEY_ID` | App Store Connect API | GitHub Actions secrets |
| `ASC_ISSUER_ID` | App Store Connect API | GitHub Actions secrets |
| `ASC_PRIVATE_KEY` | App Store Connect .p8 key | GitHub Actions secrets |
| `GIST_PAT` | Update dashboard Gist | GitHub Actions secrets |
| `GMAIL_APP_PASSWORD` | Send from patchpalfeedback@ | GitHub Actions secrets |
| `TD_EMAIL` | TelemetryDeck login | GitHub Actions secrets |
| `TD_PASSWORD` | TelemetryDeck password | GitHub Actions secrets |

**Open TODOs:**
- [ ] Fix cron drift: change to '0 16 * * *' to fire at 9 AM PDT during daylight saving

**Notes:**
- ASC API data delayed 24-72 hrs by Apple — numbers will always lag vs. the dashboard UI. Cannot be fixed.
- Email sent from patchpalfeedback@gmail.com to sushwason@gmail.com
- Key script: scripts/update_dashboard.py | Email template: dashboard_email.html

---

## SafeSF

**Description:** ML system to predict San Francisco 311 service request volumes and patterns, helping the city allocate resources proactively. Includes a REST API, interactive dashboard with maps, and automated daily data updates.

**Status:** 🟢 Active — deployed on GCP

**Last Push:** Mar 7, 2026 (24d ago)

**Tech Stack:** `Python` · `FastAPI` · `React` · `Plotly.js` · `Mapbox` · `XGBoost` · `Prophet` · `scikit-learn` · `BigQuery` · `Cloud Run` · `GCP`

**Links:**
- Live Dashboard: *(add link)*
- [GitHub](https://github.com/sushantwason/safesf)

**Schedulers / Automations:**

| Name | Where | Schedule | Notes |
|---|---|---|---|
| Data updater | GCP Cloud Scheduler | Daily at 6 AM PT | Fetches from SF 311 Open Data portal |

**Secrets / Credentials:**

| Secret | Purpose | Where Stored |
|---|---|---|
| `GCP Service Account` | Cloud Run, BigQuery, Cloud Storage | GCP IAM |

**Notes:**
- Data source: SF 311 public portal — 5M+ requests from 2008 to present
- MIT licensed
- ML models: Volume Predictor (XGBoost+Prophet, ~15% MAPE), Hotspot Detector (DBSCAN, 85% precision), Category Classifier (RF+NLP, 92% accuracy)

---

## ⚠️ New Repos Detected (not in inventory)

| Repo | Description | Last Push |
|---|---|---|
| [projects-inventory](https://github.com/sushantwason/projects-inventory) | Master inventory of all side projects | Mar 31, 2026 |

> Add these to `config.json` when ready.
