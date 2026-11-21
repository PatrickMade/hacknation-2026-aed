# The hard gate - lint + completeness + readability

`apptrick-create-skill` must not hand back a skill until these pass. Run them before
reporting; on `--dry-run`, describe what would run and write nothing.

## Gate 1 - lint (both modes, mandatory)

Run the repo's content gate and require a clean exit:

```bash
bash scripts/lint.sh    # must print "Lint OK" and exit 0
```

It verifies frontmatter (`name` == directory, non-empty `description`), the
product-agnostic forbidden patterns, and the no-direct-tracker-CLI rule across
`skills/` (including `references/`). A failure names the offending file and
pattern - fix and re-run.

## Gate 2 - split-mode completeness (split mode only)

Prove the refactor lost nothing and preserved the risk surface. Set `BASE_REF` to
the ref holding the pre-split `SKILL.md` (e.g. the base branch, or `HEAD` before
you started editing), and `SKILL` to the skill name:

```bash
SKILL=<skill-name>
BASE_REF=<ref-with-pre-split-version>
dir="skills/$SKILL"

# 2a. Every fenced code-block line from the original body still exists in the
#     body+references union (commands/snippets/templates are the risk surface).
git show "$BASE_REF:$dir/SKILL.md" | awk '/^```/{f=!f;next} f{print}' | sort -u > /tmp/base_code.txt
cat "$dir/SKILL.md" "$dir"/references/*.md 2>/dev/null | awk '/^```/{f=!f;next} f{print}' | sort -u > /tmp/new_code.txt
missing_code=$(comm -23 /tmp/base_code.txt /tmp/new_code.txt | grep -vcE '^[[:space:]]*$')
echo "code lines lost: $missing_code   (must be 0)"

# 2b. Every non-blank line removed from the body reappears in references
#     (heading level normalized; substring match tolerates reworded pointers).
git show "$BASE_REF:$dir/SKILL.md" | grep -vE '^[[:space:]]*$' | sort -u > /tmp/base_lines.txt
grep -vE '^[[:space:]]*$' "$dir/SKILL.md" | sort -u > /tmp/new_lines.txt
cat "$dir"/references/*.md 2>/dev/null > /tmp/refs.txt
comm -23 /tmp/base_lines.txt /tmp/new_lines.txt | while IFS= read -r line; do
  norm=$(printf '%s' "$line" | sed -E 's/^#+[[:space:]]*//')
  grep -Fq -- "$norm" /tmp/refs.txt || echo "REVIEW (only intro/pointer prose is acceptable here): $line"
done

# 2c. Source presence only: this does not prove that the agent read the rule.
#     Inspect the required read path from the body separately.
grep -q "Untrusted content boundary" "$dir/SKILL.md" "$dir/references/agentic-setup.md" 2>/dev/null \
  && echo "untrusted boundary: text found; delivery unverified" || echo "FAIL: safety boundary lost"

# Source pointer and heading only; inspect that the body requires the preflight
# before dependent work. Matching text alone does not prove that it was read.
grep -q "references/agentic-setup.md" "$dir/SKILL.md" \
  && grep -q "^## Task specification gate" "$dir/references/agentic-setup.md" \
  && echo "task-spec gate: pointer and heading found; delivery unverified" || echo "FAIL: task-spec gate lost"

# 2d. Description unchanged (routing must not move).
diff <(git show "$BASE_REF:$dir/SKILL.md" | sed -n '/^---$/,/^---$/{/^description:/p}') \
     <(sed -n '/^---$/,/^---$/{/^description:/p}' "$dir/SKILL.md") \
  && echo "description: unchanged" || echo "FAIL: description changed"
```

Pass condition: `code lines lost: 0`, no `FAIL:` lines, and every 2b `REVIEW`
line is only a section-intro sentence you deliberately condensed into a pointer
(not a rule, template, or command). If any real content is missing, put it back.
Also inspect the body and preflight to confirm the safety and task-spec reads are
required before dependent actions. A matching heading, comment or unused pointer
is insufficient. These source checks do not prove runtime delivery.

## Gate 3 - readability (both modes)

Read the body alone. It passes only if you can still tell **what** the skill does,
**in what order**, and **where** to look for detail. If the body became a bare
list of links with no flow, pull some content back up (per
`references/philosophy.md`).

## Gate 4 - output usefulness (author mode)

For new output templates, check a realistic small change and a change with a
verified defect plus an unresolved direction question. The opening must explain
the behavior and next action; findings need evidence and consequences. Reject
empty-section rituals, repeated body/comment summaries, or brevity that drops a
gate, evidence limitation, or parsed field. Skip this check for a pure split,
which preserves the original wording.

## Gate 5 - evidence for delivery and behavior claims (both modes)

Use a representative case on the actual host/provider when claiming selection,
required-reference delivery or correct execution. Record the instruction version,
host/provider, input, observed reads and outcome; keep these claims separate:

- **Source:** files exist, links resolve and the entrypoint requires the right
  reads. Lint and text searches support only this layer.
- **Delivery:** the actual catalog exposes the relevant metadata, and the trace
  shows the exact entrypoint and required references read before dependent work.
  An explicit path read does not prove automatic selection or native hooks.
- **Behavior:** the observed result satisfies the task and its applicable gates.
  Include a relevant failure case, such as an unavailable required reference:
  dependent actions stop and the missing dependency is reported.

Use a fresh context when previously loaded instructions could contaminate the
case. For selection changes include a close negative request; for a pure split
compare the same representative task before and after. Report missing host
capabilities or unavailable traces as unverified, not as a pass. Source-only
verification can complete a source change without claiming runtime acceptance.
No test authorizes extra installation, background work or external writes.

## On failure

Fix and re-run failed source checks; do not report a failing skill as complete.
Report lint, completeness and readability separately from observed delivery and
behavior. When a required runtime check cannot run, name its missing evidence and
leave that acceptance claim open rather than repeating unchanged attempts.
