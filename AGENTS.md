# Agent rules for this repository

Misja AED - Dane na ratunek: a HackNation 2026 prototype for the Ministerstwo
Cyfryzacji challenge. It collects AED (defibrillator) data from scattered
sources into one open, machine-readable dataset that follows dane.gov.pl rules.
The jury runs the official dane.gov.pl portal locally with Docker Compose.
Backend: Python 3.8 / Django 2.2 / Falcon / Wagtail in backend/.
Frontend: Angular 18 / Node 20 in frontend/. PostgreSQL, Elasticsearch 6,
Redis, RabbitMQ, Fuseki and nginx are defined in compose.yaml.
README.md is in Polish and defines the complete local setup.

## Project rules

- Target branch: `main`. Work on a task branch in its own worktree and open a
  PR to `main`.
- Merge policy: the owner merges autonomously after green required checks and
  an independent review, only through the harness merge gate
  (`.ai/scripts/merge_gate.py`, `SDLC.md` "Merge without a human gate (D3)").
- Tracker: Linear workspace `slop-slayer`, team `APP`, project
  "HackNation 2026 - Misja AED"; issue keys match `APP-[0-9]+`. Use only
  `.ai/scripts/apptrick_linear.py` for Linear writes.
- AI use disclosure: the submission must state the scope of AI use
  (HackNation regulamin §2 ust. 8). Keep that statement current in the
  submission materials when AI-generated code, data or content is added.

## Task routing

| When the task involves… | Read first | Key rules |
| --- | --- | --- |
| Backend and account seed | `backend/mcod/settings/jury.py`, `backend/mcod/core/management/commands/seed_jury.py`, upstream module models/rules | Reuse existing organization scoping and roles; secrets only in ignored .env |
| Frontend and UI | `frontend/package.json`, `frontend/angular.json`, changed components | Preserve portal design/content/layout outside explicitly scoped AED work; verify web flows in a browser |
| Local runtime | `compose.yaml`, `.env.example`, `README.md` | Loopback-only ports; local proxy; telemetry off; never use production credentials |
| Source and licence | `UPSTREAM.md`, `LICENSE`, `NOTICE.upstream.txt`, `local/upstream-files.json` | Preserve notices/GPLv3 and document dated changes; update the source verifier only for intentional modifications |
| Tests | `backend/mcod/core/tests/test_jury_seed.py`, `backend/mcod/aed_aggregate/tests/`, upstream tests | Run targeted Django tests in Compose; actual upstream versions are pinned in its locks |
| Harness, tracker, hooks | `.ai/agentic.config.json`, `SDLC.md`, `.ai/trackers/linear-adapter.md`, `docs/AGENT-SKILL-CATALOG.md` | Never edit installed skill copies |

## Validation gate

Run in order (the list lives in `validation.commands` of
`.ai/agentic.config.json`; keep `SDLC.md` aligned):

- `python3 -B scripts/check-portal-source.py`
- `docker compose --profile tools config --quiet`
- `docker compose run --rm manage python manage.py test mcod.core.tests.test_jury_seed mcod.aed_aggregate mcod.aed_wizard mcod.aed_reports --noinput --keepdb`
- `python3 -B .ai/scripts/check_project_copy.py`
- `python3 -B .ai/scripts/check_client_config.py`

Prepare images, dependencies and database using README.md before the test gate.
The gate tests the local seed, not the complete upstream portal test suite.

Process: `SDLC.md`. Config: `.ai/agentic.config.json`. No `CODE_REVIEW.md` or
`BACKWARD_COMPATIBILITY.md` yet.

## Task specifications

Before implementing any repository change, identify and read its covering spec
in `.ai/specs`. Use `apptrick-specify` by default to create or extend it;
manual, user-supplied and existing specs are valid when they cover the task.
Keep scope proportional and follow the spec contract in `SDLC.md`. This includes
bugs, tests, docs, configuration, and harness changes. Writing the spec itself,
read-only work, tracker-only operations and ignored runtime evidence do not
require another spec. Recheck coverage before further edits when scope changes.
Include the spec in the task PR, link it with `Source doc:`, and verify the diff
and acceptance criteria against it before declaring completion.

## Harness and continuation

- Read `SDLC.md` for authorized autonomous delivery, Linear states, web QA
  routing and completion. Read `.ai/agentic.config.json` and the covering
  `.ai/specs/` task spec before repository changes; existing feature specs stay
  canonical. Tracker-only and read-only work needs no extra spec.
