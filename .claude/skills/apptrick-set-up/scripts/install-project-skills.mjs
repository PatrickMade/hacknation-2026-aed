#!/usr/bin/env node
// apptrick- edition installer: the shipped command line, running the bundled transform.
//   node install-project-skills.mjs --source <checkout> --project <root> [--check] [--revision <sha>]
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const args = process.argv.slice(2)
const check = args.includes('--check')
const rest = args.filter((value) => value !== '--check')
const tool = path.join(path.dirname(fileURLToPath(import.meta.url)), 'apptrick_skills.py')
const result = spawnSync('python3', ['-B', tool, check ? 'check' : 'install', ...rest], { stdio: 'inherit' })
if (result.error) console.error(`apptrick installer: cannot run python3 (${result.error.message})`)
else if (result.status === null) console.error(`apptrick installer: transform stopped by signal ${result.signal}`)
process.exit(result.status === null ? 1 : result.status)
