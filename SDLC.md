# Software delivery process

## Purpose

This file documents how work flows from ticket to merged PR in this repository. The agent skills configured in `.ai/agentic.config.json` enforce the process; humans read it here. PRs target the base branch, `baseBranch` in `.ai/agentic.config.json` (`auto`: the repository's default branch); issues live in Linear and PRs on GitHub, with every tracker operation the skills run defined in `.ai/trackers/linear.md` and `.ai/trackers/github.md` (edit those files to extend or override tracker behavior). The Linear adapter (`.ai/trackers/linear-adapter.md`, tool `.ai/scripts/apptrick_linear.py`) overrides the Linear descriptor for issue search, claims, labels, state moves and provisioning.

Work enters through two paths: a free-form task brief handed to an agent, or a filed ticket. Both converge on the same review loop, the same validation gate, and the same merge gates.

Before intake, the work is shaped: `apptrick-discover` establishes the product context every later decision reads (`.ai/specs/product-brief.md` - who the users are, what hurts, what the product is not, which rules and decisions bind the work), `apptrick-brainstorm` turns a single idea or question into a routing decision and a brief, and the spec skills (`apptrick-specify`, `apptrick-publish-spec`) turn a feature into a design document before anything is built. Those steps feed the table below; they are not the ticket flow itself, and the Definition of Ready is the contract between them and Intake.

## Roles

- **Author** - the human or agent who writes the change. Owns the ticket from claim to a merge-ready PR.
- **Reviewer** - reads the diff and approves or requests changes. May be a human or the `apptrick-review` skill in a session that did not author the change; the `apptrick-review-code` checklist applies either way.
- **Designer** - owns the flow and its states before the code exists, and the design contract the UI review reads back. May be a human, `apptrick-ux-shape` for the shaping, `apptrick-ux-review` for the pass over a PR's screens.
- **QA reviewer** - exercises user-facing changes before they merge, with `apptrick-prepare-test-env` to lease a simulator, emulator or phone and install the app once, and `apptrick-verify` to walk it through Maestro or Appium. A person judges the result and owns `qa-approved`, except the agent self-QA for non-release changes under D4 (Harness deviations). Always referenced by role, never by name or handle: assignments change.
- **Maintainer** - owns branch protection, the label taxonomy, the config, and this document; arbitrates when gates conflict.

## Ticket lifecycle

| Stage | What happens | Driven by | Done when |
|---|---|---|---|
| Discovery | The product context is established before any idea is weighed - problem and who has it, stakeholders, rules, flows, success criteria, scope - from material that exists, with every claim tagged by its evidence and every decision owned by a person. Then an idea, question, or itch is talked through: the problem is questioned, alternatives (including building nothing) are weighed, and the conversation ends in a routing decision. | `apptrick-discover` (product level) and `apptrick-brainstorm` (one idea), or a human | A product brief, or a routed conversation with a brief when the work continues |
| Intake | A ticket or task brief is filed in Linear and meets the Definition of Ready below. `apptrick-create-issue` files it with SDLC labels and the ready sections; `apptrick-refine-issues` reports what an existing ticket still lacks. | Anyone, `apptrick-create-issue`, `apptrick-refine-issues` | Ticket exists and is ready, or its gaps are named on the ticket |
| Triage | Confirm the issue is real, still unfixed on the base branch, and not already claimed or covered by an open PR. Read-only; stops the chain cleanly when there is nothing to do. | `apptrick-verify-bug` or a human | Confirmed actionable, or closed as no-action |
| Claim | The author claims the ticket so concurrent agents back off. See the claim protocol below. | `apptrick-apply-fix` / `apptrick-deliver`, or a human | Claim visible on the ticket |
| Design | For a user-facing change, the flow and its states are settled before the code exists: what the screen does when empty, loading, in error, and without permission, and what the change deliberately does not do. A ticket that touches no UI skips this stage. | `apptrick-ux-shape`, or a human designer | The flow and its states are decided, or the ticket is not user-facing |
| Implement | Locate the minimal change surface (`apptrick-diagnose`, read-only), then implement the change with tests that prove it, reusing existing coverage, and run the validation gate. Task briefs without a ticket go through `apptrick-deliver`, which plans, implements phase by phase in an isolated worktree, and runs the same gate. | `apptrick-diagnose` + `apptrick-apply-fix`, `apptrick-deliver`, or a human author | Change complete, validation gate green |
| PR | Commit, push, and open a PR against the base branch with normalized labels. On a hand-worked branch, `apptrick-check-commit-push` runs the gate, fixes obvious drift, and pushes when green. | `apptrick-open-pr`, `apptrick-deliver`, or `apptrick-check-commit-push` | Open, labeled PR |
| Review loop | The reviewer reads the diff against the `apptrick-review-code` checklist and approves or requests changes. Requested changes are addressed (`apptrick-continue-pr` resumes agent PRs from the tracking plan, and adopts a PR that has none by reconstructing the plan from the PR's own context) and the PR is re-reviewed until the independent review record approves the current head. A user-facing change also gets a design pass: `apptrick-ux-review` walks the changed screens and reports findings ranked by user impact. That pass is advisory - it informs the review, it does not hold the merge. | `apptrick-review` (single PR), `apptrick-review-prs` (sweep), `apptrick-ux-review` (design pass), or a human | Independent review record (`Independent review: APPROVE`, `Head: <sha>`) for the current head |
| QA | A PR carrying `needs-qa` waits for QA. The QA reviewer leases a target and installs the app once with `apptrick-prepare-test-env`, walks the change through Maestro (simulators and emulators) or Appium (physical devices) with `apptrick-verify` - which attaches screenshots and a pass/fail report and touches no labels by default - and records the outcome. A flow worth keeping becomes `apptrick-test` coverage. See the QA gate below. | QA reviewer, with `apptrick-prepare-test-env`, `apptrick-verify`, `apptrick-test` | `qa-approved` applied by a person or by `apptrick-verify --self-qa-signoff` under D4, or `qa-failed` routes it back |
| Merge | `apptrick-check-merge-readiness` reports, read-only, which PRs can merge now and which are close but blocked. `apptrick-merge` re-checks every gate with `.ai/scripts/merge_gate.py` (independent review record, required checks and both QA verdicts on the current head) and squash-merges that exact head; the agent merges without an approving review or a human gate (D3). | `apptrick-check-merge-readiness` + `apptrick-merge`, or a human | PR squash-merged into the base branch |
| Post-merge housekeeping | Close issues the merged PR fixes; comment on issues whose PRs were closed without merging; turn leftover asks or review comments into tracked follow-up issues. | `apptrick-close-fixed-issues`, `apptrick-followup-issue-from-pr` | Tracker reconciled, follow-ups filed |

## Task specifications

Every task changing repository deliverables must identify a covering spec in
`.ai/specs` before implementation, including bugs, tests, docs, configuration,
and harness changes. Use `apptrick-specify` by default to create or extend it;
accept existing, manual, or user-supplied specs that meet the same contract.
Read the relevant section before editing, and update coverage before scope changes.

Keep the spec proportional: task id when present, current and intended behavior,
scope, acceptance criteria, affected surfaces, and verification/implementation
steps. For one small agreed change, an existing task record placed in the specs
directory that states these items is the covering spec; do not rewrite it into a
second document. Several tasks may cite sections of one spec. A ticket, external link, or
execution plan alone is insufficient. Place supplied material locally, preserving
its content and provenance. Default to one PR containing spec and implementation;
use a separate design PR when prior design review is needed or requested.

Read-only work, tracker-only operations, ignored runtime evidence, and writing the
spec itself do not require another spec. For older work without one, record what
already exists and specify remaining work before further edits; do not claim the
spec preceded old implementation. Unresolved material questions retain their
approval gates; approved scope with no open decision needs no repeat approval.

Carry `Source doc:` in the plan and PR body and `Spec: <repo-relative path>` in
handoffs. Before completion, PR approval or merge, verify the local spec covers
the candidate diff and acceptance evidence. Missing or stale coverage is a
blocker; findings-only review reports it without writing a retrospective spec.
These are agent and review gates, not a server-side CI or branch-protection check.

## Definition of Ready

A ticket is ready for implementation when the answers below are on the ticket or in a spec it links. They come in two tiers, because a spec can supply the second but never the first.

**Ticket-level - only a human can supply these:**

- the problem or need, and who has it (a user or a role);
- the expected outcome, and how it will be checked;
- what is out of scope;
- open questions, each marked blocking or non-blocking - no blocking question left unanswered;
- any autonomous assumption confirmed by a human (the resolved-assumptions comment on a spec PR).

**Spec-level - a covering spec supplies these; use `apptrick-specify` by default when they are missing:**

- acceptance criteria;
- business rules;
- the happy path and the main unhappy paths;
- impact on data and permissions;
- dependencies;
- a link to the prototype or mockups when the change is user-facing.

For a bug, reproducibility is an additional gate: `apptrick-verify-bug` is that gate, the ticket-level items apply, and a proportionate task spec is still required before implementation. Enforcement: `apptrick-create-issue` files tickets with these sections; `apptrick-refine-issues` records `READY_STATUS` per issue and posts a not-ready comment naming what is missing; `apptrick-deliver`'s feature route stops on a ticket that fails the ticket-level tier instead of speccing around the gap, the way `apptrick-verify-bug` stops on a bug that is not real. Spec-level gaps are not a stop - the spec is authored. A maintainer may waive an intake item by saying so on the ticket; this does not replace the covering task-spec requirement.

## Product decisions as a protected contract

When `apptrick-discover` has written `.ai/specs/product-brief.md`, its **Non-goals**, **Business rules**, and **Decisions** tables are protected the way `BACKWARD_COMPATIBILITY.md` protects contract surfaces. Each entry carries a stable id (`N01`, `R03`, `D07`), an owner, a status (`active` or `superseded`), a review-by date, and a required path for changing it. The rules:

- A PR that builds something a non-goal excludes, or contradicts a business rule or a decision, without a superseding entry in the same PR is a **blocker** in review, quoting the entry and its id. The way out is never "delete the code": it is "change the decision explicitly" - a superseding row approved by the entry's owner, with the maintainer arbitrating a dispute, as in Roles.
- The decisions in play are surfaced where people work, not remembered: `apptrick-refine-issues` lists them in its implementation-notes comment, `apptrick-specify` carries a *Decisions in play* section, and every PR body carries *Decisions touched*. A newcomer or a new agent reads them at the issue, the spec, or the PR, not in a chat history.
- An autonomous assumption a human confirmed on a spec PR (the resolved-assumptions comment) is recorded as a decision on the next `apptrick-discover --refresh`, with the confirmer as owner, so the reason a thing is the way it is survives the people who decided it.
- Decisions age: an entry past its review-by date is flagged in review as due for a look, not enforced blindly. Which entries block more than they protect is a retro question.

## Label state machine

Pipeline labels are mutually exclusive: a PR carries at most one, and it names where the PR sits in the flow.

- A ready, non-draft PR carries `review`.
- The reviewer moves it: request changes → `changes-requested`; after fixes it returns to `review`; approval → `merge-queue`.
- `merge-queue` is routing, not proof of QA: a `needs-qa` PR legitimately sits there until QA signs off.
- Only a QA reviewer sets the `qa` pipeline label. They move a queued `needs-qa` PR from `merge-queue` to `qa` while testing, then back to `merge-queue` with `qa-approved` on pass, or to `qa-failed` on failure. Automated skills request QA with `needs-qa`; they never set `qa`.
- `blocked` and `do-not-merge` are set and cleared by humans and stop the flow wherever it is.

| Group | Labels | Exclusivity | Meaning |
|---|---|---|---|
| Pipeline | `review`, `changes-requested`, `qa`, `qa-failed`, `merge-queue`, `blocked`, `do-not-merge` | one at a time | Workflow state |
| Category | `bug`, `feature`, `refactor`, `security`, `dependencies`, `documentation` | additive | Kind of change |
| Meta | `needs-qa`, `skip-qa`, `qa-approved`, `qa-self-verified`, `in-progress`, `ci-monitoring` | additive | Process signals |
| Priority | `priority-low`, `priority-medium`, `priority-high`, `priority-extreme` | one at a time; unset = medium | Urgency of the work |
| Risk | `risk-low`, `risk-medium`, `risk-high` | one at a time; unset = medium | Blast radius of the change |

Category labels feed the changelog (`apptrick-update-changelog`) and any generated release notes, which group a PR by its category and print its title. Every PR therefore carries at least one category, and its title reads as a release-note line: a conventional title stating the user-visible effect, such as `fix(checkout): keep the total after a discount edit`. Pick the category from what the PR changes for users, starting from its conventional-commit type:

| Change | Category |
|---|---|
| fixes a vulnerability, an auth or data-scoping flaw, or a vulnerable dependency | `security` |
| `feat` - new capability or public API | `feature` |
| `fix` - incorrect behavior corrected | `bug` |
| `refactor`, `perf`, `test`, `ci`, `build`, `chore` with no user-visible behavior change | `refactor` |
| `deps` / `chore(deps)` - dependency bumps | `dependencies` |
| `docs` only | `documentation` |

One category is the norm. Add `security` next to `bug` or `dependencies` when the change closes a vulnerability; the changelog then files it under Security. PR-opening skills set the category. Review verifies it and, when it can write labels, corrects a missing or wrong one itself: a label fix is not a finding and does not change the verdict. Fork authors usually cannot set labels, so their PRs get the category from review.

Priority is how urgent the work is; risk is how dangerous the change is to ship. A one-line fix for an outage can be `priority-extreme` and `risk-low`; a large auth refactor that can wait can be `priority-low` and `risk-high`. A PR inherits both from its source issue unless the scope clearly changed. When an automated skill adds or changes a pipeline or meta label, it leaves a short comment explaining why.

When no priority label is set, infer one:

- `priority-extreme` - production outage, data loss, or an active security incident.
- `priority-high` - security hardening or a release-blocking regression.
- `priority-medium` - ordinary bug fixes and net-new features (also the default reading of unset).
- `priority-low` - cosmetic, docs-only, dependency bumps, follow-up cleanup.

When no risk label is set, infer one:

- `risk-high` - the diff changes a high-risk area in the table below.
- `risk-medium` - an ordinary single-area change that ships with tests (also the default reading of unset).
- `risk-low` - docs-only, test-only, typo, or isolated cosmetic changes.

A **high-risk diff** changes one of these areas. Classify the changed behavior, not file names, the title or an author's statement; read `BACKWARD_COMPATIBILITY.md` and the consumers of a changed contract when they exist.

| Area | `risk-high` when the diff | Not `risk-high` on that ground |
|---|---|---|
| Migrations | rewrites, deletes, backfills or moves existing rows, drops or renames columns or tables, or changes a migration runner | an additive migration (new table, nullable column or index) with up/down evidence |
| Permissions, authentication or tenant isolation | widens or removes access control: a new or loosened authorization or session check, a grant or feature given by default, a new cross-tenant or cross-organization read or write path, a removed or bypassed scope filter, or changed tenant-context propagation | a change that only narrows access: it fails closed, scopes a read further or rejects more input |
| Money | changes how amounts are computed or moved: prices, totals, currencies, rounding, charges, payments, refunds, billing, balances, payouts, or financial retry and idempotency | labels, display formatting, or hiding an amount from a role |
| Architecture | changes service or module boundaries, persistence or state ownership, execution or deployment topology, shared extension contracts, or cross-component communication and dependency direction | new code or a refactor inside one module's existing boundaries |
| Backward-incompatible change | removes, renames or reshapes a published API or event, CLI flag, config or serialized format, persisted data contract or supported integration, or changes documented successful behavior | an additive API, a new refusal for input that was already invalid, or a bound on pagination or size |

Tightening is not widening: a change that only narrows what is allowed is not high-risk on that ground, and its tests and QA cover the negative cases (wrong tenant or organization, missing permission, malformed input). When it is unclear whether a change widens or narrows access, treat it as high-risk.

When signals conflict, pick the higher label and say why in the label comment. A `risk-high` PR strengthens the case for `needs-qa` and deeper review even when it would otherwise look routine.

One label lives outside this taxonomy: `do-not-close`, applied by humans to issues that housekeeping skills must never auto-close. Skills only ever read it.

## The QA gate

This project sets `qaGate: false`: its QA is web QA in a browser (the jury prototype is the web build), not iOS/Android device QA, so the merge gate needs no device verdicts.

The one hard rule of this process: **a PR that needs QA merges only when its head-pinned QA verdict records pass for iOS and for Android on the current head, even when every other check is green.** The records decide (`qa_freshness.py check`, enforced by `.ai/scripts/merge_gate.py`); the labels `qa-approved` and `qa-failed` are their visible state, not a separate gate. `apptrick-check-merge-readiness` classifies such a PR as blocked; `apptrick-merge` refuses to merge it.

- Apply `needs-qa` to UI changes, new features, and other user-facing behavior that needs manual exercise.
- `skip-qa` is the explicit opt-out for docs-only, CI-only and test-only changes. Never combine it with `needs-qa`. The merge gate accepts it only when every path the PR changes since its merge base is a test path, CI or docs; a dependency change (`pubspec.*`) is an app input and needs QA.
- `qa-failed`, `do-not-merge`, `blocked` and `in-progress` are hard blocks regardless of every other signal, and the merge gate refuses them. An active `qa` pipeline label means a tester is on the PR right now - never merge under an active tester.
- The gate is satisfied when the iOS and the Android verdict records on the current head pass; the QA reviewer then applies `qa-approved`.
- **Self-QA exception**: when no QA reviewer has capacity in time, any engineer may sign off instead - but only by (1) checking the PR out and running it locally, (2) exercising the affected flow, and (3) attaching evidence to the PR: a screenshot of it working, or a written account of what was exercised and the observed result, recorded as the same per-platform verdict records. Then apply both `qa-approved` (the visible state) and `qa-self-verified` (so the exception is auditable). No evidence, no `qa-approved`.

## The claim protocol

Before mutating an issue or PR, an agent checks inspect/dry-run mode, then creates or resumes one stable `RUN_ID` and persists its local context in `<paths.runs>/.sessions/<RUN_ID>.json` (`.ai/runs` by default). A claim uses three signals: assignee, `in-progress`, and one stable cross-host ownership marker. Re-entry requires the same run id or an explicit handoff; matching account identity or PR authorship alone is insufficient. A legacy claim without a run id has unknown ownership and follows explicit handoff, stale recovery, or force takeover. Shared markers contain only the opaque run id, task/spec, repository identifier, status, and last completed stage; local paths, hosts, and users stay local. A PR carrying `in-progress` is also skipped by merge tooling.

For work spanning repositories, the local run context records `requiredRepositories` as one `{ repository, requiredBranch, pullRequest, revision, outcome, evidence }` entry per required repository. An issue closes only after every entry is accepted against its actual merge/verification requirement. A single open or merged PR never completes another required repository implicitly.

`in-progress` means **actively working**. Once an agent's work is finished and fully reported - labels applied, review submitted, comments posted - it swaps `in-progress` for `ci-monitoring` if it still intends to report the CI outcome. `ci-monitoring` is **not** a claim and blocks nobody: it says only that the CI-result follow-up comment is still owed, so another agent or a human may act on the PR freely. That distinction matters because CI runs long: an agent that reported its work and then died while watching a run leaves an honest, self-describing state instead of a lock nobody holds. The label comes off when the follow-up lands, or when the agent gives up waiting at `ci.maxWaitMinutes` and says so.

The claim is released when the work finishes - on success and on failure alike. A stale `in-progress` with no recent activity may be cleared by the maintainer.

### Reporting is decoupled from CI

Agents apply labels, submit reviews, and post comments **as soon as their work is done**, without waiting for CI to go green. A review submitted while checks are still running says so in its body: branch protection plus the QA-approval gate hold the actual merge, and the approval covers the code, not a green run. The CI outcome arrives afterwards as a follow-up comment, which also corrects the pipeline label if the result changes the verdict.

The wait for that outcome is bounded by `ci.maxWaitMinutes` (default 40). When it expires with checks still running, the agent stops waiting, inspects applicable local validation evidence and runs only missing or invalidated checks, posts that together with the still-pending check names and an explicit statement that no further follow-up is coming, drops `ci-monitoring`, and finishes.

A red signal does not short-circuit the review either. A failing required check or a conflicted head is collected as a **blocker finding** and reported together with the full code review, never instead of it: one review cycle gives the author the failing check, the conflict, and every code finding at once, rather than the cheapest red flag first and another cycle to discover the rest. Such a verdict is still `changes-requested` - completeness changed, the gate did not.

None of this touches the merge gates. Reporting early is safe; merging early is not - required checks still gate every merge, and the merge tooling refuses until they are genuinely green.


## The automation contract

Skills whose own workflow declares an autonomous chain run this process unattended: each accepts the artifact the previous one produced (a provider-native issue id, a spec path, or a numeric PR from the `PR: #<number> (link: <url>)` reference line every PR-producing skill emits), and each detects work already started - an open PR referencing the issue or plan - and continues on it rather than opening a duplicate. GitHub issue reports use `Issue: #<number>`; Jira/Linear use `Issue: <native-key>`. Legacy GitHub and environment-style markers remain readable. A completed autonomous run leaves a **ready** (non-draft), fully labeled PR - one pipeline label, category, QA meta, one priority, one risk - with a run-summary comment and, for user-facing changes, screenshots from the working app attached as PR evidence. Deployed QA additionally requires a fresh observed artifact identity, accepted required scenario evidence, independent evidence review, and the shipped offline validator before PASS. Draft PRs are reserved for explicitly incomplete states: spec-only design PRs, interrupted hand-offs, or autonomous defaults flagged for human confirmation. Automation never applies `qa-approved`.

## Validation gate

Harness copy: this is a frozen, edited project copy of the harness (core 8680c72, no overlays, store routes and private host context removed), so `check_project_copy.py` replaces the upstream pin check.

Every PR passes the full validation gate before review sign-off, in this order:

- `python3 -B scripts/check-portal-source.py`
- `docker compose --profile tools config --quiet`
- `docker compose run --rm manage python manage.py test mcod.core.tests.test_jury_seed mcod.aed_aggregate mcod.aed_wizard mcod.aed_reports --noinput --keepdb`
- `python3 -B .ai/scripts/check_project_copy.py`
- `python3 -B .ai/scripts/check_client_config.py`

Run the actual required full gate once for the stable candidate before delivery.
During corrections, run only missing or invalidated checks based on changed inputs,
environment and dependency paths; retain unaffected evidence. Review inspects the
command, exit status, relevant output and current-candidate applicability instead
of requiring another full execution. A new review round, checkpoint ordinal,
commit wrapper or evidence path alone does not invalidate checks or accepted
review scope. Failed, absent or unverifiable required results block sign-off.
Explicit fresh project/live/release gates and required green CI still apply.
The command list lives in `.ai/agentic.config.json`; keep this section aligned.
A new gate goes into `validation.commands`, this list and the gate list in
`AGENTS.md` in the same change; then refresh the pin of each edited pinned file
with `python3 -B .ai/scripts/check_client_config.py --update <path>`.

One proportional independent review covers specification, correctness, security
and skill contracts. Review corrections and unresolved findings; add a separate
specialist only for a concrete distinct risk or explicit project requirement.
Ordinary tests/reviews need no invented source/evidence byte quotas, RAM/CPU or
free-disk floors, growth reservations, peer ACKs or episode clocks. Keep concrete
source/artifact/account/device/port/output ownership, actual provider and user
limits, privacy, protocol limits, test/tool timeouts and owned cleanup.

## Amending this process

This document and `.ai/agentic.config.json` describe the same process: change them together, and re-run the `apptrick-set-up` skill when the toolchain or label taxonomy changes. The design contract the Design and Review stages read is set up the same way, once rather than per ticket: `apptrick-ux-setup` extracts it from the repository, and is re-run when the design system changes. Per-skill deviations - extra review rules, a different PR body template, an added gate step - belong in a repo-local skill of the same name at `.ai/skills/<skill-name>/SKILL.md`, which takes precedence over the installed skill (and can `@`-import or reference it to extend rather than replace it); local rules win, but a repo-local skill cannot grant what the installed skill's safety rules forbid.

## Harness deviations

These project rules extend the process above. Where they differ, they win. An
overlay named in `harness.overlays` of `.ai/agentic.config.json` adds its own
deviations section. The
`.ai/skills/apptrick-*` extensions carry the same rules for each skill. The
harness owns and pins the text between the `<!-- apptrick-harness:begin -->`
and `<!-- apptrick-harness:end -->` lines of each extension; app rules go
outside that block.

### Authorities

T3 executes work and displays devices. Linear owns issue state. GitHub owns
source, PRs and CI. Existing device launchers own device leases and QA
artifacts. The skill package is the generated `apptrick-` edition, pinned by
`.ai/apptrick-skills.lock.json`; never edit installed package copies to
customize behavior. Persistent memories are disabled.

### Standing autonomy

The approved scope covers routine Linear reads and writes,
specifications, implementation, test and CI repairs, review corrections, atomic
commits, task-branch pushes and PRs, merges under D3, laboratory builds,
installs and QA, and cleanup of owned temporary resources. Continue unfinished
work without asking whether to continue. Reuse valid unchanged evidence, builds
and caches. After three no-progress attempts on a technical failure, pivot or
record the blocker and perform another ready task.

Ask only for materially changed scope, uncovered publication, account, pricing
or ownership changes, irreversible operations, secret or trust changes, or
extra spend. No force-push, hook bypass or destructive history operation.
Freshly check the target and effect before every push and merge.

### Merge without a human gate (D3)

- `delivery.mode` in `.ai/agentic.config.json` decides who merges:
  `autonomous` (the default when the key is missing) lets agents merge;
  `human-gated` stops every run at a merge-ready PR and a human merges.
- Agents merge to the base branch (`baseBranch`) after an independent review,
  green required checks and the QA gate. There is no human approval gate.
- The independent review runs in a session that did not author the change. It
  posts a COMMENT review on the current head with `Independent review: APPROVE`,
  `Head: <sha>` and `Reviewer session: <id>`. The agent does not submit an
  approving review of its own PR; the record replaces it. Independence is the
  session: the merge gate refuses a record from the authoring session
  (`--author-session`), so the project's one GitHub account may post it and a
  second account is optional. Any new commit needs a new record.
- The authoring session stops at a ready PR in Review and never reviews its
  own PR; an independent session runs `apptrick-review` without `--autofix`
  (apptrick-deliver extension, "Independent review").
- `apptrick-merge` (also when `apptrick-advance-pr --allow-merge` dispatches
  it) merges only through
  `python3 -B .ai/scripts/merge_gate.py --pr <n> --author-session <id> --merge`.
  `--merge` without the authoring session refuses. The gate refuses unless
  the PR is open, not a draft, on the base branch, MERGEABLE and CLEAN, and
  not behind the base; it carries none of `qa-failed`, `do-not-merge`,
  `blocked`, `qa` and `in-progress`; the latest review record on the current
  head, a COMMENTED or APPROVED review from an OWNER, MEMBER or COLLABORATOR,
  approves it from another session (DISMISSED and PENDING reviews are
  ignored; a trusted CHANGES_REQUESTED review on the head refuses until a
  later approval record); every required check passed on that head (no required
  checks refuses); and, unless `qaGate` is false, `qa_freshness.py check`
  passes for iOS and Android on that head from trusted authors' comments. A
  PR that is `skip-qa` without `needs-qa` needs no verdict only when its diff
  since the merge base touches no app input and no unclassified path.
  A passing gate squash-merges with `--match-head-commit <head>`; the agent
  then reads back the merge commit as the new base head.
- A merge that would trigger production publication or deployment is not
  covered by standing authority.

### QA (D4)

- In solo work (no coordinator), non-release changes that are not
  `risk-high` may be closed as QA-verified on the agent's own Maestro or
  Appium evidence: `apptrick-verify
  --self-qa-signoff` applies `qa-approved` and `qa-self-verified` with a
  `QA head: <sha>` comment. This replaces "Automation never applies
  `qa-approved`" for that case only.
- `risk-high` changes, partial runs and release candidates get evidence only
  and wait for a QA reviewer.
- This project has no store release route; the jury prototype is the web
  build. Partial evidence never grants release acceptance.

### Coordinator lanes

When a coordinator runs several PRs in parallel, it and every lane follow the
coordinator's event-only coordination contract; device lanes also follow its
mobile QA lane rules. This project holds its lanes to these
rules:

- Every lane invokes the skill for its phase (Skill tool, or `$<skill>` on
  Codex) from the project checkout. Reading a skill
  file is not invoking it.
- Lanes send only `BLOCKED` / `DECISION`, `READY-QA` and `MERGED` / `DONE` to
  the coordinator and `QA-VERDICT` to the PR's owner, once (a QA lane's
  question about a PR also goes to its owner; only sign-in and host capacity
  go to the coordinator): the line `EVENT: <type> PR #<n> head <sha8>` plus at
  most 5 fact bullets that link records. Coordinator briefs are at most 10
  lines and point to files. No acknowledgements or progress messages; wait for
  builds and devices inside the turn. Long-lived owner and QA lanes are
  top-level threads, not delegated children; native subagents only run short
  checks and a loop engine's executor steps inside a lane.
- Owner lanes (one per PR) implement, run source gates, push, fix review
  findings, write their own issue in Linear with read-back (the tracker scribe
  only creates new issues), keep their rows in the project's QA queue file and
  start the design review after QA's visual review (default set: light and
  dark at the standard and the largest text size). They merge `baseBranch`
  into their PR only for a conflict GitHub shows, a dependency on a newly
  merged PR, or once right before the merge (see below), and stop after 2
  independent-review rounds with `BLOCKED`. They hold no devices: no
  apptrick-prepare-test-env, apptrick-verify, `maestro-cli` or Appium.
