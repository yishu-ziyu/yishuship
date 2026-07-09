#!/usr/bin/env bash
set -u

# Thin wrapper around validate-artifacts.sh.
# Re-computes and stores SHA256 checksums for .ship control files.
#
# Usage: update-checksums.sh [file ...]
#        update-checksums.sh --init

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

if [ "${1:-}" = "--init" ]; then
  shift
  exec "$SCRIPT_DIR/validate-artifacts.sh" --init "$@"
fi

exec "$SCRIPT_DIR/validate-artifacts.sh" --update "$@"
