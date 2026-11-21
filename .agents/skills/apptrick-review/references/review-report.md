# Review and report - the apptrick-review-code pass plus the autofix loop

Detailed procedure for step 8 (full review pass) and step 11 (autonomous autofix and fix-forward loop) of `apptrick-review`. This skill is itself the automated second pass that other skills in this collection invoke; the review engine underneath is always the `apptrick-review-code` skill, used in delegated findings-only mode inside the isolated worktree, with the orchestrator owning command execution.

## Review pass (step 8)

Use `apptrick-review-code` in delegated findings-only mode against the PR diff. Inspect existing validation evidence under Verification reuse in `references/rules.md`. The orchestrator supplies current-candidate validation results with applicability reasons; the fresh reviewer verifies them without running commands or changing files. Explicitly verify:

- No public contract was broken silently: exported APIs, HTTP routes and response shapes, event names, CLI flags, DB schema, config formats. When `BACKWARD_COMPATIBILITY.md` exists at the repo root, check every touched surface against it - violations of its protected surfaces are Blockers and the review must explicitly WARN the user; honor any other documented compatibility rules.
- No security-sensitive surface was weakened: authentication, authorization, data scoping, input validation, secrets handling.
- Test coverage and cross-cutting impact.

## apptrick-review specifics - pass scope and gates (step 8)

- Scope changed files with the changed-file list from the tracker operation **get-pr-diff** for `{prNumber}`
- Gather context from the repository's agent-instruction and contributing docs covering the changed areas, plus the repo-local review checklist when the config's `reviewChecklist` points at one
- The orchestrator inspects existing evidence for every command in `validation.commands`, in order, for code PRs; for `SPEC_ONLY`, the docs-applicable subset and documented skips from `references/spec-review.md`. Run only missing or invalidated checks; carry valid delivery results into review without a second full gate. The reviewer audits the evidence and applicability to the current candidate; missing, stale, failed or unverifiable required results block approval
- Apply the full review checklist and the breaking-change checklist above
- Merge findings from step 7 (diff-level auto-detections) into the final review report. Do not duplicate the same issue twice.

## apptrick-review specifics - autonomous autofix flow (step 11)

The loop below runs only on **autofix-eligible** runs: `--autofix` was passed, or the stable run context records previously authorized implementation/fix scope for this PR. PR authorship, account identity, assignee, or claim ownership alone never grants edit authority. Otherwise skip branch mutation and end with review, labels, and handoff, noting `autofix: skipped (no authorized fix scope - re-run with --autofix to fix it here)`.

**Work order - binding, in this sequence:** (1) **any merge conflict against the latest base, always first**, including one that arose since step 4a and never deferred to a later pass - a conflicted branch makes every downstream signal unreliable, because the diff under review is not the diff that will merge; (2) **then the findings** - the test-evidence audit first, then fix batches with targeted validation, re-review, repeat; (3) **CI only once neither conflicts nor findings remain**, since resolving those changes what CI does on the next run anyway. The loop below implements stages 2 and 3.

When eligible: after posting a `changes_requested` review, **immediately proceed to fix every actionable in-scope blocker and major** (scope rule below) without asking the user - including the `INHERITED` ones collected in step 2 from the review feedback other reviewers already posted on the PR (`references/pr-metadata.md`), which are fixed on the same severity order as this run's own and reported per-item as fixed, deferred to a follow-up, or declined with a reason. The apptrick-review skill must be fully autonomous - it reviews, fixes, re-reviews, and iterates until the PR is merge-ready or a real blocker remains.

Only stop and ask the user in these critical situations:

- Ambiguous product or architecture decisions that could go multiple valid ways
- Missing credentials, environment access, or infrastructure failures
- Changes that would break public contracts in ways the project's compatibility rules do not allow
- Scope expansion that would fundamentally change what the PR does

For everything else, fix in-scope blockers and majors autonomously - including missing test evidence, type errors, lint failures, missing metadata exports, i18n problems and security defects in the changed code. Report out-of-scope findings and hardening, and in-scope minors/nits not needed for approval, as findings or follow-ups without implementing them.

## apptrick-review specifics - fix-forward loop (step 11)

Continue inside the isolated worktree. Do not stop after the first patch. Treat autofix as an iterative loop:

0. **Test evidence audit**: Before fixing code findings, check that each changed behavior has test evidence, in the diff (`*.test.*`, `*.spec.*`, `__tests__/*`, or the repo's equivalent) or as an existing test that exercises it. Add the smallest test only for an uncovered acceptance criterion, bug regression or material invariant. A diff without test files is not by itself a finding.
1. Convert the current review findings into a concrete fix list.
2. If the PR is currently conflicted, resolve conflicts against the latest base branch first.
3. Implement the next batch of fixable findings.
4. Run validation for the updated code:
   - Run the targeted subset of `validation.commands` relevant to the changed scope (the test and typecheck commands for the affected packages when the toolchain supports scoping; otherwise unscoped).
   - Trace changed inputs, environment and dependency paths; expand only to invalidated checks. Retain unaffected evidence with its current-candidate applicability reason; crossing a module/package boundary alone does not require another full gate.
5. Review the corrected delta and unresolved findings in the independent lane, retaining accepted unchanged scope. A specialist needs a concrete distinct risk or explicit project requirement.
6. If new or remaining actionable findings exist, repeat from step 1.
7. Stop only when:
   - the re-review outcome is `approved`, or
   - a real blocker remains that cannot be resolved autonomously in the current turn.

Examples of real blockers: ambiguous product or architecture decisions that require user input; environment or infrastructure failures unrelated to the changed code; missing credentials or missing external access.

Conflict-resolution rules for autofix mode:

- Resolve conflicts only inside the isolated worktree or carry-forward branch.
- Never attempt conflict resolution in the user's active worktree.
- Always fetch the latest `{baseRefName}` before resolving conflicts.
- After conflicts are resolved, rerun the relevant validation commands and the code review before deciding the branch is ready.
- If conflict resolution introduces additional findings, continue the autofix loop instead of stopping.

For autofix mode, the goal is not "submit one fix commit". The goal is "finish the PR". Keep iterating until the code review is clean and validation passes, unless a real blocker stops progress.

### Same-repo PRs

If the PR head branch is in the main repository and you have push access, implement the fixes on the checked-out PR branch, resolve any base-branch conflicts there if needed, run the autofix loop above, then commit and push to that branch only after the latest re-review is approvable.

Rules:

- Never force-push unless the user explicitly asked for it.
- Prefer a normal follow-up commit.
- Use conventional-commit-style messages scoped to the affected area: `fix(<area>): <summary>`, `feat(<area>): <summary>`, `refactor(<area>): <summary>`, etc.
- Before pushing, ensure the latest autofix cycle included tests, the targeted validation commands, and a fresh code review on the final diff.

### Fork PRs

For fork PRs, do not wait on the original author and do not push to the contributor's branch by default. Instead, keep the fetched PR head SHA (to preserve authorship), build a `carry/pr-{prNumber}-ready` branch in the main repo, run the autofix loop there, push it, open a replacement PR crediting the original author, and close the original only after the replacement exists. The full step sequence, the autofix validation requirements, the replacement-PR requirements, and the suggested body / handoff / closing-comment templates are in `references/fork-pr-flow.md`.