- Only the QA lane leases, boots and opens simulators, emulators and phones,
  takes the top unclaimed row for its platform from the QA queue file, records
  platform verdicts and sets QA labels. Self-QA (D4) does not apply under a
  coordinator.
- A new head on a PR under QA: the owner sets its queue rows to the new head
  and back to `queued`. QA evidence carries over only when every path in
  `git diff --no-renames --name-only <tested>..<new>` is on the project's
  closed list of non-app paths (the QA contract's non-app path classes: docs,
  tests, specs, run plans, skill and agent folders, root Markdown). The QA
  lane runs that diff itself (`rerun_scope.py` never replaces it) and records
  both SHAs and the path list in a carry record; the owner's word alone is not
  enough, and any other path needs new QA. A project under a coordinator sets
  `qa.carryMode: "strict"` on its base branch; the QA lane runs
  `rerun_scope.py` and `qa_freshness.py check` with `--strict`. A QA lane marks a row `done` only while it still has the head
  and lane it claimed; otherwise it leaves the row unchanged. The QA lane
  never pushes; it hands fixes to the owner as a patch.
- The owner merges with `apptrick-advance-pr --allow-merge` through the merge
  gate (D3) when every gate is green on the head and the coordinator's
  merge-order file allows it. When the merge-order file allows the PR and the
  gate's only refusals are `behind_base` or `BEHIND`, the owner merges
  `baseBranch` once; the new head needs green required checks and a new review
  record (not counted toward the 2 rounds), and the owner sets its QA rows to
  the new head; QA evidence carries over only under the carry rule above.
