---
name: apptrick-merge
description: "Use when merging a reviewed pull request with apptrick-merge, to re-check fresh gates and merge the exact reviewed head without a human approval."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-merge

Apply the installed skill with these changes (decision D3: agents merge to
the configured base branch after an independent review, green required checks
and the QA gate).

- **No approving review.** Skip the approve step. The author account cannot
  approve its own PR; the independent review record replaces it. Decision D3
  in `SDLC.md` ("Merge without a human gate") is the standing answer when the
  installed skill would ask whether to merge without an approval: do not ask.
- **Delivery mode.** Read `delivery.mode` from `.ai/agentic.config.json`
  (default `autonomous`, decision D3). Under `human-gated` do not merge: stop
  at merge-ready and report; a human merges.
- **Fresh gates.** Right before merging, read the PR again: it records
  passing results of every `validation.commands` entry for the current
  head; a missing result, or one for another head, refuses.
- **Merge gate.** Merge only with
  `python3 -B .ai/scripts/merge_gate.py --pr <number> --author-session <authoring session> --merge`,
  never with a bare `gh pr merge`. The authoring session comes from the run
  plan or the PR; without it the gate refuses (`author_session_missing`).
  The gate refuses unless:
  - the PR is open, not a draft, on the configured `baseBranch` (`auto`: the
    repository's default branch), MERGEABLE and CLEAN, and not behind the
    base;
  - it carries none of `qa-failed`, `do-not-merge`, `blocked`, `qa` (a
    tester is on it) and `in-progress`;
  - the latest independent review record on the current head says
    `Independent review: APPROVE` with `Head: <head>` and a
    `Reviewer session:` other than the author's: a COMMENT review (an
    APPROVED one also counts) whose `commit_id` is the head, from an OWNER,
    MEMBER or COLLABORATOR (apptrick-review extension). DISMISSED and
    PENDING reviews are ignored; a trusted CHANGES_REQUESTED review on the
    head refuses until a later approval record supersedes it;
  - every required check passed on the head; a PR with no required checks
    refuses;
  - unless `qaGate` is false, `qa_freshness.py check` passes for iOS and
    Android on that head, from trusted authors' comments; a PR that is
    `skip-qa` without `needs-qa` needs no verdict only when its diff since
    the merge base is test paths, CI or docs.

  A passing gate squash-merges exactly that head with `--match-head-commit`.
  Any refusal stops; read the PR state before any retry.
- **Readback.** Read the PR state and the base branch head: the PR is MERGED
  and its merge commit is the new base head.
- **Linear.** After the readback, move the issue to Done when the QA gate was
  satisfied (or `skip-qa`), and read the state back (decision D5).
- **Stops.** A merge that would trigger production publication or deployment
  is not covered by standing authority. No tag push, GitHub Release, build or
  publication follows from a merge. Never force-merge or bypass branch
  protection.
<!-- apptrick-harness:end -->
