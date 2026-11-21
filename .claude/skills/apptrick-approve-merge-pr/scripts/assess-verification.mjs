#!/usr/bin/env node
// Compatibility entrypoint: preserve argv, stdout, stderr and exit status.
await import(new URL("../../apptrick-merge/scripts/assess-verification.mjs", import.meta.url));
