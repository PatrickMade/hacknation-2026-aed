#!/usr/bin/env sh
# Compatibility entrypoint for the renamed workflow classifier.
set -u

SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd) || exit 2
exec sh "$SCRIPT_DIR/../../apptrick-improve-workflow/references/classify-runs.sh" "$@"
