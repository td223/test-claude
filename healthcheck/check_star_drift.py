#!/usr/bin/env python3
"""Health checker for the Star Drift game.

Checks that:
  1. /health.json responds 200 with {"status": "ok"}
  2. The game page responds 200 and actually contains the game
  3. Both respond within a time limit

Uses only the Python standard library.

Examples:
  python check_star_drift.py https://stardrift.example.com
  python check_star_drift.py https://stardrift.example.com --every 60
  python check_star_drift.py https://stardrift.example.com --every 60 --webhook https://discord.com/api/webhooks/...

Exit code is 0 when healthy and 1 when not (single-run mode), so it also
works from cron, Task Scheduler or an uptime tool that runs commands.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

USER_AGENT = "star-drift-healthcheck/1.0"
GAME_MARKERS = ("STAR DRIFT", "<canvas")


def fetch(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"})
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body, time.perf_counter() - start


def check(base_url, timeout, slow):
    """Return a list of problems; an empty list means healthy."""
    base = base_url.rstrip("/")
    problems = []
    timings = {}

    for name, path in (("health", "/health.json"), ("game", "/")):
        url = base + path
        try:
            status, body, elapsed = fetch(url, timeout)
        except urllib.error.HTTPError as e:
            problems.append(f"{name}: HTTP {e.code} from {url}")
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            reason = getattr(e, "reason", e)
            problems.append(f"{name}: could not reach {url} ({reason})")
            continue

        timings[name] = elapsed
        if status != 200:
            problems.append(f"{name}: HTTP {status} from {url}")
        if elapsed > slow:
            problems.append(f"{name}: slow response ({elapsed:.2f}s > {slow}s)")

        if name == "health":
            try:
                if json.loads(body).get("status") != "ok":
                    problems.append("health: status is not 'ok'")
            except (ValueError, AttributeError):
                problems.append("health: response is not valid JSON")
        else:
            missing = [m for m in GAME_MARKERS if m not in body]
            if missing:
                problems.append(f"game: page is missing {', '.join(missing)}")

    return problems, timings


def notify(webhook, message):
    """POST a message to a Discord or Slack style webhook."""
    payload = json.dumps({"content": message, "text": message}).encode()
    req = urllib.request.Request(
        webhook, data=payload, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        urllib.request.urlopen(req, timeout=10).close()
    except Exception as e:  # never let alerting crash the checker
        print(f"  (webhook failed: {e})", file=sys.stderr)


def run_once(args):
    problems, timings = check(args.url, args.timeout, args.slow)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    times = " ".join(f"{k}={v * 1000:.0f}ms" for k, v in timings.items())
    if problems:
        print(f"[{stamp}] DOWN  {args.url}  {times}")
        for p in problems:
            print(f"  - {p}")
    else:
        print(f"[{stamp}] OK    {args.url}  {times}")
    return problems


def main():
    p = argparse.ArgumentParser(description="Health checker for Star Drift.")
    p.add_argument("url", help="Base URL of the deployed game, e.g. https://stardrift.example.com")
    p.add_argument("--timeout", type=float, default=10, help="Seconds before a request counts as failed (default 10)")
    p.add_argument("--slow", type=float, default=3, help="Seconds before a response counts as too slow (default 3)")
    p.add_argument("--every", type=float, metavar="SECONDS", help="Keep checking at this interval instead of running once")
    p.add_argument("--webhook", help="Discord/Slack webhook URL to alert when the site goes down and recovers")
    args = p.parse_args()

    if not args.every:
        sys.exit(1 if run_once(args) else 0)

    was_down = False
    try:
        while True:
            problems = run_once(args)
            # Alert only on state changes so a long outage doesn't spam the channel
            if args.webhook and bool(problems) != was_down:
                if problems:
                    notify(args.webhook, f"Star Drift is DOWN ({args.url}):\n" + "\n".join(f"- {x}" for x in problems))
                else:
                    notify(args.webhook, f"Star Drift is back UP ({args.url})")
            was_down = bool(problems)
            time.sleep(args.every)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