- `core.hooksPath` is relative (`.ai/hooks`). Never start a native subagent
  with worktree isolation in this repository: it rewrote the shared value
  and broke every lane's push. Use a delegate with its own checkout; if the
  value changed, restore exactly `.ai/hooks`.

### Small changes

One small agreed change (one behavior; no migration, new dependency, external
contract or open product question) takes the apptrick-deliver extension's
"Small change" path: one task record in `.ai/specs/` is the covering spec and
the run plan, the gate runs once on the stable candidate, `rerun_scope.py`
from the merge base decides `skip-qa` (no app input changed) or `needs-qa`
(without a scenario catalog: `skip-qa` only for a docs-, test- or CI-only
diff), and the PR goes through the same independent review and merge gate.

### Linear states (D5)

The harness moves Linear issue states explicitly at each stage and reads every
move back. Linear's GitHub automatic state moves are disabled to avoid double
transitions.

| Stage | Linear state |
|---|---|
| Filed, Definition of Ready not met | Backlog |
| Ready for implementation | Ready |
| Claimed by `apptrick-deliver` or an author | In Progress |
| Ready PR open, awaiting review; changes requested go back to In Progress | Review |
| Review approved, `needs-qa` PR waiting for QA evidence | QA |
| Merged and read back, QA gate satisfied or `skip-qa` | Done |

