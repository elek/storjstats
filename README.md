# storjstats

Daily snapshots of the public Storj network stats from
https://stats.storjshare.io, plus a page to browse them.

## Layout

- `YYYY/MM/DD/` — one day's snapshot: `accounts.json`, `data.json`,
  `data-public.json` (from 2026-09-28), `nodes.json`, `nodes_geo.json`, as
  served upstream.
- `trends.json` — all days aggregated per satellite (storage, active /
  suspended / disqualified / exited nodes). Generated, don't edit.
- `index.html` — dashboard: per-day view and trend charts.

## How it runs

A GitHub Action (`.github/workflows/download.yml`) runs daily at 10:00 UTC:
`download.sh` fetches today's files, `build_trends.py` rebuilds
`trends.json`, and the result is committed.

US1 is shown as two satellites from 2026-09-28: `US1` is its public placement
(`data-public.json`), `US1-select` is `data.json` minus `data-public.json`.
For nodes, `US1-select` is US1's `active_select_nodes`; US1's own counts are
kept as reported.

Days with 0 active nodes for a satellite are recorded as missing: upstream
reported bogus zeros for several days in June–July 2026.

## Locally

```sh
./download.sh        # fetch today's snapshot (skips if it exists)
./build_trends.py    # regenerate trends.json
python3 -m http.server   # then open http://localhost:8000
```

`index.html` also works opened from disk; it falls back to fetching data from
raw.githubusercontent.com.
