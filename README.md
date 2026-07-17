# exercise1min.com

Product website for **Exercise 1 Min** — a fully-offline mobile app for desk-friendly,
one-minute movement breaks (English / global).

Static site — plain HTML, CSS, and JS with no build step, frameworks, analytics, or external assets.
Deployed to **GitHub Pages** on every push to `main` via `.github/workflows/deploy.yml`.

The website mirrors the current app behavior: standing-first routines, optional floor moves,
at-your-own-pace sessions with no countdown, local roast reminders, and break-based progress.

## Local preview

```bash
python3 -m http.server
# then open http://localhost:8000
```

## Quality checks

```bash
python3 -m unittest discover -s tests -v
```

## Deployment

Pushes to `main` trigger `.github/workflows/deploy.yml`, which publishes the site to
**GitHub Pages** using the **GitHub Actions** build source.

The repo's Pages **source must be set to "GitHub Actions"** (Settings → Pages → Build and
deployment → Source). The workflow passes `enablement: true` to `actions/configure-pages`,
so it enables Pages automatically on a fresh repo. If a run ever fails with
`Get Pages site failed … Not Found`, it means Pages was never enabled — set the source to
GitHub Actions (or re-run once `enablement: true` is in place) and re-run the workflow.

The custom domain is set via the `CNAME` file (`exercise1min.com`).
