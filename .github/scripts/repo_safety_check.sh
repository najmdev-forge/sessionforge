#!/usr/bin/env bash
# Repository safety checks for sessionforge.
# Runs the same checks in CI and locally before pushing, so a new check is added as a
# function here instead of a new inline step in the workflow file.
#
# Usage:
#   .github/scripts/repo_safety_check.sh [<base> <head>]
#
# Without arguments, compares origin/main against HEAD, for a local check before pushing.
# In CI, the workflow passes the pull request base and head commit SHAs explicitly.

set -euo pipefail

base="${1:-origin/main}"
head="${2:-HEAD}"

failures=0

check_no_local_paths() {
  echo "== Check: no local only paths in diff =="

  local changed
  changed=$(git diff --name-only "$base" "$head")
  local failed=0

  if echo "$changed" | grep -qE '(^|/)local/'; then
    echo "FAIL: files under a local/ directory must not be committed."
    echo "$changed" | grep -E '(^|/)local/'
    failed=1
  fi

  if echo "$changed" | grep -q '\.local\.'; then
    echo "FAIL: files with .local. in the name must not be committed."
    echo "$changed" | grep '\.local\.'
    failed=1
  fi

  if [ "$failed" -eq 0 ]; then
    echo "PASS: no local only paths in diff."
  else
    failures=$((failures + 1))
  fi
}

check_no_local_paths

echo
if [ "$failures" -eq 0 ]; then
  echo "All repository safety checks passed."
  exit 0
else
  echo "$failures repository safety check(s) failed."
  exit 1
fi
