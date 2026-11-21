---
name: apptrick-tdd
description: "Develop and fix behavior through public-interface red-green-refactor cycles, or characterize a refactor. Use when implementation needs executable regression proof; local work only, no commit or PR."
---

# Tdd

Build one observable behavior at a time. Tests should survive changes to internal
structure. This skill owns the method; the project's runner, fixture and mocking
conventions own the mechanics. Pair with `apptrick-test` for flows across
components and `apptrick-prepare-test-env` when a reusable runtime is needed.

## Arguments

- A behavior, bug or approved implementation slice, with its covering spec.
- Optional existing RED/GREEN evidence when resuming the same task.

## Workflow

**Local extension first:** Apply `references/agentic-setup.md`, including local and legacy extensions, before acting; authority and safety still apply.

0. Follow `references/agentic-setup.md`: read project instructions and the local
   extension, resolve the covering spec, and preserve the untrusted-content
   boundary. No tracker operations are used. Missing config uses `.ai/specs`;
   never run full setup merely to test a behavior.
1. Establish the requested public behavior and read the actual test conventions.
   Identify safety facts, including data scoping and authorization on newly
   reachable paths. Resolve material scope questions under the caller's rules;
   routine implementation choices need no extra approval.
2. Choose the smallest reliable verifier. New behavior and bug fixes use RED /
   GREEN / REFACTOR. Pure behavior-preserving refactors use characterization
   tests that pass before and after; do not fabricate RED. Docs, metadata and
   non-behavioral configuration use structural checks. State why executable
   coverage is unavailable and what alternative evidence cannot establish.
3. RED: write one test through a public interface and run it against unfixed
   production code. Read both output and exit status. Confirm the failure is
   the expected assertion, not a fixture, compilation, authentication or runner
   error. Save the command and relevant failure message in task evidence. When
   a fix already exists, use a disposable isolated copy to verify the test
   against unfixed code; never reset a user's worktree or claim tests-after was
   test-first. If the comparison is unavailable, report the missing RED proof.
   For assertion examples and setup failures, read `references/behavior-tests.md`.
4. GREEN: implement the smallest complete change that makes that test pass.
   Run the test and inspect the underlying result, not only a wrapper's exit.
   Do not write a bulk layer of speculative tests before the first behavior works.
5. REFACTOR only while green and only when the completed slice reveals a real
   simplification. Re-run the tests after each change, then repeat with the next
   behavior. Prefer public outputs over private-method assertions. Mock external
   boundaries where needed; preserve established project fixtures and justified
   internal test doubles rather than imposing a different test architecture.
   When choosing seams or mocks, read `references/testable-boundaries.md`.
6. Verify safety facts with relevant negative cases. For example, reviving a
   lookup fallback requires a test that another tenant's record cannot be selected,
   not just a search for callers. Wait for observable async conditions with a
   timeout rather than guessed sleeps. Add guards only for reachable failure modes.
   For asynchronous behavior, apply `references/async-verification.md`.
7. Run the relevant wider checks. Report behaviors covered, RED/GREEN or
   characterization evidence, baseline failures, checks not run and unresolved
   gaps. Leave publication and tracker operations to the caller.

## Rules

- Apply `references/rules.md`; project conventions and the caller's authorization
  remain binding. This skill grants no merge, push, deployment or new access.
- Reuse the existing test stack. TypeScript, Java, Python or other examples do
  not determine a project's framework, mocks or dependency policy.
- Keep assertions about behavior, not copies of implementation. A negative
  control counts only when a passing baseline becomes a failure at its intended
  assertion, not an earlier unrelated guard.

## Example

For a checkout failure, first assert that a declined payment leaves the order
unpaid. Observe that assertion fail against the bug, implement the fix, and show
it passes. A test that fails because its payment fixture cannot start is not RED
proof of the checkout defect.
