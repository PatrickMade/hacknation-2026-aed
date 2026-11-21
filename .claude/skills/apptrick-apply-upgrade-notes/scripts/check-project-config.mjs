#!/usr/bin/env node
// Compatibility entrypoint: preserve argv, stdout, stderr and exit status.
await import(new URL("../../apptrick-upgrade/scripts/check-project-config.mjs", import.meta.url));
