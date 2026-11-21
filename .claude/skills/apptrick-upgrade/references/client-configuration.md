# Verify project-owned client configuration

Package integrity and client configuration are separate checks. After installing
and checking the package, inventory the project's actual agent configuration:
`.claude/`, `.agents/`, `.codex/`, root `.mcp.json`, `agent-browser.json`, `AGENTS.md`
and `CLAUDE.md`, plus any discovered project-owned client declaration elsewhere.
Read applicable nested project instructions. Do not inspect global settings or
credential stores. Never silently approve an unknown hook or MCP command.

For a new project, create `.ai/client-config.json` after reviewing the intended
files. For an existing project, compare with its recorded inventory first; show
intentional additions/updates before recording their new hashes. A drift failure
is not fixed by automatically recalculating every hash. Preserve project-owned
rules, allowed configuration and package/local-extension ownership. The manifest
is reviewed configuration, not a security signature or independent attestation.

Schema (version 1): `roots` is exactly `[".agents", ".claude", ".codex"]`;
`packageRoots` is exactly `[".agents/skills", ".claude/skills"]`; `personalFiles`
lists the applicable ignored personal settings (`.claude/settings.local.json`
and optionally `.codex/config.local.toml`); `files` maps every other regular
project-owned configuration file to its SHA-256. Include root declarations and
instructions when present. Do not include package descendants, the manifest
itself, secrets or personal settings. Ensure selected personal paths are actually
ignored and not already tracked: adding `.gitignore` does not untrack a file.
Do not invent client-specific settings files that the project does not use.

Run `node scripts/check-project-config.mjs --project <absolute-target>` from this
skill directory. The checker reads the manifest, rejects symlinks/path escapes,
checks complete client-directory coverage and file hashes, and queries the Git
index for personal settings. Its package-root exemptions must be checked by the
separate source-anchored package verifier. Existing project verifiers remain
valid when they demonstrably cover these surfaces; do not replace one merely to
standardize its language.

Report package integrity, client configuration and observed live client discovery
separately. A clean manifest cannot prove that a client loaded the skills or that
MCP permissions are correct. Run the actual client discovery checks supported by
the project; unavailable clients stay not tested. Windows needs its own execution.
