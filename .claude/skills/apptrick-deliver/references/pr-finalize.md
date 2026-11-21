# PR finalize - open or reuse, labels, summary comment, markers

The single procedure for the "commit → push → open (or reuse) the PR → normalize labels → summary comment → chaining reference lines" mechanics (steps 10 and 12 of the skill body). The point is **one** implementation of PR opening + labeling, reused rather than copied, and never a second PR for work that already has one.

## Specification before publication

Apply the Task specification gate from `references/agentic-setup.md` to the
candidate tree before commit or PR publication. Include the covering spec in the
branch and `Source doc:` in the body; verify coverage again after review fixes.
An incomplete draft states any gap and cannot be marked complete or ready.

## Never open a duplicate PR

Before opening anything, check whether a PR already exists for this branch (or, in an issue-driven run, one that references the issue) via **search-prs** / **get-pr**. If one exists, **reuse it** - push new commits to its head branch and update its body/labels - never open a second PR. Only the skill that first opens the PR owns opening it; everyone else updates that same PR.

## Prefer the `apptrick-open-pr` skill when installed

`apptrick-open-pr` already implements exactly this: it commits the worktree, pushes the branch, opens a **ready-for-review** PR against `$BASE_BRANCH` (draft only with `--draft`) with the unified body template, applies the full SDLC label set (pipeline `review`, category, QA meta, one priority, one risk) through the descriptor guards with rationale comments, posts the caller's summary comment, and (in an issue-driven run) hands the issue back and releases the `in-progress` lock - emitting the `PR:` / `Issue:` chaining reference lines. When it is installed, **delegate to it** instead of re-deriving the steps:

- Issue-driven run (an `{issueId}` is in scope): invoke `apptrick-open-pr {issueId} {category}` (add `--plan <path>` when an execution plan exists, `--draft` for a spec-only design PR) and capture the PR number and URL from its `PR:` reference line.
- Brief- or spec-driven run (no issue - e.g. `apptrick-deliver`): invoke it without `{issueId}`; the issue-handback and lock-release parts don't apply.

## Graceful fallback when `apptrick-open-pr` is NOT installed

`apptrick-open-pr` is an **optional** enhancement - a repo may install this skill without it, and it must still work. When `apptrick-open-pr` is absent, perform the mechanics inline:

1. Commit the worktree changes with a conventional-commit subject carrying `TASK_COMMIT_PREFIX`; push the branch.
2. Open the PR via the tracker operation **create-pr** against `$BASE_BRANCH`, with the body template below.
3. Normalize labels per the section below.

Detect availability simply: if invoking `apptrick-open-pr` is not possible in this environment (skill not present), take the inline path. Behavior is identical either way - the same PR, the same labels - so installing `apptrick-open-pr` only removes duplication, it never changes the outcome.

## One PR; early draft only when useful

A small agreed change is implemented and verified first, then published once; the task branch is pushed from the plan commit onward. An interrupted run that has not opened its PR reports its pushed branch and this resume command: `apptrick-deliver --spec <SPEC_PATH> --run-id <RUN_ID>` (add `--issue <ref>` when a task is bound). Routing (`references/task-routing.md` section 1) then opens the bare draft PR on that branch, claims it and continues through `apptrick-continue-pr`.