A blocked task keeps its state; record the blocked reason and the next
executable action on the existing issue. Keep detailed progress local and avoid
duplicate milestone comments. A merge alone never closes an issue whose QA is
open. Test-only tasks can close with a reviewed report. Open PRs and partial
test coverage are not completion.

### Linear provisioning (D6)

The harness creates Linear projects, milestones and labels without asking, as
routine Linear writes, and reads each one back. A missing taxonomy label is
created, not skipped: `apptrick-set-up` runs the adapter's `ensure-taxonomy`
for every name in `labels.*`. Deleting or archiving anything in Linear requires the
owner's approval. Search within the bound project before creating an issue;
always pass the project explicitly.

### Specs, PRs and commits

- Specs live in `.ai/specs/<YYYY-MM-DD>-<slug>.md` with `Issue: <KEY>-<n>` when a
  Linear issue exists. For one small agreed change, an existing task record in
  `.ai/specs/` that states problem, outcome, scope, acceptance and verification
  is the covering spec.
- Read the matching feature spec in `.ai/specs/`; update behavior, flow, test
  and evidence links together.
- PR bodies use `Refs <KEY>-<n>`; never a GitHub close keyword for a Linear
  issue. Commit subjects are Conventional Commits naming that commit's change,
  without the issue key or title (`TASK_COMMIT_PREFIX` is empty). A given
  issue title is used verbatim; otherwise titles are short imperatives without
  an `Implement:` or `Fix:` prefix.
