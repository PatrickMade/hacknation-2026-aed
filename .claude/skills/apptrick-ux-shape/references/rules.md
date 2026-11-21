# Shared rules

Canonical rules shared by every skill in this collection. They always apply,
in addition to the skill-specific rules in the skill body. On conflict, the
stricter rule wins.

- **Verification reuse.** During iteration run affected checks; run the actual configured full gate once for the stable candidate before delivery. Inspect existing evidence: command, exit status, relevant output, source/config/dependency inputs (including untracked files) and environment. Retain unaffected results; rerun only invalidated checks, missing/unverifiable evidence or explicitly fresh project/live/release gates. Bind reused evidence to the current candidate with the applicability reason; an unchanged HEAD or pass summary alone is insufficient. A new review round, task ordinal, commit wrapper or evidence path alone never requires repeating unchanged tests, artifacts, source, reviews or history. Failed or absent required results still block acceptance.
- **Independent review.** One proportional independent review covers specification, correctness, security and skill contracts. Reuse accepted unchanged scope; review corrections and unresolved findings without replaying the whole review. Add a specialist only for a concrete distinct risk or explicit project requirement. The implementation owner fixes and accepts; never substitute self-review for required independence.
- **Execution resources.** Start authorized independent tests/reviews without invented source/evidence byte quotas, RAM/CPU or free-disk floors, growth reservations, all-peer resource ACKs or episode clocks. Let the operating system schedule work. Keep concrete source/artifact/account/device/port/output ownership, actual provider limits, explicit user limits, privacy, protocol limits, tool/test timeouts and owned cleanup. Serialize actual mutable-resource conflicts.
- **Scope and completion.** Complete the agreed scope with its required acceptance and project gates, then stop. Report material out-of-scope findings, hardening ideas and follow-ups with evidence instead of implementing them; file a follow-up only through this skill's documented tracker operation. After acceptance passes, broaden or repeat work only for changed inputs, a failed check or a concrete unresolved concern.
- **Interactive run - a user is in the loop.** This skill acts once, may ask
  the few questions that could change the direction, reports, and hands
  control back. Its explicit contract is interactive: it chains no further skills
  and starts no implementation unless asked.
- **Secrets hygiene.** Never paste secrets, tokens, `.env` content, or raw
  credentials into specs, handoffs, or reports.
- **Emoji glossary** in user-facing output: 🎯 goal · 📋 plan · 📝 spec · 🏷️ labels · 📸 evidence · 🔍 review · 🧪 tests · 💥 breaking · ✅ pass · ❌ fail · ⚠️ needs-human · ⛔ blocked · 🔁 resume · 🚀 merge/release. Emojis decorate; parsers key on text markers only.
- **Reporting style.** Lead with the outcome, blocker, or recommended action and its concrete reason. Explain what changes for whom in everyday language; use before/after behavior when useful. Replace vague claims with supported actors, behavior, constraints, or evidence. Follow the recipient's language and level of formality unless the project requires another language; keep established technical terms consistent. Avoid process narration, generic praise, repeated conclusions, and empty optional `None`/`N/A` sections. Use ASCII hyphen-minus for dashes in your own prose; protected content follows the Template contract.
- **One explanation, updates elsewhere.** The PR or issue body explains the current change; keep it current when this skill owns that body. Reviews add findings; run comments add changes since the last report, evidence, blockers, or a handoff. Link existing detail instead of repeating it. Preserve the claim, label, assumption, evidence, and release comments this workflow requires, updating their stable markers in place.
- **Issue milestones.** Keep useful English tracker updates for meaningful start, blocker, implementation/verification, PR, and deployment outcomes. Upsert each stable milestone marker instead of posting heartbeats or per-stage narration; keep detailed run state local. Preserve PR review findings, required label rationale, evidence links, and legacy marker parsing.
- **Task identity.** Preserve provider-native issue ids across handoffs. Jira/Linear task branches include the native key plus title slug, and every new task commit includes the key plus the project-required full task title. Resolve the convention from project instructions/config; never hard-code it.
- **Decision evidence.** Within this skill's scope, separate direction/scope questions from verified defects. State the affected behavior, consequence, and next action; cite code or the repository rule behind a finding. Distinguish observed facts, inferences, checks not run, and work still incomplete. Preserve uncertainty beside the claim it qualifies; do not turn an attempted action into a completed result. Qualify absence claims by where you searched. A planned consumer or missing document alone is not proof of a defect.
- **Useful detail only.** Include cross-system effects, durable contracts, defaults imposed on users, and rollback limits when they affect the decision. Use a small Mermaid flow or dependency diagram when relationships are clearer than prose; label current, changed, and planned parts accurately and add a one-sentence takeaway. Do not add an intake document or diagram for every change.
- **Length follows the decision.** Aim for 150-300 words for a substantive PR/issue body, 40-100 for a routine update, and 3-6 lines for a final handoff; simple work needs less. These are editing targets, not caps. Keep every actionable finding, required evidence, material uncertainty, and recovery instruction. Put long logs and inventories in linked artifacts or collapsible detail.
- **Template contract.** Use the skill's template for its purpose and required fields; omit optional sections that add no information. Preserve exact machine fields, verdicts, stable comment markers, and chaining lines even when shortening prose. Keep quoted text, code, commands, logs, identifiers, citations, and required template wording exact unless editing them is part of the task. The complete agent artifact stays complete when a skill defines a shorter human projection; disclose omitted counts and link the full findings. Use glossary emojis for meaningful headings or states, and backticks around skill names in human-facing prose. Workflow requirements, evidence, severity, uncertainty, approval and rollback instructions, and completion status take precedence over style or length. New `🤖` markers separate the skill name from the purpose with the ASCII hyphen-minus; when locating an existing marker, also accept the em dash (U+2014) that comments written before 2026-09-11 use.
- **Reader's language over method vocabulary.** The framework's vocabulary is
  for the author, never the reader: section names like evidence ledger, value
  gaps, complexity hotspots, behavioral signal, or guardrail must not appear
  in the delivered text. Render each as a plain statement about screens,
  behavior, and what to change.
- **The result obeys the rules it enforces.** Before delivering, check the
  text against the repository's own copy conventions (the manual section of
  `.uxproof/conventions.md` and any team rules the user has stated). A
  recommendation that flags a copy violation while committing it is invalid.

## apptrick-ux-shape specifics

- **Never invent evidence.** No fabricated research, user quotes, metrics, or
  constraints. An unverified belief is labeled as an assumption and given a
  validation path; a provisional persona is not evidence.
- **Recommend, do not enumerate.** One direction with the decisive trade-off
  beats an unranked menu. Rejected options stay internal unless they help the
  reader understand a consequential choice.
- **Depth follows risk.** A small, reversible decision gets a short answer.
  Do not make a low-risk task carry the full process.
- This skill writes no code and touches no tracker item. Its Handoff output is
  written to be consumed by the collection's implementing skills.

- **Renamed commands.** When comparing a stored skill identifier, recognize the installed compatibility alias and its frontmatter `metadata.deprecated-alias-for` target as the same command. Preserve original stable markers when updating existing records. Resolve only a shipped primary skill; unknown or missing targets block dependent work.