- Skills: the generated `apptrick-` edition in `.agents/skills` and
  `.claude/skills`, pinned by `.ai/apptrick-skills.lock.json`. Project rules
  live in `.ai/skills/apptrick-*/SKILL.md` extensions; add app rules outside
  the pinned `apptrick-harness` block. Never edit installed package copies;
  upgrades go through `apptrick-upgrade`.
- Deliver with `apptrick-deliver` (it has a small-change path); a bare
  continue resumes the same issue, run and PR. Agents merge to `baseBranch`
  only through `.ai/scripts/merge_gate.py` (review, required checks, and both
  device QA verdicts only while `qaGate` is true; it is false here) and only when `delivery.mode` is `autonomous`.
- Invoke skills; reading a skill file is not invoking it. Under a coordinator
  (SDLC.md "Coordinator lanes"; contract: the coordinator's
  event-only rules) lanes report only events, owners hold no devices
  and merge through the merge gate by the merge-order file, and only the QA
  lane runs devices and sets QA labels; set `qa.carryMode: "strict"`.
- The harness moves Linear states itself (Backlog, Ready, In Progress, Review,
  QA, Done) and creates projects, milestones and labels without asking.
  Deleting anything in Linear needs the owner's approval.
- QA is web browser evidence for the local portal. Mobile builds and device
  scenarios do not apply to this architecture. qaGate is false; record actual
  web/API verification and do not claim untested upstream/AED behavior.
- Push guard: `sh .ai/scripts/bootstrap-hooks.sh` sets `core.hooksPath` for
  the clone; a task worktree that must not change shared config uses
  `--worktree`, or pushes with `git -c core.hooksPath=.ai/hooks push`.
  The value is relative: never give a native subagent worktree isolation.
- A new gate goes into `validation.commands` in `.ai/agentic.config.json` and
  the gate lists in `AGENTS.md` and `SDLC.md` in the same change; then run
  `python3 -B .ai/scripts/check_client_config.py --update AGENTS.md` (and for
  each other edited pinned file) to refresh its pin.
- Persistent memories are disabled; preserve ordinary specs, code, reports and
  conversation history.

## Evidence and acceptance

- During iteration use affected checks, then run the actual required full gate once for the stable candidate. Review inspects existing command, exit status, relevant output and source/config/dependency/environment binding, including untracked inputs. Retain unaffected evidence after corrections; run only missing or invalidated checks. A review round, checkpoint ordinal, commit wrapper or evidence path alone never requires repeating unchanged tests, artifacts, source, reviews or history. Required fresh project/live/release gates and green CI remain.
- One proportional independent review covers spec, correctness, security and skill contracts. Retain accepted unchanged scope; review corrections and unresolved findings. Add a specialist only for a concrete distinct risk or explicit project requirement.
- Start authorized independent tests/reviews without invented source/evidence byte quotas, RAM/CPU or free-disk floors, growth reservations, peer resource ACKs or episode clocks. Let the operating system schedule work. Preserve concrete source/artifact/account/device/port/output ownership, actual provider and explicit user limits, privacy, protocol limits, tool/test timeouts and owned cleanup.
- Verify claims of success, absence or completion against output observed in this session. Read the operation's full relevant output and its exit status separately; a successful wrapper, pipe or background launch does not prove the underlying build passed. Report checks not run and baseline failures beside the result.
- Copy published identifiers (commit IDs, issue keys, paths, line numbers and tool names) from current tool results or user-provided material. Do not reconstruct them from memory. Qualify user-supplied identifiers until verified when a downstream action depends on them.
- For live third-party tool, API and permission claims, inspect the actual runtime/system or version-matched source. Official documentation establishes documented design, not proof that an account has a capability. Name the source and distinguish unverified availability.
- Give each acceptance criterion a deciding command, file check, diff or observable scenario. Record claims that cannot be evaluated as goals or open questions, not passed criteria. Reconcile every enumerated deliverable by identifier, with expected, missing and duplicate counts, before claiming completeness.
- For executable changes, name the one or two facts their safety depends on and prove each with an executable check; say where the proof stops. For non-executable changes, name the structural check and its limits. Listing callers alone is insufficient. A newly reachable path needs its guards established, including authorization and data scoping where applicable.
- When changing configuration, search for the old value as well as its key and update affected documentation and consumers. Explain retained historical references; do not blindly replace unrelated occurrences.

## Scope and simplicity

