#!/usr/bin/env bash
# Download MorphyNet's English derivational TSV at a pinned commit.
# Output: ../data/eng.derivational.v1.tsv (gitignored).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data"
DEST="$DATA_DIR/eng.derivational.v1.tsv"

# Pinned to MorphyNet main @ this SHA so re-runs fetch the same data.
COMMIT_SHA="378144f64df58c78db5245af19d16a511ccecf3a"
URL="https://raw.githubusercontent.com/kbatsuren/MorphyNet/${COMMIT_SHA}/eng/eng.derivational.v1.tsv"

mkdir -p "$DATA_DIR"

if [[ -f "$DEST" ]]; then
  echo "Already downloaded: $DEST ($(wc -l < "$DEST") rows)"
  exit 0
fi

echo "Downloading $URL"
curl -fL -o "$DEST" "$URL"
echo "Done: $DEST ($(wc -l < "$DEST") rows)"