- Issue and PR claims follow one contract, the apptrick-deliver extension's
  "Claim and release"; Linear claim writes use only the adapter commands.
- Pushes go to the bound repository through the `personalgit:` remote alias.

### Push guard

The pinned pre-push guard runs only where `core.hooksPath` is `.ai/hooks`:

- `sh .ai/scripts/bootstrap-hooks.sh` (default) sets it in the shared clone
  config, so every worktree of the clone runs the guard.
- `sh .ai/scripts/bootstrap-hooks.sh --worktree` sets it for one task worktree
  (`git config --worktree`, turning on `extensions.worktreeConfig`) when the
  session must not change the shared config.
- Without either, push with `git -c core.hooksPath=.ai/hooks push -u origin HEAD`.

Both modes read the effective value back. Never push from a worktree without
the guard, and never use `--no-verify`.

### Local portal setup and QA

README.md defines the one Docker Compose flow. Build the images, start the
support services and migrate the local database before validation.commands.
The seed integration tests use an isolated test database. They do not prove the
entire upstream portal or future AED features.

The jury target is the local web portal, not a mobile binary. Verify changed
browser/API/admin flows locally; no mobile preparation, simulator or physical
device gate applies. Keep qaGate false. Preserve empty upstream CMS behavior
rather than adding unrequested portal content. Frozen skill package copies
remain unchanged; their generic mobile examples do not change this scope.

## Project notes (Misja AED)

- Base branch `main`. Tracker: Linear workspace `slop-slayer`, team `APP`,
  project "HackNation 2026 - Misja AED" (IDs in `.ai/agentic.config.json`).
- `delivery.mode` is unset, so it is `autonomous`: the owner merges through
  `merge_gate.py` after green checks and an independent review (D3).
- The jury runs the official portal locally via compose.yaml; there is no mobile or public hosting target.
- The submission must state the scope of AI use (HackNation regulamin §2 ust. 8).
