---
name: apptrick-review
description: "Use when reviewing one pull request with apptrick-review, to apply the catalog routing and post the independent review record that the agent merge needs."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-review

## Project skill catalog

Follow `docs/AGENT-SKILL-CATALOG.md` for exact-source procedure routing. Resolve
required procedures through project-aware `find-skills`; preserve native
invocation restrictions and the complete upstream workflow.

## Independent review record

Agents merge after an independent review (decision D3). The review is
independent when it runs in a session that did not author the change.

- Apply the apptrick-review-code extension checklist.
- Post the verdict as a PR review with event COMMENT whose `commit_id` is the
  current head. Its body carries the lines `Independent review: APPROVE` (or
  `Independent review: CHANGES_REQUESTED`), `Head: <sha>` and
  `Reviewer session: <id>`, plus the model, the scope and a verdict summary.
- The project's one account may post it: the author account cannot approve
  its own PR on GitHub, and the record replaces that approval. Independence
  is the session, not the account: the merge gate refuses a record whose
  `Reviewer session:` is the authoring session (`--author-session`), so a
  second account is optional. The gate counts a record only from an OWNER,
  MEMBER or COLLABORATOR, in a COMMENTED or APPROVED review. A DISMISSED or
  PENDING review is ignored; a trusted CHANGES_REQUESTED review on the head
  refuses the merge until a later approval record. Any new commit needs a
  new record.
- Run without `--autofix`: a reviewer that commits a fix becomes that fix's
  author, so the fix needs a record from another session. Report the findings
  and leave fixes to an authoring session (apptrick-deliver extension,
  "Independent review").

## Linear states

After posting the record, move the Linear issue with
`.ai/scripts/apptrick_linear.py transition-issue` (contract
`.ai/trackers/linear-adapter.md`), which reads the state back (decision D5): on APPROVE, Review to QA when the PR
carries `needs-qa` (a `skip-qa` PR stays in Review until the merge moves it to
Done); on CHANGES_REQUESTED, back to In Progress.
<!-- apptrick-harness:end -->
