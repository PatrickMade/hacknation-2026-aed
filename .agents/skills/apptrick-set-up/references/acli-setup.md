# Atlassian CLI setup

Use this flow only when Jira is the selected tracker and the local `acli` prerequisite is missing, incompatible, or unauthenticated. It is the setup skill's narrow exception to the rule that companion skills do not install dependencies.

## Reuse and verify first

1. Run `command -v acli`, then `acli --version` when found.
2. Require the minimum supported version `1.3.5`. Compare the numeric major, minor, and patch components rather than comparing the version text lexically. Also probe the command surface used by the Jira descriptor:

   ```bash
   acli jira workitem edit --help | grep -Fq -- '--remove-labels' &&
     acli jira workitem comment list --help | grep -Fq -- '--paginate' &&
     acli jira workitem comment update --help | grep -Fq -- '--body-file'
   ```

3. Capture `acli jira auth status` separately; the command has no JSON flag. Parse its `Site:` and `Email:` lines locally, compare both with the explicitly authorized `ATLASSIAN_SITE` and `ATLASSIAN_EMAIL`, and discard the raw output. Do not print account values. Authentication success against another target is a mismatch and stops before writes; never switch accounts automatically. A connected Jira app, MCP connector, API integration, or authenticated browser session does not prove that the local CLI is authenticated.
4. Reuse the installation without prompting only when compatibility, authentication, site, and account checks all pass. If the binary is compatible but authentication fails, keep it and use the OAuth recovery below when the user selected browser login; other approved methods remain in the Jira descriptor. Never ask the user to paste a token into chat, a command argument, or a committed file. In an unattended run, report `⚠️ NEEDS HUMAN CONFIRMATION: authenticate Atlassian CLI` and stop Jira operations.

## Permission and installation

When `acli` is absent, below the version floor, or lacks any required capability:

1. Ask once for explicit permission to install or upgrade the system CLI. Name the detected OS and the official Atlassian installation route you will use. If installation approval was already granted in the current session for this machine and target, continue without asking again.
2. Under `--defaults` or another unattended run with no prior approval, make no system change. Report `⚠️ NEEDS HUMAN CONFIRMATION: install Atlassian CLI`, include the official per-OS guide, and return control to the caller.
3. Detect the OS and architecture. Open the matching guide linked from Atlassian's [official installation guide](https://developer.atlassian.com/cloud/acli/guides/install-acli/) at execution time. Follow only the commands for that OS. A package-manager route is acceptable when it is the verified official route and requires no unapproved trust or privilege change. For every direct binary route on every operating system, verify an official published checksum or publisher signature before executing the downloaded binary. When neither proof is available, stop without executing or installing the binary. Do not silently install Homebrew, invoke `sudo`, add package repositories, change trust policy, or substitute a third-party package.
4. On macOS, when Homebrew is already installed, Atlassian documents:

   ```bash
   brew tap atlassian/homebrew-acli
   brew install acli
   ```

   Run these only after permission. If Homebrew rejects the tap as untrusted or asks for `brew trust --formula`, stop the Homebrew route and keep trust unchanged. With the same installation permission, use the architecture-specific binary linked by Atlassian's [macOS guide](https://developer.atlassian.com/cloud/acli/guides/install-macos/) only when you can verify its published checksum or macOS code signature, then place it in an existing user-owned directory on `PATH`. If no verified official binary route is available, report the trust boundary and leave installation to the user.
5. On other operating systems, use the current official per-OS guide. If its required step needs elevation, a package manager installation, or another trust change that was not approved, stop and name that boundary instead of widening the approval.

## OAuth browser success, terminal failure

The browser confirmation only completes the browser part of OAuth. The CLI must
remain running and select the intended site before authentication is ready. This
procedure resolved a macOS pilot failure with `timeout is not supported in accessible mode`; it is a targeted recovery, not a diagnosis of every OAuth error.

1. Keep one active login attempt. Stop the failed attempt you started before
   retrying; do not terminate unrelated CLI processes. Reuse the user's signed-in
   browser session, and start the CLI in a real interactive terminal or PTY with
   stdin kept open. Do not pipe the login through a logger or wait for the user
   after the CLI has already exited.
2. For the accessible-mode site-selector failure on macOS, Linux, or WSL, run:

   ```bash
   env -u NO_COLOR -u ACLI_ACCESSIBLE TERM=xterm-256color acli auth login
   ```

   These overrides apply to that process only. Never change shell profiles, global environment settings,
   accessibility preferences, CLI configuration, or callback routing to repair it.
   On Windows, use an interactive terminal and process-scoped equivalents only;
   this exact POSIX command was verified on macOS, not native Windows.
3. Let the user finish the authorization in the browser opened by this live
   attempt. If the CLI exposes a login URL, open that URL; do not guess a callback
   port or replay an old localhost URL. Return to the same terminal, finish the
   site selector, and wait for the CLI's successful exit.
4. Run `acli jira auth status`, compare its parsed site and email with the authorized target, then perform a read-only issue lookup through the selected Jira descriptor against a known issue in the intended project. Report success only after target comparison and issue readback pass. Do not print OAuth codes, email, account id, credential-store contents, or raw authentication logs.
5. If this targeted retry fails, retain the non-sensitive error and identify
   whether the browser callback, terminal selector, site access, or read-back
   failed. Stop repeating the same attempt. Do not switch to an API token,
   reinstall the CLI, or request wider permissions as an automatic fallback.
   Ask for the specific missing user action only when the evidence requires it.

## Post-install check and return

After installation or upgrade, run `acli --version`, repeat the three feature probes, and run `acli jira auth status` separately. Report the observed version and whether authentication is ready, without quoting identities or credentials. A failed compatibility check is an installation failure. A failed auth status requires authentication, not reinstallation.

When setup was entered from a Jira tracker operation, return control after every check passes. The original caller may retry its operation once from the beginning. Preserve the approval decision for the rest of the current session. Do not retry setup again from the same operation if the retry fails.
