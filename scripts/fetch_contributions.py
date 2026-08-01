#!/usr/bin/env python3
"""Fetch a GitHub user's public contribution calendar (no auth/token needed)
and write day-level data + derived stats to data/contributions.json.

Usage:
    python fetch_contributions.py <github-username>
    # or set GITHUB_USERNAME / GITHUB_REPOSITORY_OWNER in the environment
"""
import sys
import os
import json
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup


def get_username():
    if len(sys.argv) > 1:
        return sys.argv[1]
    env = os.environ.get(hex0n1) or os.environ.get(hex0n1)
    if env:
        return env
    raise SystemExit(
        "Usage: python fetch_contributions.py <github-username>  "
        "(or set GITHUB_USERNAME)"
    )


def fetch_calendar_html(username):
    url = f"https://github.com/users/hex0n1/contributions"
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-heatmap-script)"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html):
    soup = BeautifulSoup(html, "html.parser")
    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        date_str = cell.get("data-date")
        if not date_str:
            continue
        level = cell.get("data-level")
        count = 0
        cell_id = cell.get("id")
        tooltip = soup.select_one(f'tool-tip[for="{cell_id}"]') if cell_id else None
        if tooltip and tooltip.text:
            m = re.search(r"([\d,]+)\s+contribution", tooltip.text)
            if m:
                count = int(m.group(1).replace(",", ""))
        days.append(
            {
                "date": date_str,
                "count": count,
                "level": int(level) if level is not None else 0,
            }
        )
    days.sort(key=lambda d: d["date"])
    return days


def derive_stats(days):
    total = sum(d["count"] for d in days)

    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = {}
    for d in days:
        month = d["date"][:7]
        monthly[month] = monthly.get(month, 0) + d["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly": monthly,
    }


def main():
    username = get_username()
    html = fetch_calendar_html(username)
    days = parse_days(html)
    if not days:
        raise SystemExit(
            "No contribution cells found — GitHub's markup may have changed, "
            "or the username is wrong."
        )
    stats = derive_stats(days)

    os.makedirs("data", exist_ok=True)
    with open("data/contributions.json", "w") as f:
        json.dump(
            {
                "username": username,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "days": days,
                "stats": stats,
            },
            f,
            indent=2,
        )

    print(
        f"Wrote data/contributions.json — {stats['total']} contributions, "
        f"current streak {stats['current_streak']}d, longest streak {stats['longest_streak']}d"
    )


if __name__ == "__main__":
    main()
