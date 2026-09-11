#!/usr/bin/env python3
"""Aggregate the per-day snapshots into a single trends.json.

The dashboard needs the whole history to draw a trend, and fetching one file
per day does not scale. This walks YYYY/MM/DD/ and emits one compact file: a
sorted list of days plus, per satellite, the daily value of each tracked
counter (null where a day or a counter is missing).
"""

import json
import os
import re
import sys

SATELLITE_NAMES = {
    "us1.storj.io": "US1",
    "eu1.storj.io": "EU1",
    "ap1.storj.io": "AP1",
    "saltlake.tardigrade.io": "Salt Lake",
}

# Fixed display order, so a satellite always keeps the same categorical color.
SATELLITE_ORDER = ["US1", "EU1", "AP1", "Salt Lake"]

# Node counters to carry over, as output_name -> key in nodes.json.
NODE_FIELDS = {
    "active": "active_nodes",
    "suspended": "suspended_nodes",
    "disqualified": "disqualified_nodes",
    "exited": "exited_nodes",
}

# Counters for which zero cannot be a real observation: a satellite never has
# zero active nodes. Upstream reported 0 for at least one satellite on 21 days
# between 2026-06-19 and 2026-07-11 while inflating offline_nodes by the same
# amount. Plotted as zero those days read as a total network collapse, so they
# are recorded as missing instead.
ZERO_MEANS_MISSING = {"active"}

DAY_DIR = re.compile(r"^\d{2}$")
YEAR_DIR = re.compile(r"^\d{4}$")


def satellite_name(key):
    host = key.split("@")[1] if "@" in key else key
    host = host.rsplit(":", 1)[0]
    return SATELLITE_NAMES.get(host, host)


def find_days(root):
    for year in sorted(os.listdir(root)):
        if not YEAR_DIR.match(year):
            continue
        for month in sorted(os.listdir(os.path.join(root, year))):
            if not DAY_DIR.match(month):
                continue
            month_path = os.path.join(root, year, month)
            for day in sorted(os.listdir(month_path)):
                if not DAY_DIR.match(day):
                    continue
                day_path = os.path.join(month_path, day)
                if os.path.isdir(day_path):
                    yield f"{year}-{month}-{day}", day_path


def load(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError) as e:
        print(f"skipping {path}: {e}", file=sys.stderr)
        return None


def number(value):
    return value if isinstance(value, (int, float)) else None


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    days = []
    storage_by_day = {}
    nodes_by_day = {name: {} for name in NODE_FIELDS}
    seen = []
    dropped_zeros = 0

    for date, day_path in find_days(root):
        data = load(os.path.join(day_path, "data.json"))
        nodes = load(os.path.join(day_path, "nodes.json"))
        if data is None and nodes is None:
            continue

        storage = {}
        for key, val in (data or {}).items():
            name = satellite_name(key)
            if name not in seen:
                seen.append(name)
            storage[name] = number(val.get("storage_total_bytes"))

        counters = {field: {} for field in NODE_FIELDS}
        for key, val in (nodes or {}).items():
            name = satellite_name(key)
            if name not in seen:
                seen.append(name)
            for field, source_key in NODE_FIELDS.items():
                v = number(val.get(source_key))
                if v == 0 and field in ZERO_MEANS_MISSING:
                    dropped_zeros += 1
                    v = None
                counters[field][name] = v

        days.append(date)
        storage_by_day[date] = storage
        for field in NODE_FIELDS:
            nodes_by_day[field][date] = counters[field]

    # Known satellites first in their fixed order, then any newcomer as found.
    satellites = [s for s in SATELLITE_ORDER if s in seen]
    satellites += [s for s in seen if s not in satellites]

    def column(per_day, sat):
        return [per_day.get(d, {}).get(sat) for d in days]

    out = {
        "satellites": satellites,
        "days": days,
        "storage": {sat: column(storage_by_day, sat) for sat in satellites},
        "nodes": {
            field: {sat: column(nodes_by_day[field], sat) for sat in satellites}
            for field in NODE_FIELDS
        },
    }

    dest = os.path.join(root, "trends.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
        fh.write("\n")
    print(f"wrote {dest}: {len(days)} days, satellites: {', '.join(satellites)}, "
          f"{dropped_zeros} impossible zeros recorded as missing")


if __name__ == "__main__":
    main()
