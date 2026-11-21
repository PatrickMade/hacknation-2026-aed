#!/usr/bin/env node
// Compatibility entrypoint: preserve argv, stdout, stderr and exit status.
await import(new URL("../../apptrick-deliver/scripts/validate-issue-reference.mjs", import.meta.url));
