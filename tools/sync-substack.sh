#!/usr/bin/env bash
# The publisher never operates in this working checkout. Substack blocks
# GitHub's servers, so the user timer invokes the local isolated publisher.
set -euo pipefail
exec "$HOME/Projects/code/home-ops/bin/actualspirit-sync" "$@"
