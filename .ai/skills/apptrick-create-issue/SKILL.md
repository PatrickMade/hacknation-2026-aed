---
name: apptrick-create-issue
description: "Use when filing a new task with apptrick-create-issue, to create it in the bound Linear project after a full duplicate search."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-create-issue

Apply the installed skill.

- Create issues only in the Linear workspace, team and project bound in
  `.ai/agentic.config.json`, with `.ai/scripts/apptrick_linear.py create-issue`
  (contract `.ai/trackers/linear-adapter.md`); `--route` selects the bound
  project. Read the binding back before the first write.
- Search the routed project to the last page before creating:
  `apptrick_linear.py search-issues --route <route>` lists every issue, and
  `--query <text>` narrows by title or description. Deduplicate semantically
  over the full list. An incomplete search is `SEARCH_UNAVAILABLE` and stops
  the create.
- Title: a title given by the owner, the brief or a parent issue is used
  verbatim. Otherwise write a short imperative title that names the change
  (`Add a settings reset button`), without an `Implement:` or `Fix:` prefix; the
  `bug` or `feature` label carries the category. This replaces the installed
  skill's title rule.
- Routine Linear writes are standing-authorized: create the issue, its labels
  and a milestone without asking (decision D6), then read each one back.
  Deleting or archiving anything in Linear needs the owner's approval.
- A new issue starts in Backlog, or in Ready when it meets the ticket-level
  Definition of Ready in `SDLC.md`.
- Never create an issue per thread: review and continuation threads reuse the
  existing issue.
<!-- apptrick-harness:end -->