1. **Open once** - by default when the validation gate passes (skill step 10), open the PR via **create-pr** with the draft flag for the review loop, carrying the body template's `Tracking plan:` line and `Status: in-progress`. Open a bare early draft right after the plan's first commit (skill step 8) only when collaboration, recovery of long work or explicit project policy needs early visibility. Keep the opening bare - no labels, no summary yet. (Do **not** delegate this open to `apptrick-open-pr` - that skill also applies labels and posts a summary, which belong at steps 11-13.)
2. **Reuse it** - steps 11-13 update this same PR (never open a second one): apply labels (delegating to `apptrick-open-pr`'s reuse path when installed - it refreshes the body and labels without disturbing the draft state), run the review pass, post the summary comment.
3. **Flip to ready at completion** - at cleanup (skill step 13), once `Status:` is `complete` (all Progress steps `- [x]`), promote the draft with **mark-pr-ready**. A run that ends `in-progress` stays a draft for the user to resume. A spec-only design PR stays draft by intent.

## Verification comments on the PR

Verification proofs land on the PR, not only in the plan. Keep the validation outcome and material limits in the PR body; the end-of-run comment links its evidence; when a verification (validation gate, integration or UI check) runs mid-flight and is worth surfacing before the summary, post it as its own idempotent comment with the marker `` 🤖 `apptrick-deliver` - verification `` (re-run updates it in place). Attach screenshots via **attach-image-evidence** whenever UI was touched.

## PR body

Use the template in `references/pr-body-template.md` - a title built per the PR title section below, and a body that **MUST** include the `Tracking plan:` line so `apptrick-continue-pr` can resume. Flip `Status:` to `complete` on the PR body once all Progress steps are checked.

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

## Label normalization

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

- Apply exactly one priority label. Infer it from the brief and the diff: outage, data loss, or a security incident → `priority-extreme`; security hardening or a release-blocking regression → `priority-high`; ordinary bug or feature → `priority-medium`; cosmetic, docs, dependency bumps, or cleanup → `priority-low`.
- Apply exactly one risk label. Infer it from the changed behavior: a diff that widens access control (authorization, sessions, grants, tenant or scope filters), rewrites or deletes existing data or changes a migration runner, changes how money is computed or moved, changes module boundaries or state ownership, or breaks a published contract → `risk-high` (only tightening access, an additive migration with up/down evidence, display-only amount changes and stricter validation of invalid input are not high-risk on that ground; unclear direction counts as high-risk); an ordinary single-area change with tests → `risk-medium`; docs, dependency bumps, test-only, or isolated cleanup → `risk-low`.
- After applying the label set, post **one** consolidated rationale comment covering every applied label - never one comment per label (that spams the PR timeline and multiplies tracker API calls). Labels are still applied individually through the `apply_label` guard; only the commentary consolidates. The comment carries the standard idempotent marker, so a re-run updates it in place.
- When `qaGate` is `true`, a `needs-qa` PR will not be mergeable until QA signs off with `qa-approved`. Do not add `qa-approved` from this skill - it is earned by manual QA or the self-QA exception. State in the PR summary that manual QA is still pending.

Consolidated label-rationale comment - exactly **one** marker-idempotent comment from this skill per PR, listing only the labels actually applied: **one label per line**, each with its emoji from the map below and a full-sentence reason (drop lines for labels not applied; never compress into a `·`-concatenated one-liner). On any later label change - a pipeline transition, a priority/risk adjustment - find the marker via **list-issue-comments** and rewrite this same comment via **update-comment** so it always describes the current label state; never post an additional per-change comment (when the descriptor lacks **update-comment**, post a replacement stating it supersedes the previous rationale):

```markdown
🤖 `apptrick-deliver` - 🏷️ label rationale

- 🔍 `review` - ready for code review.
- ✨ `feature` - {why this category fits, one full sentence}.
- 🧪 `needs-qa` - {why manual QA is needed}.
- 🔺 `priority-high` - {why this priority}.
- 🟡 `risk-medium` - {why this risk}.
```

Label emoji map (decoration only - parsers key on the backticked label text): 🔍 `review` · ❌ `changes-requested` / `qa-failed` · 🧪 `qa` / `needs-qa` · 🚀 `merge-queue` · ⛔ `blocked` / `do-not-merge` · 🐛 `bug` · ✨ `feature` · ♻️ `refactor` · 🔒 `security` · 📦 `dependencies` · 📚 `documentation` · ⏭️ `skip-qa` · ✅ `qa-approved` · 📸 `qa-self-verified` · 🔥 `priority-extreme` · 🔺 `priority-high` · 🔹 `priority-medium` · 🔽 `priority-low` · ⚠️ `risk-high` · 🟡 `risk-medium` · 🟢 `risk-low` · 🤖 `in-progress` · ⏱️ `ci-monitoring`.

## Summary comment

Every run ends with one outcome and handoff comment: the run’s delta, verification result or evidence link, and next action. Keep the enduring explanation in the PR body; do not repeat its scope or label rationale. Post it via the tracker operation **comment-pr** with a body file so multi-line formatting is preserved. Full structure and rules: `references/summary-comment-template.md`. Never post it before the automated review loop (step 11) finishes, never claim a completion you did not reach, and never paste secrets into it.

## Marker emission

End the run's final report with the chaining reference lines, one per line, exact shape - include `Issue:` only when the run has a subject issue:

```
Issue: {#<number> for GitHub | <native-key> for Jira/Linear} (link: <full issue URL>)
PR: #<PR number> (link: <full PR URL>)
```

Chained consumers (`apptrick-review`, `apptrick-verify`, orchestration scripts) parse these exact text markers - never rename, translate, or decorate them.
