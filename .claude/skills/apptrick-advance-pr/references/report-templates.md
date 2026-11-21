# PR driver reports

Follow `references/rules.md`. The PR body explains the change; this skill reports
what remains after the chain. Keep diagnosis and per-step logs out of the summary
unless they explain a blocker. A dry run prints the proposed chain and reasons
without posting anything.

## 1. Summary comment on the PR

Find the existing marker via **list-issue-comments** and update it through
**update-comment**. Match the stable `apptrick-advance-pr` / `run at` prefix rather
than the timestamp; accept the legacy bare skill name and the legacy em dash (U+2014) separator. If editing is unsupported,
post a replacement identifying the earlier report it supersedes.

```markdown
🤖 `apptrick-advance-pr` - run at {UTC timestamp}

**{Merge-ready | waiting for QA | blocked | needs a decision}:** {reason and current behavior changed, in one sentence}.
{Only consequential changes from this chain, with links to review, QA evidence, or follow-up issues.}
🧪 {Required CI status at this head; QA result or missing sign-off.}
🔁 {Next action and who owns it; state when --allow-merge was absent or a requested merge actually happened.}
```

Aim for 40-100 words; keep all remaining blockers and pending check names.
Include a short chain table only when several step outcomes explain the result.
Do not paste the ten-signal diagnosis, file inventory, or all prior findings.

## 2. Label set

Derive the full intended set from the diff and the repository's agent
instructions, which own the taxonomy. This skill applies the derivation, never
its own vocabulary:

- **pipeline** (exactly one): the review state while under review, the
  changes-requested state on a failed review, the merge-queue state when
  approved and green, the blocked state on a genuine blocker. **Never set the
  manual-QA-in-progress state** - that one is driven by QA reviewers only.
- **category** (additive): whatever the repository defines (bug, feature,
  refactor, security, dependencies, documentation, …), picked from what the PR
  changes for users: a closed vulnerability → security (next to bug or
  dependencies), feat → feature, fix → bug, behavior-neutral refactor/perf/test/
  ci/build/chore → refactor, dependency bumps → dependencies, docs only →
  documentation.
- **meta**: QA-required for user-facing behavior, QA-skipped for
  docs/dependency/CI/test-only changes. Never both. The evidence label when UI
  evidence was posted.
- **priority** (exactly one, inferred when absent): outage, data loss, or a
  security incident → the highest; security hardening, a release-blocking
  regression, or auth/session/tenant-scope/money/event-reliability work → high;
  an ordinary fix or feature → medium; cosmetic, docs, dependency bumps, or
  cleanup → low. Conflicting signals → the higher one, and say why.
- **risk** (exactly one, inferred when absent): a diff that widens access
  control (authorization, sessions, grants, tenant or scope filters), rewrites or
  deletes existing data or changes a migration runner, changes how money is
  computed or moved, changes module boundaries or state ownership, or breaks a
  published contract → high (only tightening access, an additive migration with
  up/down evidence, display-only amount changes and stricter validation of
  invalid input are not high-risk on that ground; unclear direction counts as
  high); an ordinary single-module change shipping
  with tests → medium; docs, dependencies, test-only, typo, or cosmetic → low.

Keep the full applied set in one marker-idempotent
`` 🤖 `apptrick-advance-pr` - 🏷️ label rationale `` comment, updated through
**update-comment**. Use one concise reason per label; link this comment from the
run summary only when a label issue affects the next action.

**No triage rights:** an account without them cannot apply labels, and the guard
reports a permission error. Do not retry or work around it - list the intended
set in the label-rationale comment, distinguish it from applied labels, and name
the maintainer action in the summary and session handoff.

## 3. Session report

Return the outcome and next action in 3-6 lines, linking the PR summary and any
material evidence. Include a permissions gap or unresolved decision if it remains.
Do not repeat the tracker report. For `--dry-run`, show the diagnosis needed to
understand the proposed chain and a one-line reason per step; say it was not run.
End with exact chaining fields (issue only when the run has one):

```text
PR: #{number} (link: {url})
Issue: {#number for GitHub | native-key for Jira/Linear} (link: {url})
```

## 4. Evidence limits

- Name any required gate not run and why; never infer a pass.
- QA pass requires attached evidence; link it rather than repeating it.
- Report a merge only when `--allow-merge` was passed and it actually happened.
- A requested label is not an applied label; report guard permission failures.
