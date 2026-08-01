#!/usr/bin/env python3
import json
from datetime import datetime, timedelta

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT_MARGIN = 30
TOP_MARGIN = 24
BOTTOM_MARGIN = 34
RIGHT_MARGIN = 12
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Python weekday(): Mon=0..Sun=6


def load_data(path="data/contributions.json"):
    with open(path) as f:
        return json.load(f)


def build_weeks(days):
    by_date = {d["date"]: d for d in days}
    if not days:
        return []
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    last = datetime.strptime(days[-1]["date"], "%Y-%m-%d")
    # rewind to the Sunday on/before the first day, GitHub's calendar starts on Sunday
    start = first - timedelta(days=(first.weekday() + 1) % 7)

    weeks, week, cur = [], [], start
    while cur <= last:
        key = cur.strftime("%Y-%m-%d")
        week.append(by_date.get(key, {"date": key, "count": 0, "level": 0}))
        if len(week) == 7:
            weeks.append(week)
            week = []
        cur += timedelta(days=1)
    if week:
        while len(week) < 7:
            week.append({"date": None, "count": 0, "level": 0})
        weeks.append(week)
    return weeks


def top_decile(days):
    counts = sorted(d["count"] for d in days if d["count"] > 0)
    if not counts:
        return None
    return counts[min(int(len(counts) * 0.9), len(counts) - 1)]


def level_for(day, threshold):
    lvl = day.get("level") or 0
    # push the very top of the real data into a 6th, brighter "neon" tier
    if lvl >= 4 and threshold is not None and day["count"] >= threshold:
        return 5
    return min(lvl, 5)


def month_labels(weeks):
    labels, seen = [], set()
    for i, week in enumerate(weeks):
        for day in week:
            if not day.get("date"):
                continue
            month = day["date"][:7]
            if month not in seen:
                seen.add(month)
                dt = datetime.strptime(day["date"], "%Y-%m-%d")
                labels.append((i, dt.strftime("%b")))
            break
    return labels


def esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render(data):
    days = data["days"]
    stats = data["stats"]
    weeks = build_weeks(days)
    threshold = top_decile(days)
    n_weeks = len(weeks)
    width = LEFT_MARGIN + n_weeks * STEP + RIGHT_MARGIN
    height = TOP_MARGIN + 7 * STEP + BOTTOM_MARGIN

    p = []
    p.append(
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'xmlns="http://www.w3.org/2000/svg" '
        'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">'
    )
    p.append(
        "<style>"
        ".cell{opacity:0;animation:reveal .5s ease-out forwards;}"
        "@keyframes reveal{0%{opacity:0;transform:translate(-6px,-6px);}"
        "100%{opacity:1;transform:translate(0,0);}}"
        ".lbl{fill:#8b949e;font-size:10px;}"
        ".stat{fill:#c9d1d9;font-size:12px;}"
        "</style>"
    )
    p.append(f'<rect width="{width}" height="{height}" fill="#0d1117"/>')

    for wd, label in DAY_LABELS.items():
        y = TOP_MARGIN + wd * STEP + CELL - 1
        p.append(f'<text x="4" y="{y}" class="lbl">{label}</text>')

    for week_idx, label in month_labels(weeks):
        x = LEFT_MARGIN + week_idx * STEP
        p.append(f'<text x="{x}" y="14" class="lbl">{label}</text>')

    delay_step = 0.012
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if not day.get("date"):
                continue
            color = PALETTE[level_for(day, threshold)]
            x = LEFT_MARGIN + wi * STEP
            y = TOP_MARGIN + di * STEP
            delay = (wi + di) * delay_step
            title = esc(f'{day["count"]} contributions on {day["date"]}')
            p.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2" ry="2" fill="{color}" style="animation-delay:{delay:.3f}s">'
                f"<title>{title}</title></rect>"
            )

    legend_y = height - BOTTOM_MARGIN + 18
    lx = LEFT_MARGIN
    p.append(f'<text x="{lx}" y="{legend_y + 8}" class="lbl">Less</text>')
    lx += 30
    for color in PALETTE:
        p.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" '
            f'rx="2" ry="2" fill="{color}"/>'
        )
        lx += STEP
    p.append(f'<text x="{lx + 4}" y="{legend_y + 8}" class="lbl">More</text>')

    footer = esc(
        f'{stats["total"]:,} contributions in the last year · '
        f'streak {stats["current_streak"]}d · longest {stats["longest_streak"]}d'
    )
    p.append(
        f'<text x="{width - RIGHT_MARGIN}" y="{legend_y + 8}" '
        f'text-anchor="end" class="stat">{footer}</text>'
    )

    p.append("</svg>")
    return "\n".join(p)


def main():
    data = load_data()
    svg = render(data)
    with open("contrib-heatmap.svg", "w") as f:
        f.write(svg)
    print("Wrote contrib-heatmap.svg")


if __name__ == "__main__":
    main()
