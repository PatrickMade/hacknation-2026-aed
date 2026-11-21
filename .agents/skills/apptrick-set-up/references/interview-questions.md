# Setup interview questions

The questions step 3 of `apptrick-set-up` asks the user (skipped with `--defaults`, which writes the auto-detected config without confirmation):

1. Confirm or edit the detected validation commands.
2. Which tracker provider to install (default: `github`):
   - `github` - issues, PRs, reviews, CI, and labels through the `gh` CLI.
   - `linear` - Linear issues through `schpet/linear-cli`, with GitHub as the required PR/review/CI companion. Setup installs both `linear.md` and `github.md`.
   - `jira` - Jira Cloud work items through an explicitly selected Atlassian MCP integration or Atlassian CLI (`acli`), with GitHub as the PR/review/CI companion when those stages are in scope. Full setup installs both descriptors.
   - a custom provider - scaffold from `TEMPLATE.md`; stop tracker-driven work until every required operation is filled in.

   This sets the config's `tracker` field to the selected primary descriptor. For Jira also select `trackerTransport` (`mcp` or `acli`) and the intended site/project identity. Verify only the clients required by the requested stage; the companion `gh` CLI is required before PR/review/CI work, not for Jira-only issue work. For `acli`, bind the intended account email in local session context, compare it and the site with the parsed auth status without logging their values, and reuse only a matching authenticated client. If it is missing or incompatible, ask for explicit permission to install the system CLI and follow [acli-setup.md](acli-setup.md). Under `--defaults` or another unattended run without prior installation approval, do not install it: report `⚠️ NEEDS HUMAN CONFIRMATION` and the required action. For MCP, verify the selected provider's complete required operation mapping and one scoped read; never install or switch to `acli` after an uncertain MCP mutation.
3. Which browser provider to install (default: `agent-browser`; `playwright` is
   the compatibility choice). Explain that the selected descriptor owns
   autonomous CLI/browser provisioning and that repository-native E2E suites
   remain authoritative.
4. Labels: install the full taxonomy above (recommended), keep a subset, or disable labels entirely.
5. QA gate on or off. Recommend on when the repo ships user-facing changes.
6. Where specs live (`paths.specs`, default `.ai/specs`) - confirm or point at an existing design-doc directory.
7. Optional repo-local review checklist path.
8. Project docs to generate (each only when missing): `SDLC.md` (recommended), `AGENTS.md` with the task-routing table (when no agent instruction file exists), `CODE_REVIEW.md`, and `BACKWARD_COMPATIBILITY.md`.
