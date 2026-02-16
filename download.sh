#!/bin/bash
set -euo pipefail

BASE_URL="https://stats.storjshare.io"
FILES="accounts.json nodes.json data.json nodes_geo.json"

dir="$(date +%Y/%m/%d)"

if [ -d "$dir" ]; then
    echo "Directory $dir already exists, skipping."
    exit 0
fi

mkdir -p "$dir"

for f in $FILES; do
    echo "Downloading $f -> $dir/$f"
    curl -sSf "$BASE_URL/$f" -o "$dir/$f"
done

echo "Done. Files saved to $dir/"
