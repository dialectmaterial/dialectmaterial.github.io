#!/usr/bin/env bash
# Bring in new Substack posts, make their share images and publish them.
# Runs daily on this computer (systemd timer "actualspirit-sync"); Substack
# blocks GitHub's own servers, so this can't run as a GitHub Action.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${ACTUALSPIRIT_PYTHON:-$HOME/.local/share/actualspirit/venv/bin/python}"

git pull -q --rebase --autostash
"$PY" tools/import-substack.py
"$PY" tools/make-share-images.py
git add -A _posts assets
if git diff --cached --quiet; then echo "Nothing new on Substack."; exit 0; fi
git commit -q -m "Import new posts from Substack" -- _posts assets
git push -q
echo "Published new posts."