- Preserve the requested behavior and scope. Report bounded assumptions; resolve material uncertainty under the calling workflow's existing authority and stop rules. Removing a requirement means removing it, not moving it or adding a compensating requirement. Record resulting risks in the spec and PR; retain higher-priority safety and approval boundaries.
- Once acceptance criteria and required gates pass, stop. Report material out-of-scope findings without implementing them.
- Use `apptrick-tdd` for new or changed production behavior and bug fixes when a reliable executable test surface exists. Show the expected RED failure before the fix, then GREEN; read the failure message to exclude broken setup. A regression test must fail for the expected reason against the unfixed code. Record the command and relevant failure in task evidence. Never present tests-after as test-first evidence.
- For a behavior-preserving refactor, use characterization tests that pass before and after. Documentation, metadata and non-behavioral configuration changes use their smallest relevant verifier. If RED is infeasible, explain why and use contract or characterization coverage where possible.
- Handle reachable failure modes required by evidence, project conventions, security or acceptance criteria. Avoid speculative checks, fallbacks, retries and logging; never hide failure behind a successful-looking result.
- Use the least complex design that meets current requirements. Reuse existing code, dependencies and conventions. Every abstraction or new public API needs a concrete current use; do not build parallel implementations or future-proof hypothetical needs.
- Explain why a new dependency, migration, feature flag, cross-module change or architectural layer is needed. If implementation materially exceeds the implied components, record the reason and impact in the spec and PR and apply the existing scope/approval rules.

## Research discipline

- Start with the missing fact. Use repository evidence for routine work; research unresolved or version-sensitive library, framework, API, CLI or service questions before relying on an assumption. Prefer official documentation and primary sources; use an available search tool such as Exa for discovery, without requiring that vendor.
- Check research-tool availability in the active runtime. Distinguish authentication failure, unavailable capability and exhausted quota using observed errors. Record the gap and use an available primary-source route; block only work that depends on missing evidence. Do not invent an installed tool or silently change accounts.
- Distinguish demonstrated behavior, documented design, proposals/open issues and inference. Documentation or search output alone does not prove a live operation succeeded.
- Never send secrets, private logs, customer data, sensitive code or private environment details to external research tools.

## Unslop

Apply this final writing pass to replies, progress, PR/issue bodies, specs,
plans, reviews, handoffs and commit messages. Preserve conclusions, evidence,
uncertainty and authorization boundaries. Required workflow fields, severity,
blockers, approvals, rollback instructions and completion status take precedence
over style or length. Never turn an attempted action into a completed result;
distinguish observed facts, inference, checks not run and unfinished work.

1. Lead with the result, decision or blocker and its concrete reason.
2. Cut greetings, filler, generic praise, repetition and conclusions that repeat the answer.
3. Use plain words and name the actor, behavior, constraint or evidence. Remove unsupported claims rather than inventing specifics.
4. Split sentences that require rereading. Use only the headings, lists and emphasis the content needs.
5. Use only ASCII hyphen-minus for dashes in agent-authored prose. Preserve quotes, code, commands, logs, identifiers, citations, required templates and parsed output fields unless their editing is in scope.
6. Follow the recipient's language and level of formality unless the project requires another language. Keep technical terms consistent.
7. Remove vague attribution, promotional wording, metaphors or personified artifacts used instead of a mechanism, synonym cycling and forced parallel lists. These are signals to inspect, not blanket bans.
8. Give a judgment when evidence supports it; explain why. Do not invent feelings, experiences, confidence or sources. Read once as the recipient and remove wording that sounds performative, defensive or needlessly formal.

### Polish-language pass

When writing in Polish, compose in Polish from the first draft rather than
translating English sentence structure. Keep exact labels, identifiers and
familiar technical terms; explain unfamiliar terms once. Rewrite calques and
mixed constructions, distinguish permissions from subscription access, and read
once for natural Polish. Project-required languages and protected text remain
unchanged.

## Local portal boundaries

- Never commit .env, generated passwords or private runtime evidence. .env.example
  contains names and empty secret values. scripts/init-env.py creates local values.
- seed_jury manages only the named demo accounts and six jury-* institutions;
  it must validate all passwords before writes and keep existing portal guards.
- The local seed deliberately omits upstream basic_data.json and production CMS
  content. Do not create replacement pages merely to hide empty CMS responses.
- Imported backend/ and frontend/ retain upstream source and test fixtures;
  check_project_copy excludes these third-party trees from harness text-residue
  checks. scripts/check-portal-source.py verifies their release manifest instead.
- Existing mobile boilerplate in frozen harness skills does not require creating
  Flutter, iOS or Android surfaces. This project targets a local web portal only.
