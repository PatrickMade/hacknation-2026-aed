#!/usr/bin/env node
// Compatibility entrypoint: preserve argv, stdout, stderr and exit status.
await import(new URL("../../apptrick-verify/scripts/validate-deployed-evidence.mjs", import.meta.url));
