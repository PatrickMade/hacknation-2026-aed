#!/usr/bin/env node
// Compatibility entrypoint: preserve argv, stdout, stderr and exit status.
await import(new URL("../../apptrick-guide-qa/scripts/render-runbook.mjs", import.meta.url));
