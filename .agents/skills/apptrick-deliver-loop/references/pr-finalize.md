# PR finalize - open, labels, summary comment, markers

The single procedure for the "commit → push → open (or reuse) the PR → normalize labels → summary comment → chaining reference lines" mechanics (the draft PR opens at step 7; reuse/labels at step 10, summary at step 12, ready-flip and ownership finalization at step 13). The point is **one** implementation of PR opening + labeling, reused rather than copied, and never a second PR for work that already has one.

## Specification before publication

Apply the Task specification gate from `references/agentic-setup.md` to the
candidate tree before commit or PR publication. Include the covering spec in the
branch and `Source doc:` in the body; verify coverage again after review fixes.
An incomplete draft states any gap and cannot be marked complete or ready.

## Never open a duplicate PR

Before opening anything, check whether a PR already exists for this branch (or one that references the run folder) via **search-prs** / **get-pr**. If one exists, **reuse it** - push new commits to its head branch and update its body/labels - never open a second PR. Only the skill that first opens the PR owns opening it; everyone else updates that same PR. (The step-2 slot check already routes an existing-PR run to `apptrick-continue-pr-loop`; this is the last line of defense.)

## Opening the PR (inline, via **create-pr**)

This skill always opens the PR inline - it does not delegate to `apptrick-open-pr`, because it owns the three-signal lock lifecycle and the run-folder contract itself (see specifics below). Commit the worktree changes with a conventional-commit subject carrying `TASK_COMMIT_PREFIX`, push the branch, open the PR via **create-pr** against `$BASE_BRANCH` with the body template below, and normalize labels per the section below.

## Early draft PR, then ready

The run **always** leaves a PR the user can watch, even when it never finishes:

1. **Open early as a draft** - right after the run-folder commit (skill step 7), open the PR with the draft flag, carrying the `Tracking plan:` line and `Status: in-progress`. Assign it, apply guarded `in-progress`, upsert the stable ownership marker with this `RUN_ID`, and re-read it before implementation (`references/claim-pr.md`). The run folder is committed, so an interrupted run leaves a draft PR carrying the plan/Tasks table rather than a run folder with no PR.
2. **Reuse it** - steps 8-13 update this same PR: checkpoint evidence + verification comments, the review pass, labels, the summary comment.
3. **Flip to ready at completion** - at cleanup (skill step 13), once `Status:` is `complete` (every Tasks row `done`), promote the draft with **mark-pr-ready**. A run that ends `in-progress` stays a draft for the user to resume.

## PR body

Use the template in `references/pr-body-template.md` - a title built per the PR title section below, and a body that **MUST** include the `Tracking plan:` line so `apptrick-continue-pr-loop` can resume. Flip `Status:` to `complete` on the PR body once every row in the Tasks table has `Status` = `done`.

## PR title

Build the title from the optional `prTitleTemplate` config key. A missing or empty key keeps the default format `{prefix}({area}): {summary}`, so existing projects see no change. When the key is empty and the repository's instructions require another task key/title convention, build that title and pass it as the caller-supplied title. Load these values in a shell; template and replacement values are literal data, never shell code (do not use `eval`):

```bash
PR_TITLE_TEMPLATE=$(jq -r '.prTitleTemplate // empty' "${CONFIG:-.ai/agentic.config.json}" 2>/dev/null) || PR_TITLE_TEMPLATE=""
[ -n "$PR_TITLE_TEMPLATE" ] || PR_TITLE_TEMPLATE='{prefix}({area}): {summary}'
TICKET_KEY_PATTERN=$(jq -r '.ticketKeyPattern // empty' "${CONFIG:-.ai/agentic.config.json}" 2>/dev/null) || TICKET_KEY_PATTERN=""
TICKET_KEY=""
if [ -n "$TICKET_KEY_PATTERN" ]; then
  TITLE_HEAD_BRANCH=${TITLE_HEAD_BRANCH:-$(git branch --show-current)}
  if TICKET_KEY_MATCHES=$(printf '%s\n' "$TITLE_HEAD_BRANCH" | grep -oE -- "$TICKET_KEY_PATTERN" 2>/dev/null); then
    TICKET_KEY=$(printf '%s\n' "$TICKET_KEY_MATCHES" | sed -n '1p')
  else
    MATCH_STATUS=$?
    [ "$MATCH_STATUS" -eq 1 ] || printf '%s\n' 'Warning: invalid ticketKeyPattern; using an empty ticket key.' >&2
  fi
fi

render_pr_title() {
  if [ -n "${5:-}" ]; then printf '%s\n' "$5"; return; fi
  jq -nr --arg template "$PR_TITLE_TEMPLATE" --arg prefix "$1" \
    --arg area "$2" --arg summary "$3" --arg issueId "${4:-}" \
    --arg ticketKey "$TICKET_KEY" '
    ($issueId | test("^[0-9]+$")) as $numeric |
    {prefix: $prefix, area: $area, summary: $summary,
     issue: (if $issueId == "" then "" elif $numeric
             then "#" + $issueId else $issueId end),
     issueRef: (if $issueId == "" then "" elif $numeric
                then " (#" + $issueId + ")" else " (" + $issueId + ")" end),
     ticketKey: $ticketKey} as $values |
    $template |
    (if $values.issue == "" then
       gsub("\\[\\{issue\\}\\] ?|\\(\\{issue\\}\\) ?|\\{issue\\} ?| ?\\{issue\\}"; "") else . end) |
    (if $values.ticketKey == "" then
       gsub("\\[\\{ticketKey\\}\\] ?|\\(\\{ticketKey\\}\\) ?|\\{ticketKey\\} ?| ?\\{ticketKey\\}"; "") else . end) |
    gsub("\\{(?<key>prefix|area|summary|issue|issueRef|ticketKey)\\}"; $values[.key]) |
    sub("\\s+$"; "")'
}
```

