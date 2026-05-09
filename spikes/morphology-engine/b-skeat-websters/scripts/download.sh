#!/usr/bin/env bash
# Download GCIDE 0.54 (GNU Collaborative International Dictionary of English),
# the structured/maintained corpus of Webster's 1913 + supplements.
# Output: ../data/gcide-0.54/CIDE.{A..Z} (gitignored).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data"
TARBALL="$DATA_DIR/gcide-0.54.tar.xz"
EXTRACT_DIR="$DATA_DIR/gcide-0.54"

# Pinned to a specific tarball name on FSF FTP.
URL="https://ftp.gnu.org/gnu/gcide/gcide-0.54.tar.xz"

mkdir -p "$DATA_DIR"

if [[ -d "$EXTRACT_DIR" && -f "$EXTRACT_DIR/CIDE.A" ]]; then
  echo "Already extracted: $EXTRACT_DIR ($(ls $EXTRACT_DIR/CIDE.* 2>/dev/null | wc -l | tr -d ' ') letter files)"
  exit 0
fi

if [[ ! -f "$TARBALL" ]]; then
  echo "Downloading $URL"
  curl -fL -o "$TARBALL" "$URL"
fi

echo "Extracting to $DATA_DIR"
tar -xJf "$TARBALL" -C "$DATA_DIR"
echo "Done: $EXTRACT_DIR ($(ls $EXTRACT_DIR/CIDE.* 2>/dev/null | wc -l | tr -d ' ') letter files)"
