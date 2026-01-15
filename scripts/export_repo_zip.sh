#!/usr/bin/env bash
set -euo pipefail

output_path=${1:-"polysport.zip"}
repo_root=$(git rev-parse --show-toplevel)

cd "$repo_root"

git archive --format=zip --output="$output_path" HEAD

echo "Created archive at $repo_root/$output_path"

if command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "$output_path"
elif command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$output_path"
else
  echo "SHA256 tool not found; skipping checksum."
fi