Call `render_pr_title` with five quoted arguments: conventional-commit type, primary area, one-line summary, provider-native issue id (or empty), and caller-supplied title (or empty). Capture its output for **create-pr**. Substitution happens once, so placeholder-like text inside a summary stays literal; wrapper cleanup applies only to template placeholders.

| Placeholder | Value |
|---|---|
| `{prefix}` | Conventional-commit type (`feat`, `fix`, `refactor`, ...). |
| `{area}` | Primary affected area. |
| `{summary}` | One-line behavioral summary. |
| `{issue}` | The subject issue as its tracker writes it: `#123` for a numeric GitHub id, the native key itself (`ENG-123`) otherwise. Empty without an issue. |
| `{issueRef}` | ` (#123)` or ` (ENG-123)` in an issue-driven run, else empty (the upstream suffix form). |
| `{ticketKey}` | First match of the `ticketKeyPattern` ERE in the head branch name (case-sensitive). Empty when the key is unset or nothing matches. |

An empty `{issue}` or `{ticketKey}` is removed together with a `[]` or `()` pair wrapped directly around it and one adjacent space, and a rendered title never ends in a space. A caller-supplied title always wins. Keep the conventional-commit type as the first word after any leading reference: `apptrick-update-changelog` reads it from there.

## Label normalization (step 11)

Apply labels from the config's taxonomy after opening the PR, always through the `apply_label` guard from the tracker descriptor (missing labels degrade to a logged skip; `labels.enabled: false` skips everything - note that in the summary comment). This is the canonical label contract for every PR-opening skill; `apptrick-open-pr` carries the same rules and the two must stay in sync.

- Apply the `review` pipeline label. New PRs always start in `review` unless the run terminated early with an explicit blocker.
- Add `skip-qa` **only** for clearly low-risk non-user-facing changes (docs-only, dependency-only, CI-only, test-only, trivial typos, single-file maintenance).
- Add `needs-qa` when the run touches UI or other user-facing behavior that requires manual exercise.
- Never add both `needs-qa` and `skip-qa`.
- Add additive category labels when they clearly apply: `bug`, `feature`, `refactor`, `security`, `dependencies`, `documentation`. Every PR carries at least one, because the changelog and release notes group PRs by category and print the title as a release-note line (a conventional title stating the user-visible effect). Pick it from what the PR changes for users, starting from its conventional-commit type, and add `security` next to `bug` or `dependencies` when the change closes a vulnerability:

  | Change | Category |
  |---|---|
  | fixes a vulnerability, an auth or data-scoping flaw, or a vulnerable dependency | `security` |
  | `feat` - new capability or public API | `feature` |
  | `fix` - incorrect behavior corrected | `bug` |
  | `refactor`, `perf`, `test`, `ci`, `build`, `chore` with no user-visible behavior change | `refactor` |
  | `deps` / `chore(deps)` - dependency bumps | `dependencies` |
  | `docs` only | `documentation` |

- Apply exactly one priority label. Infer it from the brief and the diff: outage, data loss, or a security incident → `priority-extreme`; security hardening or a release-blocking regression → `priority-high`; ordinary bug or feature → `priority-medium`; cosmetic, docs, dependency bumps, or cleanup → `priority-low`. Never open the PR without a priority.
- Apply exactly one risk label. Infer it from the changed behavior: a diff that widens access control (authorization, sessions, grants, tenant or scope filters), rewrites or deletes existing data or changes a migration runner, changes how money is computed or moved, changes module boundaries or state ownership, or breaks a published contract → `risk-high` (only tightening access, an additive migration with up/down evidence, display-only amount changes and stricter validation of invalid input are not high-risk on that ground; unclear direction counts as high-risk); an ordinary single-area change with tests → `risk-medium`; docs, dependency bumps, test-only, or isolated cleanup → `risk-low`. Never open the PR without a risk label.
- After applying the label set, post **one** consolidated rationale comment covering every applied label - never one comment per label (that spams the PR timeline and multiplies tracker API calls). Labels are still applied individually through the `apply_label` guard; only the commentary consolidates. The comment carries the standard idempotent marker, so a re-run updates it in place.
- When `qaGate` is `true`, a `needs-qa` PR will not be mergeable until QA signs off with `qa-approved`. Do not add `qa-approved` from this skill - it is earned by manual QA or the self-QA exception. State in the PR summary that manual QA is still pending.

