#!/usr/bin/env node
// Compatibility entrypoint: preserve argv, stdout, stderr and exit status.
await import(new URL("../../apptrick-set-up/scripts/install-project-skills.mjs", import.meta.url));
