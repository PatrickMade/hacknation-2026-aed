#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";

export * from "../../apptrick-design/scripts/sync-tokens.mjs";

const wrapper = fileURLToPath(import.meta.url);
const target = fileURLToPath(new URL("../../apptrick-design/scripts/sync-tokens.mjs", import.meta.url));
if (process.argv[1] && realpathSync(process.argv[1]) === realpathSync(wrapper)) {
  const result = spawnSync(process.execPath, [target, ...process.argv.slice(2)], { stdio: "inherit" });
  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  if (result.signal) process.kill(process.pid, result.signal);
  process.exit(result.status ?? 1);
}
