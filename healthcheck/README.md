# Star Drift health checks

There are two parts:

1. **`star-drift/health.json`**: a tiny file the site serves at `/health.json`. Coolify checks it to tell whether the container is healthy.
2. **`check_star_drift.py`**: a script that checks the live site from outside, so you know when it's unreachable for real visitors.

## 1. Coolify health check

Deploy the commit that adds `health.json`, then in Coolify open your Star Drift application and go to **Configuration → Healthcheck**:

| Setting | Value |
|---|---|
| Enabled | on |
| Method | GET |
| Scheme | http |
| Host | localhost |
| Port | the port your container listens on (usually `80` for a static site) |
| Path | `/health.json` |
| Return code | 200 |
| Interval / Timeout / Retries | defaults are fine (e.g. 5s / 5s / 10) |

Save and redeploy. The app should show **Running (healthy)**.

Notes:
- If Coolify's **Base Directory** is the repo root rather than `/star-drift`, the path is `/star-drift/health.json` instead.
- Coolify runs the check *inside* the container with `curl` or `wget`. The nginx image Coolify uses for static sites has `wget`, so this works. If you use a custom image without either, the check will always fail.

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
