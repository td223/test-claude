# Star Drift health checks

There are two parts:

1. **`star-drift/health.json`**: a tiny file the site serves at `/health.json`. Coolify checks it to tell whether the container is healthy.
2. **`check_star_drift.py`**: a script that checks the live site from outside, so you know when it's unreachable for real visitors.

## 1. Deploying on Coolify

The repo root has a `Dockerfile` that serves `star-drift/` with nginx on port 80. In Coolify, under the application's **Configuration → General**:

| Setting | Value |
|---|---|
| Build Pack | **Dockerfile** |
| Base Directory | `/` |
| Dockerfile Location | `/Dockerfile` |
| Ports Exposes | `80` or `3000` (nginx listens on both) |
| Domains | `https://<your domain>` |

Then press **Redeploy** and watch the deployment log until it finishes.

The Dockerfile has its own health check, so Coolify will report the container as healthy without further setup.

## Coolify health check settings (optional)

If you'd rather set it in Coolify too, go to **Configuration → Healthcheck**:

| Setting | Value |
|---|---|
| Enabled | on |
| Method | GET |
| Scheme | http |
| Host | localhost |
| Port | `80` |
| Path | `/health.json` |
| Return code | 200 |
| Interval / Timeout / Retries | defaults are fine (e.g. 5s / 5s / 10) |

Save and redeploy. The app should show **Running (healthy)**.

Coolify runs the check *inside* the container with `curl` or `wget`. The Dockerfile's nginx:alpine image has `wget`, so this works.

## 2. External monitor script

Needs Python 3.8+ and nothing else.

Check once (exit code 0 = healthy, 1 = down):

```bash
python healthcheck/check_star_drift.py https://your-star-drift-url
```

Keep watching every 60 seconds:

```bash
python healthcheck/check_star_drift.py https://your-star-drift-url --every 60
```

Get alerts in Discord or Slack when it goes down and when it recovers (one message per change, not every check):

```bash
python healthcheck/check_star_drift.py https://your-star-drift-url --every 60 --webhook https://discord.com/api/webhooks/...
```

What it checks:
- `/health.json` returns 200 with `"status": "ok"`
- `/` returns 200 and contains the game (the title and its `<canvas>`)
- Each response arrives within `--slow` seconds (default 3)

To run it on a schedule without leaving a window open, use Windows Task Scheduler or cron with the single-check form.
