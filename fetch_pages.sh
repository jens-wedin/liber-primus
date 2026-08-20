#!/usr/bin/env bash
# Fetch the complete Liber Primus page images (the "book") into data/pages/.
# ~75 JPEG scans (2400x3600), ~50 MB total — gitignored, not vendored, since
# they are the primary source the rune transcription (data/liber_primus.md) was
# made from. Source: scream314/cicada3301, assets/2014/liber-primus-complete/.
#
# Usage: bash fetch_pages.sh
set -euo pipefail

REPO="scream314/cicada3301"
BRANCH="master"
SRCDIR="assets/2014/liber-primus-complete"
OUT="data/pages"

mkdir -p "$OUT"
echo "Listing $SRCDIR in $REPO ..."
paths=$(gh api "repos/$REPO/git/trees/$BRANCH?recursive=1" \
          -q '.tree[].path' \
        | grep -E "^$SRCDIR/.*\.(jpg|jpeg|png)$" | sort)

n=0
while read -r p; do
  [ -z "$p" ] && continue
  curl -sSL --max-time 60 -o "$OUT/$(basename "$p")" \
    "https://raw.githubusercontent.com/$REPO/$BRANCH/$p"
  n=$((n + 1))
done <<< "$paths"

echo "Downloaded $n page images -> $OUT/ ($(du -sh "$OUT" | cut -f1))"