Consolidated label-rationale comment - exactly **one** marker-idempotent comment from this skill per PR, listing only the labels actually applied: **one label per line**, each with its emoji from the map below and a full-sentence reason (drop lines for labels not applied; never compress into a `·`-concatenated one-liner). On any later label change, find the marker via **list-issue-comments** and rewrite this same comment via **update-comment** so it always describes the current label state; never post an additional per-change comment (no **update-comment** in the descriptor → post a replacement stating it supersedes the previous rationale):

```markdown
🤖 `apptrick-deliver-loop` - 🏷️ label rationale

- 🔍 `review` - ready for code review.
- ✨ `feature` - {why this category fits, one full sentence}.
- 🧪 `needs-qa` - {why manual QA is needed}.
- 🔺 `priority-high` - {why this priority}.
- 🟡 `risk-medium` - {why this risk}.
```

Label emoji map (decoration only - parsers key on the backticked label text): 🔍 `review` · ❌ `changes-requested` / `qa-failed` · 🧪 `qa` / `needs-qa` · 🚀 `merge-queue` · ⛔ `blocked` / `do-not-merge` · 🐛 `bug` · ✨ `feature` · ♻️ `refactor` · 🔒 `security` · 📦 `dependencies` · 📚 `documentation` · ⏭️ `skip-qa` · ✅ `qa-approved` · 📸 `qa-self-verified` · 🔥 `priority-extreme` · 🔺 `priority-high` · 🔹 `priority-medium` · 🔽 `priority-low` · ⚠️ `risk-high` · 🟡 `risk-medium` · 🟢 `risk-low` · 🤖 `in-progress` · ⏱️ `ci-monitoring`.

## Summary comment

Every run ends with one outcome and handoff comment: the run’s delta, verification result or evidence link, and next action. Keep the enduring explanation in the PR body; do not repeat its scope or label rationale. Post it via the tracker operation **comment-pr** with a body file so multi-line formatting is preserved. Full structure and rules: `references/summary-comment-template.md`. Never post it before the automated review loop (step 12) finishes, never claim a completion you did not reach, and never paste secrets into it.

## Marker emission

End the run's final report with the chaining reference lines, one per line, exact shape - include `Issue:` only when the run has a subject issue:

```
Issue: {#<number> for GitHub | <native-key> for Jira/Linear} (link: <full issue URL>)
PR: #<PR number> (link: <full PR URL>)
```

Chained consumers (`apptrick-review`, `apptrick-verify`, orchestration scripts) parse these exact text markers - never rename, translate, or decorate them.

## apptrick-deliver-loop specifics

- **Claim immediately after opening.** As soon as the draft PR opens, assign it, apply guarded `in-progress`, upsert the stable ownership marker for this `RUN_ID`, and re-read it. Preserve that claim through review; finalization writes and reads back `handoff`, `completed`, or `aborted` before any permitted label removal. Full sequence: `references/claim-pr.md`.
- **Checkpoint & final-gate verification on the PR.** The PR exists from step 7, so each checkpoint (step 8) and the final gate (step 9) post their verification outcome to the PR immediately - an idempotent `` 🤖 `apptrick-deliver-loop` - checkpoint <N> / final gate verification `` comment plus **attach-image-evidence** screenshots (marker `` 🤖 `apptrick-deliver-loop` - checkpoint <N> evidence ``, slug `checkpoint-<N>`) when UI was touched - never only in the run folder. Full procedure: `references/checkpoint-pass.md`.
- **Flip to ready at completion.** At step 13, once `Status:` is `complete` (every Tasks row `done`), promote the draft with **mark-pr-ready**; a run that ends `in-progress` stays a draft.
- **Final run-folder update lands under the lock.** If the PR was opened, write a final `HANDOFF.md` + `NOTIFY.md`, commit, and push before ownership finalization so the update lands under the same `RUN_ID` (step 13).
- **Simple runs** open the PR directly with a short body - summary + test plan + rollback; no `Tracking plan:` line, no `Status:` field, no linked run folder (`references/run-mode-contracts.md`). Label normalization and the lock lifecycle still apply in full.
